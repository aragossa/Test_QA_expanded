import math

import pytest

import src.testing.test_framework as framework_module
from src.testing.test_framework import AmmeterTestFramework
from conftest import AMMETERS


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def build_framework(tmp_path, sampling, ammeters=None):
    framework = AmmeterTestFramework.__new__(AmmeterTestFramework)
    framework.config = {
        "testing": {"sampling": sampling},
        "ammeters": ammeters
        or {"greenlee": {"port": 5001, "command": "MEASURE", "timeout_seconds": 0.1}},
    }
    framework.results_directory = tmp_path
    return framework


def test_sampling_collects_configured_measurement_count(monkeypatch, tmp_path):
    framework = build_framework(
        tmp_path,
        {
            "measurements_count": 3,
            "total_duration_seconds": None,
            "sampling_frequency_hz": None,
        },
    )
    values = iter((1.0, 2.0, 3.0))
    monkeypatch.setattr(
        framework_module, "request_current_from_ammeter", lambda *_, **__: next(values)
    )

    assert framework.collect_measurements("greenlee") == [1.0, 2.0, 3.0]


def test_sampling_respects_duration_and_frequency(monkeypatch, tmp_path):
    framework = build_framework(
        tmp_path,
        {
            "measurements_count": None,
            "total_duration_seconds": 2.0,
            "sampling_frequency_hz": 2.0,
        },
    )
    clock = FakeClock()
    monkeypatch.setattr(framework_module.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(framework_module.time, "sleep", clock.sleep)
    monkeypatch.setattr(
        framework_module, "request_current_from_ammeter", lambda *_, **__: 1.0
    )

    assert framework.collect_measurements("greenlee") == [1.0] * 4
    assert clock.sleeps == [0.5, 0.5, 0.5]


@pytest.mark.parametrize(
    "sampling",
    [
        {"measurements_count": None, "total_duration_seconds": None, "sampling_frequency_hz": None},
        {"measurements_count": 0, "total_duration_seconds": None, "sampling_frequency_hz": None},
        {"measurements_count": None, "total_duration_seconds": 1, "sampling_frequency_hz": 0},
        {"measurements_count": None, "total_duration_seconds": 1, "sampling_frequency_hz": None},
    ],
)
def test_invalid_sampling_configuration_is_rejected(tmp_path, sampling):
    framework = build_framework(tmp_path, sampling)

    with pytest.raises(ValueError):
        framework.collect_measurements("greenlee")


def test_measurement_error_aborts_run_without_partial_archive(monkeypatch, tmp_path):
    framework = build_framework(
        tmp_path,
        {
            "measurements_count": 3,
            "total_duration_seconds": None,
            "sampling_frequency_hz": None,
        },
    )
    values = iter((1.0, ValueError("bad measurement")))

    def request(*_, **__):
        value = next(values)
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(framework_module, "request_current_from_ammeter", request)

    with pytest.raises(ValueError, match="bad measurement"):
        framework.run_test("greenlee")
    assert list(tmp_path.iterdir()) == []


def test_analysis_calculates_required_population_metrics():
    result = AmmeterTestFramework.analyze([1.0, 2.0, 3.0, 4.0])

    assert result == {
        "mean": 2.5,
        "median": 2.5,
        "standard_deviation": pytest.approx(math.sqrt(1.25)),
        "minimum": 1.0,
        "maximum": 4.0,
    }


def test_result_can_be_archived_loaded_and_compared(monkeypatch, tmp_path):
    framework = build_framework(
        tmp_path,
        {
            "measurements_count": 2,
            "total_duration_seconds": None,
            "sampling_frequency_hz": None,
        },
    )
    runs = iter(([1.0, 3.0], [2.0, 4.0]))
    monkeypatch.setattr(framework, "collect_measurements", lambda _: next(runs))

    first = framework.run_test("greenlee")
    second = framework.run_test("greenlee")

    assert first["test_id"] != second["test_id"]
    assert first["created_at"].endswith("+00:00")
    assert framework.load_result(first["test_id"]) == first
    assert framework.compare_results(first["test_id"], second["test_id"]) == {
        first["test_id"]: first["analysis"],
        second["test_id"]: second["analysis"],
    }


def test_archived_results_can_be_listed_and_filtered(tmp_path):
    framework = build_framework(
        tmp_path,
        {
            "measurements_count": 1,
            "total_duration_seconds": None,
            "sampling_frequency_hz": None,
        },
    )
    archived = [
        {
            "test_id": "older-greenlee",
            "created_at": "2026-08-09T08:00:00+00:00",
            "ammeter_type": "greenlee",
        },
        {
            "test_id": "newer-entes",
            "created_at": "2026-08-09T09:00:00+00:00",
            "ammeter_type": "entes",
        },
    ]
    for result in archived:
        framework.archive_result(result)

    assert framework.list_results() == [
        {
            "test_id": "newer-entes",
            "created_at": "2026-08-09T09:00:00+00:00",
            "ammeter_type": "entes",
        },
        {
            "test_id": "older-greenlee",
            "created_at": "2026-08-09T08:00:00+00:00",
            "ammeter_type": "greenlee",
        },
    ]
    assert framework.list_results("greenlee") == [archived[0]]



@pytest.mark.parametrize("emulator_class,minimum,maximum", AMMETERS)
def test_framework_collects_from_each_real_ammeter(
    real_emulator, emulator_class, minimum, maximum, tmp_path
):
    port = real_emulator(emulator_class)
    ammeter_name = {
        "GreenleeAmmeter": "greenlee",
        "EntesAmmeter": "entes",
        "CircutorAmmeter": "circutor",
    }[emulator_class.__name__]
    framework = build_framework(
        tmp_path,
        {
            "measurements_count": 2,
            "total_duration_seconds": None,
            "sampling_frequency_hz": None,
        },
        {
            ammeter_name: {
                "port": port,
                "command": emulator_class(port).get_current_command.decode("utf-8"),
                "timeout_seconds": 0.5,
            }
        },
    )

    measurements = framework.collect_measurements(ammeter_name)

    assert len(measurements) == 2
    assert all(minimum <= measurement <= maximum for measurement in measurements)
