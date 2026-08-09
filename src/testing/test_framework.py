import json
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
        result = {
            "test_id": uuid.uuid4().hex,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ammeter_type": ammeter_type,
            "sampling": dict(self.config["testing"]["sampling"]),
            "measurements": measurements,
            "analysis": self.analyze(measurements),
        }
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

    def archive_result(self, result: Dict) -> Path:
        self.results_directory.mkdir(parents=True, exist_ok=True)
        result_path = self.results_directory / f"{result['test_id']}.json"
        result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result_path

    def load_result(self, test_id: str) -> Dict:
        result_path = self.results_directory / f"{test_id}.json"
        return json.loads(result_path.read_text(encoding="utf-8"))

    def compare_results(self, *test_ids: str) -> Dict:
        if len(test_ids) < 2:
            raise ValueError("At least two test IDs are required for comparison")
        return {
            test_id: self.load_result(test_id)["analysis"] for test_id in test_ids
        }
