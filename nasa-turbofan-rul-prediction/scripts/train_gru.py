"""GRU sequence baseline with engine-level train/validation separation."""

import json
import random
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from turbofan_rul import SENSORS, add_training_rul, read_test_targets, read_trajectory

INPUT_COLUMNS = ["setting_1", "setting_2", "setting_3", *SENSORS]
SEQUENCE_LENGTH = 30


class RULGru(nn.Module):
    def __init__(self, feature_count: int) -> None:
        super().__init__()
        self.gru = nn.GRU(feature_count, 48, batch_first=True)
        self.head = nn.Sequential(nn.Linear(48, 24), nn.ReLU(), nn.Dropout(0.15), nn.Linear(24, 1))

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        output, _ = self.gru(values)
        return self.head(output[:, -1]).squeeze(1)


def sequences(frame, scaler, final_only=False):
    values, targets, engines = [], [], []
    for engine_id, trajectory in frame.groupby("engine_id"):
        scaled = scaler.transform(trajectory[INPUT_COLUMNS])
        starts = [len(trajectory) - SEQUENCE_LENGTH] if final_only else range(
            0, len(trajectory) - SEQUENCE_LENGTH + 1
        )
        for start in starts:
            values.append(scaled[start : start + SEQUENCE_LENGTH])
            targets.append(float(trajectory.iloc[start + SEQUENCE_LENGTH - 1].get("rul", 0)))
            engines.append(int(engine_id))
    return (
        np.asarray(values, dtype=np.float32),
        np.asarray(targets, dtype=np.float32),
        np.asarray(engines),
    )


def predict(model, loader):
    model.eval()
    actual, predicted = [], []
    with torch.no_grad():
        for values, targets in loader:
            actual.extend(targets.numpy())
            predicted.extend(model(values).numpy())
    return np.asarray(actual), np.clip(np.asarray(predicted), 0, None)


def main() -> None:
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.set_num_threads(2)
    raw = Path("data/raw")
    training = add_training_rul(read_trajectory(raw / "train_FD001.txt"))
    engine_ids = training.engine_id.unique()
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_engine_indices, validation_engine_indices = next(
        splitter.split(engine_ids, groups=engine_ids)
    )
    train_engines = set(engine_ids[train_engine_indices])
    validation_engines = set(engine_ids[validation_engine_indices])
    scaler = StandardScaler().fit(training[training.engine_id.isin(train_engines)][INPUT_COLUMNS])
    all_sequences, all_targets, groups = sequences(training, scaler)
    train_mask = np.isin(groups, list(train_engines))
    validation_mask = np.isin(groups, list(validation_engines))
    train_loader = DataLoader(
        TensorDataset(
            torch.from_numpy(all_sequences[train_mask]),
            torch.from_numpy(all_targets[train_mask]),
        ),
        batch_size=128,
        shuffle=True,
    )
    validation_loader = DataLoader(
        TensorDataset(
            torch.from_numpy(all_sequences[validation_mask]),
            torch.from_numpy(all_targets[validation_mask]),
        ),
        batch_size=256,
    )
    model = RULGru(len(INPUT_COLUMNS))
    optimizer = torch.optim.AdamW(model.parameters(), lr=8e-4, weight_decay=1e-4)
    loss_function = nn.HuberLoss(delta=15)
    best_state, best_mae, patience = None, float("inf"), 0
    for _epoch in range(25):
        model.train()
        for values, targets in train_loader:
            optimizer.zero_grad()
            loss = loss_function(model(values), targets)
            loss.backward()
            optimizer.step()
        actual, predicted = predict(model, validation_loader)
        score = mean_absolute_error(actual, predicted)
        if score < best_mae - 0.05:
            best_mae = score
            best_state = {key: value.detach().clone() for key, value in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
        if patience >= 5:
            break

    model.load_state_dict(best_state)
    test_frame = read_trajectory(raw / "test_FD001.txt")
    test_sequences, _, _ = sequences(test_frame, scaler, final_only=True)
    test_targets = read_test_targets(raw / "RUL_FD001.txt").astype(np.float32)
    test_loader = DataLoader(
        TensorDataset(torch.from_numpy(test_sequences), torch.from_numpy(test_targets)),
        batch_size=256,
    )
    actual, predicted = predict(model, test_loader)
    report = {
        "split": "complete engines separated; final official test trajectory per engine",
        "sequence_length": SEQUENCE_LENGTH,
        "epochs_completed": _epoch + 1,
        "validation_mae": round(float(best_mae), 4),
        "official_test_mae": round(float(mean_absolute_error(actual, predicted)), 4),
        "official_test_rmse": round(float(np.sqrt(mean_squared_error(actual, predicted))), 4),
    }
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/gru_metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    torch.save(best_state, "artifacts/rul_gru.pt")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
