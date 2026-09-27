from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import PrecisionRecallDisplay, RocCurveDisplay
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from semiconductor_yield.data import chronological_split, load_secom
from semiconductor_yield.metrics import bootstrap_interval, classification_metrics
from semiconductor_yield.modeling import (
    build_logistic_model,
    choose_recall_threshold,
    positive_probability,
    select_train_columns,
)


def main() -> None:
    data_dir = Path("data")
    artifact_dir = Path("artifacts")
    artifact_dir.mkdir(exist_ok=True)
    features, target, timestamps = load_secom(data_dir)
    splits = chronological_split(features, target, timestamps)
    x_train, y_train = splits["train"]
    x_validation, y_validation = splits["validation"]
    x_test, y_test = splits["test"]

    x_development = pd.concat([x_train, x_validation], ignore_index=True)
    y_development = pd.concat([y_train, y_validation], ignore_index=True)
    columns = select_train_columns(x_development)
    model = build_logistic_model()
    cross_validation = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    development_probability = cross_val_predict(
        model,
        x_development[columns],
        y_development,
        cv=cross_validation,
        method="predict_proba",
        n_jobs=-1,
    )[:, 1]
    threshold = choose_recall_threshold(
        y_development, development_probability, minimum_recall=0.50
    )
    development_metrics = classification_metrics(
        y_development.to_numpy(), development_probability, threshold
    )
    model.fit(x_development[columns], y_development)
    test_probability = positive_probability(model, x_test[columns])

    test_metrics = classification_metrics(y_test.to_numpy(), test_probability, threshold)
    test_metrics["pr_auc_ci_95"] = list(
        bootstrap_interval(y_test.to_numpy(), test_probability, "pr_auc")
    )
    test_metrics["roc_auc_ci_95"] = list(
        bootstrap_interval(y_test.to_numpy(), test_probability, "roc_auc")
    )
    baseline_probability = np.full(len(y_test), float(y_development.mean()))
    baseline = classification_metrics(y_test.to_numpy(), baseline_probability, 0.5)
    report = {
        "dataset": {
            "samples": len(features),
            "raw_features": features.shape[1],
            "selected_features": len(columns),
            "failure_rate": float(target.mean()),
        },
        "split": {
            name: {"samples": len(y), "failures": int(y.sum())}
            for name, (_, y) in splits.items()
        },
        "threshold_policy": {
            "source": "five_fold_out_of_fold_development_predictions",
            "minimum_development_recall": 0.50,
            "false_negative_cost": 10,
            "false_positive_cost": 1,
        },
        "development_oof": development_metrics,
        "test": test_metrics,
        "constant_prevalence_baseline": baseline,
    }
    (artifact_dir / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    pd.DataFrame(
        {"actual": y_test.to_numpy(), "failure_probability": test_probability}
    ).to_csv(artifact_dir / "test_predictions.csv", index=False)
    joblib.dump({"model": model, "columns": columns, "threshold": threshold}, artifact_dir / "model.joblib")

    figure, axes = plt.subplots(1, 2, figsize=(10, 4))
    PrecisionRecallDisplay.from_predictions(y_test, test_probability, ax=axes[0])
    axes[0].set_title("Chronological holdout: precision-recall")
    RocCurveDisplay.from_predictions(y_test, test_probability, ax=axes[1])
    axes[1].set_title("Chronological holdout: ROC")
    figure.tight_layout()
    figure.savefig(artifact_dir / "holdout_curves.png", dpi=160)
    plt.close(figure)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
