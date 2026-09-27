"""Fixed 1D-CNN baseline: train loads 0-1, validate load 2, test load 3."""

import json
import random
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, classification_report, f1_score
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from bearing_fault import LABELS, load_dataset


class BearingCNN(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv1d(1, 16, 15, stride=2, padding=7),
            nn.BatchNorm1d(16),
            nn.ReLU(),
            nn.MaxPool1d(4),
            nn.Conv1d(16, 32, 9, stride=2, padding=4),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(16),
        )
        self.classifier = nn.Sequential(nn.Flatten(), nn.Dropout(0.25), nn.Linear(32 * 16, 4))

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(values))


def prepare(windows: np.ndarray, labels: np.ndarray, mask: np.ndarray) -> TensorDataset:
    selected = windows[mask].astype(np.float32)
    selected = (selected - selected.mean(axis=1, keepdims=True)) / (
        selected.std(axis=1, keepdims=True) + 1e-6
    )
    encoded = np.asarray([LABELS.index(label) for label in labels[mask]])
    return TensorDataset(torch.from_numpy(selected[:, None, :]), torch.from_numpy(encoded))


def evaluate(model: nn.Module, loader: DataLoader) -> tuple[np.ndarray, np.ndarray]:
    model.eval()
    actual, predicted = [], []
    with torch.no_grad():
        for values, targets in loader:
            actual.extend(targets.numpy())
            predicted.extend(model(values).argmax(dim=1).numpy())
    return np.asarray(actual), np.asarray(predicted)


def main() -> None:
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.set_num_threads(2)
    windows, labels, loads, _ = load_dataset(Path("data/raw"))
    train = DataLoader(prepare(windows, labels, loads <= 1), batch_size=64, shuffle=True)
    validation = DataLoader(prepare(windows, labels, loads == 2), batch_size=128)
    test = DataLoader(prepare(windows, labels, loads == 3), batch_size=128)
    model = BearingCNN()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    loss_function = nn.CrossEntropyLoss()
    best_state, best_score, patience = None, -1.0, 0

    for _epoch in range(30):
        model.train()
        for values, targets in train:
            optimizer.zero_grad()
            loss = loss_function(model(values), targets)
            loss.backward()
            optimizer.step()
        actual, predicted = evaluate(model, validation)
        score = f1_score(actual, predicted, average="macro")
        if score > best_score + 1e-4:
            best_score = score
            best_state = {key: value.detach().clone() for key, value in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
        if patience >= 6:
            break

    assert best_state is not None
    model.load_state_dict(best_state)
    actual, predicted = evaluate(model, test)
    report = {
        "split": "train loads 0-1 HP; validation 2 HP; untouched test 3 HP",
        "epochs_completed": _epoch + 1,
        "validation_macro_f1": round(float(best_score), 4),
        "test_accuracy": round(float(accuracy_score(actual, predicted)), 4),
        "test_macro_f1": round(float(f1_score(actual, predicted, average="macro")), 4),
        "classification_report": classification_report(
            actual, predicted, target_names=LABELS, output_dict=True, zero_division=0
        ),
    }
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/cnn_metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    torch.save(best_state, "artifacts/bearing_cnn.pt")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
