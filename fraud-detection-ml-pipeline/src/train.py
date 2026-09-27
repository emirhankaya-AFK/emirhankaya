"""Train, compare and persist cost-sensitive fraud models."""

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.data import FEATURES, save_dataset

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
DATA_PATH = ROOT / "data" / "transactions.csv"
FALSE_POSITIVE_COST = 5
FALSE_NEGATIVE_COST = 250


def build_models() -> dict[str, Pipeline]:
    numeric = ColumnTransformer(
        [("numeric", Pipeline([("imputer", SimpleImputer()), ("scale", StandardScaler())]), FEATURES)]
    )
    return {
        "logistic_regression": Pipeline(
            [("preprocess", numeric), ("model", LogisticRegression(class_weight="balanced", max_iter=1_000))]
        ),
        "gradient_boosting": Pipeline(
            [
                ("preprocess", ColumnTransformer([("numeric", SimpleImputer(), FEATURES)])),
                ("model", HistGradientBoostingClassifier(max_iter=180, learning_rate=0.07, random_state=42)),
            ]
        ),
    }


def business_cost(y_true: np.ndarray, y_pred: np.ndarray) -> int:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    del tn, tp
    return int(fp * FALSE_POSITIVE_COST + fn * FALSE_NEGATIVE_COST)


def select_threshold(y_true: np.ndarray, probabilities: np.ndarray) -> tuple[float, int]:
    candidates = np.linspace(0.05, 0.95, 181)
    costs = [business_cost(y_true, probabilities >= threshold) for threshold in candidates]
    best = int(np.argmin(costs))
    return float(candidates[best]), int(costs[best])


def run_training() -> dict:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    frame = save_dataset(DATA_PATH)
    train, holdout = train_test_split(
        frame, test_size=0.30, random_state=42, stratify=frame["is_fraud"]
    )
    validation, test = train_test_split(
        holdout, test_size=0.50, random_state=42, stratify=holdout["is_fraud"]
    )
    x_train, y_train = train[FEATURES], train["is_fraud"].to_numpy()
    reports: dict[str, dict] = {}
    trained: dict[str, Pipeline] = {}

    for name, model in build_models().items():
        weights = np.where(y_train == 1, (y_train == 0).sum() / max((y_train == 1).sum(), 1), 1.0)
        if name == "gradient_boosting":
            model.fit(x_train, y_train, model__sample_weight=weights)
        else:
            model.fit(x_train, y_train)
        validation_probability = model.predict_proba(validation[FEATURES])[:, 1]
        threshold, _ = select_threshold(validation["is_fraud"].to_numpy(), validation_probability)
        probability = model.predict_proba(test[FEATURES])[:, 1]
        prediction = probability >= threshold
        tn, fp, fn, tp = confusion_matrix(test["is_fraud"], prediction, labels=[0, 1]).ravel()
        reports[name] = {
            "roc_auc": round(float(roc_auc_score(test["is_fraud"], probability)), 4),
            "pr_auc": round(float(average_precision_score(test["is_fraud"], probability)), 4),
            "precision": round(float(precision_score(test["is_fraud"], prediction, zero_division=0)), 4),
            "recall": round(float(recall_score(test["is_fraud"], prediction, zero_division=0)), 4),
            "f1": round(float(f1_score(test["is_fraud"], prediction, zero_division=0)), 4),
            "threshold": round(threshold, 3),
            "business_cost": business_cost(test["is_fraud"].to_numpy(), prediction),
            "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        }
        trained[name] = model

    winner = min(reports, key=lambda key: reports[key]["business_cost"])
    report = {
        "dataset": {
            "rows": len(frame),
            "fraud_rate": round(float(frame["is_fraud"].mean()), 4),
            "source": "synthetic",
        },
        "cost_assumptions": {"false_positive": FALSE_POSITIVE_COST, "false_negative": FALSE_NEGATIVE_COST},
        "models": reports,
        "selected_model": winner,
    }
    joblib.dump({"model": trained[winner], "threshold": reports[winner]["threshold"]}, ARTIFACTS / "model.joblib")
    (ARTIFACTS / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    create_charts(report)
    return report


def create_charts(report: dict) -> None:
    names = list(report["models"])
    values = [report["models"][name]["roc_auc"] for name in names]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar([name.replace("_", " ").title() for name in names], values, color=["#2563eb", "#14b8a6"])
    ax.bar_label(bars, fmt="%.3f")
    ax.set_ylim(0.5, 1)
    ax.set_ylabel("ROC-AUC")
    ax.set_title("Holdout Model Comparison")
    fig.tight_layout()
    fig.savefig(ARTIFACTS / "model_comparison.png", dpi=160)
    plt.close(fig)

    selected = report["models"][report["selected_model"]]["confusion_matrix"]
    matrix = np.array([[selected["tn"], selected["fp"]], [selected["fn"], selected["tp"]]])
    display = ConfusionMatrixDisplay(matrix, display_labels=["Legitimate", "Fraud"])
    display.plot(cmap="Blues", colorbar=False)
    display.ax_.set_title("Selected Model — Holdout Set")
    display.figure_.tight_layout()
    display.figure_.savefig(ARTIFACTS / "confusion_matrix.png", dpi=160)
    plt.close(display.figure_)


if __name__ == "__main__":
    print(json.dumps(run_training(), indent=2))

