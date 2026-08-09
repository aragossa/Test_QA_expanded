import math
import socket

import pytest

import src.testing.test_framework as framework_module
from src.testing.test_framework import AmmeterTestFramework


def build_framework(tmp_path, bonus=None):
    framework = AmmeterTestFramework.__new__(AmmeterTestFramework)
    framework.results_directory = tmp_path
    framework.config = {
        "testing": {
            "sampling": {
                "measurements_count": 3,
                "total_duration_seconds": None,
                "sampling_frequency_hz": None,
            }
        },
        "ammeters": {
            "greenlee": {
                "port": 5001,
                "command": "MEASURE",
                "timeout_seconds": 0.1,
            }
        },
        "bonus": bonus or {},
    }
    return framework


def test_consistency_uses_coefficient_of_variation():
    consistent = AmmeterTestFramework.evaluate_consistency([9.0, 10.0, 11.0], 0.1)
    inconsistent = AmmeterTestFramework.evaluate_consistency([0.0, 20.0], 0.1)

    assert consistent["range"] == 2.0
    assert consistent["coefficient_of_variation"] == pytest.approx(
        math.sqrt(2 / 3) / 10
    )
    assert consistent["within_threshold"] is True
    assert inconsistent["within_threshold"] is False


def test_accuracy_is_calculated_against_known_reference():
    accuracy = AmmeterTestFramework.assess_accuracy([9.0, 10.0, 11.0], 10.0, 10.0)

    assert accuracy == {
        "reference_current": 10.0,
        "bias": 0.0,
        "mean_absolute_error": pytest.approx(2 / 3),
        "root_mean_square_error": pytest.approx(math.sqrt(2 / 3)),
        "relative_error_percent": pytest.approx(20 / 3),
        "within_tolerance": True,
    }


def test_accuracy_is_omitted_without_reference(monkeypatch, tmp_path):
    framework = build_framework(tmp_path)
    monkeypatch.setattr(framework, "collect_measurements", lambda _: [1.0, 1.0, 1.0])

    result = framework.run_test("greenlee")

    assert "consistency" in result["analysis"]
    assert "accuracy" not in result["analysis"]


def test_visualization_creates_png_with_measurements_mean_and_reference(tmp_path):
    framework = build_framework(tmp_path)
    result = {
        "test_id": "visual-test",
        "ammeter_type": "greenlee",
        "measurements": [9.0, 10.0, 11.0],
        "analysis": {
            "mean": 10.0,
            "accuracy": {"reference_current": 10.0},
        },
    }

    plot_path = framework.create_visualization(result)

    assert plot_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.parametrize(
    ("error_type", "expected_exception"),
    [
        ("timeout", socket.timeout),
        ("connection", ConnectionError),
        ("malformed", ValueError),
    ],
)
def test_configured_error_is_simulated_on_selected_sample(
    monkeypatch, tmp_path, error_type, expected_exception
):
    framework = build_framework(
        tmp_path,
        {
            "error_simulation": {
                "enabled": True,
                "type": error_type,
                "fail_on_samples": [2],
            }
        },
    )
    calls = []
    monkeypatch.setattr(
        framework_module,
        "request_current_from_ammeter",
        lambda *_, **__: calls.append("request") or 1.0,
    )

    with pytest.raises(expected_exception, match="Simulated"):
        framework.collect_measurements("greenlee")
    assert calls == ["request"]


def test_ammeter_comparison_ranks_accuracy_consistency_and_reliability(tmp_path):
    framework = build_framework(tmp_path)
    results = [
        {
            "test_id": "greenlee",
            "ammeter_type": "greenlee",
            "analysis": {
                "accuracy": {
                    "root_mean_square_error": 0.2,
                    "relative_error_percent": 2.0,
                },
                "consistency": {"coefficient_of_variation": 0.04},
            },
        },
        {
            "test_id": "entes",
            "ammeter_type": "entes",
            "analysis": {
                "accuracy": {
                    "root_mean_square_error": 0.1,
                    "relative_error_percent": 1.0,
                },
                "consistency": {"coefficient_of_variation": 0.05},
            },
        },
        {
            "test_id": "circutor",
            "ammeter_type": "circutor",
            "analysis": {
                "accuracy": {
                    "root_mean_square_error": 0.3,
                    "relative_error_percent": 3.0,
                },
                "consistency": {"coefficient_of_variation": 0.0},
            },
        },
    ]
    for result in results:
        framework.archive_result(result)

    comparison = framework.compare_ammeters("greenlee", "entes", "circutor")

    assert comparison == {
        "most_accurate": "entes",
        "most_consistent": "circutor",
        "most_reliable": "entes",
        "accuracy_ranking": ["entes", "greenlee", "circutor"],
        "consistency_ranking": ["circutor", "greenlee", "entes"],
    }
