"""Engine-level validation and official FD001 test evaluation."""

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupShuffleSplit

from turbofan_rul import (
    add_training_rul,
    build_features,
    last_cycle_rows,
    read_test_targets,
    read_trajectory,
    regression_metrics,
)


def new_model() -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        learning_rate=0.06,
        max_iter=350,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=42,
    )


def main() -> None:
    raw = Path("data/raw")
    artifact_dir = Path("artifacts")
    artifact_dir.mkdir(exist_ok=True)
    training = add_training_rul(read_trajectory(raw / "train_FD001.txt"))
    features = build_features(training)
    targets = training["rul"].to_numpy()
    groups = training["engine_id"].to_numpy()

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_indices, validation_indices = next(splitter.split(features, targets, groups))
    model = new_model()
    model.fit(features.iloc[train_indices], targets[train_indices])
    validation_predictions = np.clip(model.predict(features.iloc[validation_indices]), 0, None)
    validation_metrics = regression_metrics(targets[validation_indices], validation_predictions)
    conformal_radius = float(
        np.quantile(np.abs(targets[validation_indices] - validation_predictions), 0.90)
    )

    test_frame = read_trajectory(raw / "test_FD001.txt")
    test_features = build_features(test_frame)
    final_test_rows = last_cycle_rows(test_frame)
    final_test_indices = final_test_rows.index
    actual_test_rul = read_test_targets(raw / "RUL_FD001.txt")

    final_model = new_model()
    final_model.fit(features, targets)
    predictions = np.clip(final_model.predict(test_features.loc[final_test_indices]), 0, None)
    baseline = np.repeat(np.median(actual_test_rul), len(actual_test_rul))
    lower = np.clip(predictions - conformal_radius, 0, None)
    upper = predictions + conformal_radius
    interval_coverage = float(np.mean((actual_test_rul >= lower) & (actual_test_rul <= upper)))

    report = {
        "dataset": "NASA C-MAPSS FD001",
        "target": "piecewise-linear RUL capped at 125 cycles",
        "validation_split": "20% complete engines held out with GroupShuffleSplit",
        "train_engines": int(training.engine_id.nunique()),
        "test_engines": int(test_frame.engine_id.nunique()),
        "validation_metrics": validation_metrics,
        "official_test_metrics": regression_metrics(actual_test_rul, predictions),
        "median_baseline_test_metrics": regression_metrics(actual_test_rul, baseline),
        "conformal_interval": {
            "nominal_coverage": 0.90,
            "radius_cycles": round(conformal_radius, 4),
            "official_test_coverage": round(interval_coverage, 4),
        },
    }
    (artifact_dir / "classical_metrics.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    plt.figure(figsize=(6.4, 5.2))
    plt.scatter(actual_test_rul, predictions, alpha=0.72, edgecolor="none")
    limit = max(float(actual_test_rul.max()), float(predictions.max()))
    plt.plot([0, limit], [0, limit], linestyle="--", color="black", linewidth=1)
    plt.xlabel("Actual RUL (cycles)")
    plt.ylabel("Predicted RUL (cycles)")
    plt.title("FD001 official test predictions")
    plt.tight_layout()
    plt.savefig(artifact_dir / "predicted_vs_actual.png", dpi=170)
    plt.close()
    joblib.dump(final_model, artifact_dir / "hist_gradient_boosting.joblib")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
