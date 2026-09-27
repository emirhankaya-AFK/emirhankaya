from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from air_sensor.data import chronological_split, load_dataset
from air_sensor.modeling import build_model, conformal_radius, population_stability_index


def regression_metrics(actual: pd.Series, prediction: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(actual, prediction)),
        "rmse": float(mean_squared_error(actual, prediction) ** 0.5),
        "r2": float(r2_score(actual, prediction)),
    }


def main() -> None:
    artifact_dir = Path("artifacts")
    artifact_dir.mkdir(exist_ok=True)
    features, target, timestamps = load_dataset(Path("data"))
    splits = chronological_split(features, target)
    x_train, y_train = splits["train"]
    x_calibration, y_calibration = splits["calibration"]
    x_test, y_test = splits["test"]

    model = build_model()
    model.fit(x_train, y_train)
    calibration_prediction = model.predict(x_calibration)
    radius = conformal_radius(y_calibration.to_numpy(), calibration_prediction, coverage=0.90)
    test_prediction = model.predict(x_test)
    lower, upper = np.maximum(0.0, test_prediction - radius), test_prediction + radius
    baseline_prediction = np.full(len(y_test), float(y_train.median()))
    drift = {
        column: population_stability_index(x_train[column], x_test[column])
        for column in x_train.columns
    }
    report = {
        "dataset": {"usable_rows": len(features), "features": features.shape[1]},
        "period": {"start": str(timestamps.min()), "end": str(timestamps.max())},
        "split_rows": {name: len(values[1]) for name, values in splits.items()},
        "test": regression_metrics(y_test, test_prediction),
        "median_baseline": regression_metrics(y_test, baseline_prediction),
        "conformal_interval": {
            "nominal_coverage": 0.90,
            "radius": radius,
            "test_coverage": float(np.mean((y_test >= lower) & (y_test <= upper))),
        },
        "drift_psi": dict(sorted(drift.items(), key=lambda item: item[1], reverse=True)),
    }
    (artifact_dir / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    pd.DataFrame({"timestamp": timestamps.iloc[-len(y_test):], "actual_no2": y_test, "predicted_no2": test_prediction, "lower_90": lower, "upper_90": upper}).to_csv(artifact_dir / "test_predictions.csv", index=False)
    joblib.dump(model, artifact_dir / "model.joblib")

    count = min(500, len(y_test))
    figure, axis = plt.subplots(figsize=(11, 4.5))
    time = timestamps.iloc[-len(y_test):].iloc[:count]
    axis.plot(time, y_test.iloc[:count], label="Reference NO2", linewidth=1.2)
    axis.plot(time, test_prediction[:count], label="Calibrated sensor estimate", linewidth=1.2)
    axis.fill_between(time, lower[:count], upper[:count], alpha=0.18, label="90% conformal interval")
    axis.set_ylabel("NO2 concentration (µg/m³)")
    axis.set_title("Chronological holdout: first 500 hours")
    axis.legend(ncol=3, fontsize=8)
    figure.tight_layout()
    figure.savefig(artifact_dir / "holdout_calibration.png", dpi=160)
    plt.close(figure)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
