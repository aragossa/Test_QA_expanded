import json
from pathlib import Path

from src.testing.test_framework import AmmeterTestFramework


SAMPLES = Path("sample_results")


def test_sample_results_match_calculations_and_comparison(tmp_path):
    framework = AmmeterTestFramework.__new__(AmmeterTestFramework)
    framework.results_directory = tmp_path
    test_ids = []

    for ammeter_type in ("greenlee", "entes", "circutor"):
        sample = json.loads(
            (SAMPLES / f"{ammeter_type}.json").read_text(encoding="utf-8")
        )
        measurements = sample["measurements"]
        reference = sample["analysis"]["accuracy"]["reference_current"]

        assert sample["analysis"] == {
            **framework.analyze(measurements),
            "consistency": framework.evaluate_consistency(measurements, 0.1),
            "accuracy": framework.assess_accuracy(measurements, reference, 5.0),
        }
        framework.archive_result(sample)
        test_ids.append(sample["test_id"])

    expected_comparison = json.loads(
        (SAMPLES / "comparison.json").read_text(encoding="utf-8")
    )
    assert framework.compare_ammeters(*test_ids) == expected_comparison
    assert (SAMPLES / "greenlee.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
