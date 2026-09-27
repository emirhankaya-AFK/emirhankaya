"""Run the saved classical baseline on one CWRU-style MATLAB vibration file."""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np

from bearing_fault import extract_feature_matrix, load_drive_end_signal, split_windows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mat_file", type=Path)
    parser.add_argument("--model", type=Path, default=Path("artifacts/extra_trees_load_3.joblib"))
    arguments = parser.parse_args()

    model = joblib.load(arguments.model)
    windows = split_windows(load_drive_end_signal(arguments.mat_file))
    probabilities = model.predict_proba(extract_feature_matrix(windows))
    mean_probabilities = probabilities.mean(axis=0)
    result = {
        "file": str(arguments.mat_file),
        "window_count": len(windows),
        "predicted_class": str(model.classes_[int(np.argmax(mean_probabilities))]),
        "mean_class_probability": {
            str(label): round(float(probability), 4)
            for label, probability in zip(model.classes_, mean_probabilities, strict=True)
        },
        "warning": (
            "Confidence is not a field-performance guarantee; this model was trained on CWRU."
        ),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
