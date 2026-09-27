"""
Extraction accuracy evaluation against ground_truth.json.

Produces a field-level Precision / Recall / F1 report per document type.

Usage:
    python tests/evaluation/run_evaluation.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.pipeline.coordinator import DocumentPipeline  # noqa: E402

GROUND_TRUTH = Path(__file__).parent / "ground_truth.json"


def run_evaluation():
    ground_truth = json.loads(GROUND_TRUTH.read_text(encoding="utf-8"))
    pipeline = DocumentPipeline()

    results_per_type: dict[str, dict] = {
        "invoice": {"tp": 0, "fp": 0, "fn": 0, "docs": 0},
        "contract": {"tp": 0, "fp": 0, "fn": 0, "docs": 0},
        "technical": {"tp": 0, "fp": 0, "fn": 0, "docs": 0},
    }

    classification_correct = 0
    classification_total = 0
    validation_correct = 0
    validation_total = 0

    print("\n" + "=" * 70)
    print("  DOCUMENT INTELLIGENCE PIPELINE — EVALUATION REPORT")
    print("=" * 70)

    for doc_spec in ground_truth["documents"]:
        file_path = ROOT / doc_spec["file"]
        expected_type = doc_spec["document_type"]
        required_fields = doc_spec.get("required_fields", {})
        must_be_valid = doc_spec.get("must_be_valid", None)

        print(f"\n📄 {file_path.name}")
        print(f"   Expected type: {expected_type}")

        if not file_path.exists():
            print(f"   ⚠️  File not found: {file_path}")
            continue

        result = pipeline.run(file_path)
        actual_type = result.classification.document_type.value
        confidence = result.classification.confidence
        fields = result.fields

        # Classification check
        classification_total += 1
        type_ok = actual_type == expected_type
        if type_ok:
            classification_correct += 1
        print(f"   Classified as: {actual_type} (confidence={confidence:.2f}) {'✅' if type_ok else '❌'}")

        # Validation check
        if must_be_valid is not None:
            validation_total += 1
            actual_valid = result.validation.is_valid
            val_ok = actual_valid == must_be_valid
            if val_ok:
                validation_correct += 1
            print(f"   Validation: is_valid={actual_valid} (expected={must_be_valid}) {'✅' if val_ok else '❌'}")
            if result.validation.missing_fields:
                print(f"   Missing: {result.validation.missing_fields}")
            if result.validation.conflicts:
                print(f"   Conflicts: {result.validation.conflicts}")

        # Field-level accuracy
        bucket = results_per_type.get(expected_type)
        if bucket is None:
            continue
        bucket["docs"] += 1

        for check_key, expected_value in required_fields.items():
            if check_key.endswith("_contains"):
                field_name = check_key[:-9]  # strip "_contains"
                actual = str(fields.get(field_name, ""))
                hit = expected_value in actual
            elif check_key.endswith("_min_count"):
                field_name = check_key[:-10]
                actual = fields.get(field_name, [])
                hit = isinstance(actual, list) and len(actual) >= int(expected_value)
            elif check_key.endswith("_non_empty"):
                field_name = check_key[:-10]
                actual = fields.get(field_name, "")
                hit = bool(actual) and str(actual).strip() != ""
            elif check_key.endswith("_prefix"):
                field_name = check_key[:-7]
                actual = str(fields.get(field_name, ""))
                hit = actual.startswith(str(expected_value))
            elif check_key == "must_be_valid":
                continue
            else:
                actual = str(fields.get(check_key, ""))
                hit = expected_value in actual

            if hit:
                bucket["tp"] += 1
                status = "✅"
            else:
                bucket["fn"] += 1
                status = "❌"

            actual_display = fields.get(check_key.replace("_contains", "")
                                          .replace("_min_count", "")
                                          .replace("_non_empty", "")
                                          .replace("_prefix", ""), "—")
            if isinstance(actual_display, list):
                actual_display = f"[{len(actual_display)} items]"
            print(f"   {status} {check_key}: expected '{expected_value}' | got '{str(actual_display)[:50]}'")

    # Summary
    print("\n" + "=" * 70)
    print("  CLASSIFICATION ACCURACY")
    print("=" * 70)
    if classification_total:
        acc = classification_correct / classification_total * 100
        print(f"  Correct: {classification_correct}/{classification_total} = {acc:.1f}%")

    print("\n" + "=" * 70)
    print("  VALIDATION ACCURACY")
    print("=" * 70)
    if validation_total:
        val_acc = validation_correct / validation_total * 100
        print(f"  Correct: {validation_correct}/{validation_total} = {val_acc:.1f}%")

    print("\n" + "=" * 70)
    print("  FIELD EXTRACTION — PRECISION / RECALL / F1 PER TYPE")
    print("=" * 70)

    overall_tp = overall_fp = overall_fn = 0
    for doc_type, counts in results_per_type.items():
        tp = counts["tp"]
        fp = counts["fp"]
        fn = counts["fn"]
        overall_tp += tp
        overall_fp += fp
        overall_fn += fn

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        n_docs = counts["docs"]

        grade = "🟢" if f1 >= 0.80 else "🟡" if f1 >= 0.60 else "🔴"
        print(f"  {grade} {doc_type.upper():12s}  P={precision:.2f}  R={recall:.2f}  F1={f1:.2f}  ({n_docs} docs)")

    # Overall
    p_all = overall_tp / (overall_tp + overall_fp) if (overall_tp + overall_fp) > 0 else 0.0
    r_all = overall_tp / (overall_tp + overall_fn) if (overall_tp + overall_fn) > 0 else 0.0
    f1_all = (2 * p_all * r_all / (p_all + r_all)) if (p_all + r_all) > 0 else 0.0
    print(f"  {'─' * 50}")
    print(f"  {'OVERALL':14s}  P={p_all:.2f}  R={r_all:.2f}  F1={f1_all:.2f}")
    print("=" * 70 + "\n")

    # Exit with non-zero if F1 < 0.70
    if f1_all < 0.70:
        print("⚠️  Overall F1 below 0.70 threshold.")
        sys.exit(1)
    else:
        print("✅ Evaluation passed.")


if __name__ == "__main__":
    run_evaluation()
