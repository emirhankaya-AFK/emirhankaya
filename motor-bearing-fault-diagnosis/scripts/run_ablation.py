"""Measure how much each engineered feature family contributes on the 3 HP holdout."""

import json
from pathlib import Path

from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import accuracy_score, f1_score

from bearing_fault import extract_feature_matrix, feature_names, load_dataset


def main() -> None:
    windows, labels, loads, _ = load_dataset(Path("data/raw"))
    features = extract_feature_matrix(windows)
    train_mask, test_mask = loads != 3, loads == 3
    groups = {
        "time_only": list(range(0, 8)),
        "frequency_only": list(range(8, 17)),
        "wavelet_only": list(range(17, 22)),
        "all_features": list(range(22)),
    }
    results = {}
    for name, columns in groups.items():
        model = ExtraTreesClassifier(
            n_estimators=400,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
        model.fit(features[train_mask][:, columns], labels[train_mask])
        predictions = model.predict(features[test_mask][:, columns])
        results[name] = {
            "feature_count": len(columns),
            "features": [feature_names()[index] for index in columns],
            "accuracy": round(float(accuracy_score(labels[test_mask], predictions)), 4),
            "macro_f1": round(float(f1_score(labels[test_mask], predictions, average="macro")), 4),
        }
    Path("artifacts/ablation_metrics.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
