# Ammeter Emulators

TCP emulators for three current measurement devices. Each device accepts one
command and returns the measured current as a UTF-8 encoded number.

| Device | Port in `main.py` | Command | Formula |
|---|---:|---|---|
| Greenlee | 5001 | `MEASURE_GREENLEE -get_measurement` | `I = V / R` |
| ENTES | 5002 | `MEASURE_ENTES -get_data` | `I = B * K` |
| CIRCUTOR | 5003 | `MEASURE_CIRCUTOR -get_measurement -current` | `I = sum(V * dt)` |

## Setup

Python 3.10 or newer is recommended. Runtime configuration uses PyYAML and the
tests use pytest; both are listed in the existing `requirements.txt`.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

On Windows, replace `.venv/bin/python` with `.venv\\Scripts\\python`.

## Run the emulators

```sh
.venv/bin/python main.py
```

The script starts all three servers and runs the configured measurement test for
each device. It prints the sample count, mean current, and test ID, then stores
the complete results under `results/<test_id>.json`.

Example output shape (values and IDs vary):

```text
GREENLEE: 3 measurements, mean 0.0518 A, test ID f8d8bd7f...
ENTES: 3 measurements, mean 88.2584 A, test ID b73d2e45...
CIRCUTOR: 3 measurements, mean 0.0241 A, test ID a3edfae8...
```

## Configuration

Edit `config/config.yaml` to select:

- `measurements_count` — maximum number of samples;
- `total_duration_seconds` — maximum run duration, or `null`;
- `sampling_frequency_hz` — requests per second;
- device port, command, and response timeout;
- result archive directory.

At least a count or duration must be set. Duration-based runs also require a
frequency. If count and duration are both present, the first reached limit ends
sampling. A failed measurement aborts the run and no partial result is archived.

Each JSON result contains a unique test ID, UTC creation time, device name,
sampling metadata, raw measurements, and the following population metrics:
mean, median, standard deviation, minimum, and maximum.

Archived results can be retrieved or compared from Python:

```python
from src.testing.test_framework import AmmeterTestFramework

framework = AmmeterTestFramework()
saved = framework.load_result("test_id")
comparison = framework.compare_results("first_test_id", "second_test_id")
```

## Run the tests

```sh
.venv/bin/python -m pytest -q
```

## Coverage

The suite covers all three commands, numeric response format, formula-derived
ranges, deterministic formula calculations, connection failure, timeout,
empty/malformed/non-finite responses, repeated measurements, configurable
sampling, required statistics, and archive/retrieval/comparison of results. See
`TEST_PLAN.md` for traceability and `DEFECTS.md` for findings.

## Limitations

- Emulators process one connection at a time and have no explicit shutdown API.
- Integration tests isolate real emulators in short-lived processes and use
  dynamically allocated ports.
- Timing tests use a deterministic fake clock and do not assess real-time
  scheduling precision.
- JSON archiving is intentionally local and has no locking for concurrent runs.
- Visualization and comparison of physical device accuracy are not implemented.

## Possible improvements

Visualization could be added if it becomes a product requirement.
