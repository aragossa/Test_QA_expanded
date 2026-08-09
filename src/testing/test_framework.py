import json
import math
import socket
import statistics
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from Ammeters.client import request_current_from_ammeter
from ..utils.config import load_config


class AmmeterTestFramework:
    """Collect, analyse, and archive current measurements."""

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = load_config(config_path)
        result_config = self.config.get("result_management") or {}
        self.results_directory = Path(result_config.get("directory", "results"))

    def run_test(self, ammeter_type: str) -> Dict:
        measurements = self.collect_measurements(ammeter_type)
        bonus_config = self.config.get("bonus") or {}
        reference = (bonus_config.get("accuracy") or {}).get(
            "reference_currents", {}
        ).get(ammeter_type)
        analysis = self.analyze(measurements)
        analysis["consistency"] = self.evaluate_consistency(
            measurements,
            (bonus_config.get("consistency") or {}).get(
                "maximum_coefficient_of_variation", 0.1
            ),
        )
        if reference is not None:
            analysis["accuracy"] = self.assess_accuracy(
                measurements,
                reference,
                (bonus_config.get("accuracy") or {}).get(
                    "tolerance_percent", 5.0
                ),
            )

        result = {
            "test_id": uuid.uuid4().hex,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ammeter_type": ammeter_type,
            "sampling": dict(self.config["testing"]["sampling"]),
            "measurements": measurements,
            "analysis": analysis,
        }
        visualization = bonus_config.get("visualization") or {}
        if visualization.get("enabled", False):
            result["visualization"] = str(
                self.create_visualization(result, visualization.get("directory"))
            )
        self.archive_result(result)
        return result

    def collect_measurements(self, ammeter_type: str) -> List[float]:
        try:
            ammeter = self.config["ammeters"][ammeter_type]
        except KeyError as error:
            raise ValueError(f"Unknown ammeter type: {ammeter_type}") from error

        sampling = self.config["testing"]["sampling"]
        count = sampling.get("measurements_count")
        duration = sampling.get("total_duration_seconds")
        frequency = sampling.get("sampling_frequency_hz")
        self._validate_sampling(count, duration, frequency)

        interval = 1 / frequency if frequency is not None else 0
        started_at = time.monotonic()
        measurements = []

        while True:
            elapsed = time.monotonic() - started_at
            if count is not None and len(measurements) >= count:
                break
            if duration is not None and elapsed >= duration:
                break

            sample_number = len(measurements) + 1
            self._simulate_error(sample_number)
            measurements.append(
                request_current_from_ammeter(
                    ammeter["port"],
                    ammeter["command"].encode("utf-8"),
                    timeout=ammeter.get("timeout_seconds", 2.0),
                )
            )

            if interval:
                next_sample_at = started_at + len(measurements) * interval
                if count is not None and len(measurements) >= count:
                    break
                if duration is not None and next_sample_at - started_at >= duration:
                    break
                remaining = next_sample_at - time.monotonic()
                if remaining > 0:
                    time.sleep(remaining)

        return measurements

    def _simulate_error(self, sample_number: int) -> None:
        simulation = (self.config.get("bonus") or {}).get("error_simulation") or {}
        if not simulation.get("enabled", False):
            return
        if sample_number not in simulation.get("fail_on_samples", []):
            return

        error_type = simulation.get("type", "timeout")
        errors = {
            "timeout": socket.timeout("Simulated response timeout"),
            "connection": ConnectionError("Simulated connection error"),
            "malformed": ValueError("Simulated malformed response"),
        }
        try:
            error = errors[error_type]
        except KeyError as exception:
            raise ValueError(f"Unsupported simulated error type: {error_type}") from exception
        raise error

    @staticmethod
    def _validate_sampling(count, duration, frequency):
        if count is None and duration is None:
            raise ValueError("Set measurements_count or total_duration_seconds")
        if count is not None and (not isinstance(count, int) or count <= 0):
            raise ValueError("measurements_count must be a positive integer")
        if duration is not None and duration <= 0:
            raise ValueError("total_duration_seconds must be positive")
        if frequency is not None and frequency <= 0:
            raise ValueError("sampling_frequency_hz must be positive")
        if duration is not None and frequency is None:
            raise ValueError("sampling_frequency_hz is required with total duration")

    @staticmethod
    def analyze(measurements: List[float]) -> Dict:
        if not measurements:
            raise ValueError("Cannot analyze an empty measurement set")

        return {
            "mean": statistics.mean(measurements),
            "median": statistics.median(measurements),
            "standard_deviation": statistics.pstdev(measurements),
            "minimum": min(measurements),
            "maximum": max(measurements),
        }

    @staticmethod
    def evaluate_consistency(
        measurements: List[float], maximum_coefficient_of_variation: float = 0.1
    ) -> Dict:
        if not measurements:
            raise ValueError("Cannot evaluate an empty measurement set")
        if maximum_coefficient_of_variation < 0:
            raise ValueError("Consistency threshold cannot be negative")

        mean = statistics.mean(measurements)
        deviation = statistics.pstdev(measurements)
        coefficient = deviation / abs(mean) if mean else None
        return {
            "range": max(measurements) - min(measurements),
            "coefficient_of_variation": coefficient,
            "within_threshold": (
                coefficient is not None
                and coefficient <= maximum_coefficient_of_variation
            ),
        }

    @staticmethod
    def assess_accuracy(
        measurements: List[float], reference_current: float, tolerance_percent: float = 5.0
    ) -> Dict:
        if not measurements:
            raise ValueError("Cannot assess an empty measurement set")
        if tolerance_percent < 0:
            raise ValueError("Accuracy tolerance cannot be negative")

        errors = [measurement - reference_current for measurement in measurements]
        mean_absolute_error = statistics.mean(abs(error) for error in errors)
        root_mean_square_error = math.sqrt(
            statistics.mean(error**2 for error in errors)
        )
        relative_error = (
            mean_absolute_error / abs(reference_current) * 100
            if reference_current
            else None
        )
        return {
            "reference_current": reference_current,
            "bias": statistics.mean(errors),
            "mean_absolute_error": mean_absolute_error,
            "root_mean_square_error": root_mean_square_error,
            "relative_error_percent": relative_error,
            "within_tolerance": (
                relative_error is not None and relative_error <= tolerance_percent
            ),
        }

    def create_visualization(self, result: Dict, directory=None) -> Path:
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError as error:
            raise RuntimeError("Visualization requires matplotlib") from error

        plot_directory = Path(directory or self.results_directory / "plots")
        plot_directory.mkdir(parents=True, exist_ok=True)
        plot_path = plot_directory / f"{result['test_id']}.png"
        measurements = result["measurements"]

        figure, axis = plt.subplots(figsize=(7, 4))
        sample_numbers = range(1, len(measurements) + 1)
        axis.plot(sample_numbers, measurements, marker="o", label="Current")
        axis.axhline(
            result["analysis"]["mean"], linestyle="--", label="Mean", color="tab:orange"
        )
        accuracy = result["analysis"].get("accuracy")
        if accuracy:
            axis.axhline(
                accuracy["reference_current"],
                linestyle=":",
                label="Reference",
                color="tab:green",
            )
        axis.set(
            title=f"{result['ammeter_type'].upper()} current measurements",
            xlabel="Sample",
            ylabel="Current (A)",
        )
        axis.grid(alpha=0.3)
        axis.legend()
        figure.tight_layout()
        figure.savefig(plot_path)
        plt.close(figure)
        return plot_path

    def archive_result(self, result: Dict) -> Path:
        self.results_directory.mkdir(parents=True, exist_ok=True)
        result_path = self.results_directory / f"{result['test_id']}.json"
        result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result_path

    def load_result(self, test_id: str) -> Dict:
        result_path = self.results_directory / f"{test_id}.json"
        return json.loads(result_path.read_text(encoding="utf-8"))

    def list_results(self, ammeter_type=None) -> List[Dict]:
        if not self.results_directory.exists():
            return []

        results = []
        for result_path in self.results_directory.glob("*.json"):
            result = json.loads(result_path.read_text(encoding="utf-8"))
            if ammeter_type is None or result.get("ammeter_type") == ammeter_type:
                results.append(
                    {
                        "test_id": result["test_id"],
                        "created_at": result["created_at"],
                        "ammeter_type": result["ammeter_type"],
                    }
                )
        return sorted(results, key=lambda result: result["created_at"], reverse=True)

    def compare_results(self, *test_ids: str) -> Dict:
        if len(test_ids) < 2:
            raise ValueError("At least two test IDs are required for comparison")
        return {
            test_id: self.load_result(test_id)["analysis"] for test_id in test_ids
        }

    def compare_ammeters(self, *test_ids: str) -> Dict:
        if len(test_ids) < 2:
            raise ValueError("At least two test IDs are required for comparison")
        results = [self.load_result(test_id) for test_id in test_ids]
        if any("accuracy" not in result["analysis"] for result in results):
            raise ValueError("All compared results require a reference current")

        by_accuracy = sorted(
            results,
            key=lambda result: result["analysis"]["accuracy"]["relative_error_percent"],
        )
        by_consistency = sorted(
            results,
            key=lambda result: (
                result["analysis"]["consistency"]["coefficient_of_variation"]
                is None,
                (
                    result["analysis"]["consistency"]["coefficient_of_variation"]
                    if result["analysis"]["consistency"]["coefficient_of_variation"]
                    is not None
                    else float("inf")
                ),
            ),
        )
        by_reliability = sorted(
            results,
            key=lambda result: (
                result["analysis"]["accuracy"]["relative_error_percent"],
                (
                    result["analysis"]["consistency"]["coefficient_of_variation"]
                    if result["analysis"]["consistency"]["coefficient_of_variation"]
                    is not None
                    else float("inf")
                ),
            ),
        )
        return {
            "most_accurate": by_accuracy[0]["ammeter_type"],
            "most_consistent": by_consistency[0]["ammeter_type"],
            "most_reliable": by_reliability[0]["ammeter_type"],
            "accuracy_ranking": [result["ammeter_type"] for result in by_accuracy],
            "consistency_ranking": [
                result["ammeter_type"] for result in by_consistency
            ],
        }
