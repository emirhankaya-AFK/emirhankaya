"""Reproducible synthetic classification benchmark."""

from __future__ import annotations

import json
import time

from power_quality import DisturbanceType, PowerQualityAnalyzer, SignalSimulator


def main() -> None:
    classes = list(DisturbanceType)
    analyzer = PowerQualityAnalyzer()
    confusion = {actual.value: {predicted.value: 0 for predicted in classes} for actual in classes}
    durations = []

    for class_index, actual in enumerate(classes):
        for sample_index in range(50):
            window = SignalSimulator(seed=class_index * 1000 + sample_index).generate(actual)
            started = time.perf_counter()
            result = analyzer.analyze(window)
            durations.append((time.perf_counter() - started) * 1000)
            confusion[actual.value][result.primary_class.value] += 1

    correct = sum(confusion[item.value][item.value] for item in classes)
    total = len(classes) * 50
    report = {
        "dataset": "seeded synthetic waveforms",
        "samples": total,
        "accuracy": round(correct / total, 4),
        "average_latency_ms": round(sum(durations) / len(durations), 3),
        "confusion_matrix": confusion,
        "scope": "educational prototype; no field-data or standards-compliance claim",
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
