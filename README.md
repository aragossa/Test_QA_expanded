# Ammeter Emulators

TCP emulators for three current measurement devices. Each device accepts one
command and returns the measured current as a UTF-8 encoded number.

| Device | Port in `main.py` | Command | Formula |
|---|---:|---|---|
| Greenlee | 5001 | `MEASURE_GREENLEE -get_measurement` | `I = V / R` |
| ENTES | 5002 | `MEASURE_ENTES -get_data` | `I = B * K` |
| CIRCUTOR | 5003 | `MEASURE_CIRCUTOR -get_measurement -current` | `I = sum(V * dt)` |

## Setup

Python 3.10 or newer is recommended. Direct dependencies are deliberately kept
to three packages: PyYAML for configuration, matplotlib for PNG visualization,
and pytest for tests. The final verification used PyYAML 6.0.3, matplotlib
3.11.1, and pytest 9.1.1.

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

The legacy example now calls the same working entry point:

```sh
.venv/bin/python examples/run_tests.py
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

## Bonus features

Bonus behavior is configured under `bonus` in `config/config.yaml`:

- visualization writes a PNG with measurements, mean, and optional reference;
- consistency reports range and coefficient of variation (CV);
- accuracy reports bias, MAE, RMSE, relative error, and tolerance status;
- error simulation raises a deterministic timeout, connection, or malformed
  response error on selected sample numbers.

Accuracy is intentionally omitted unless `reference_currents` contains a known
value for that device. Random emulator outputs alone cannot establish physical
accuracy. `compare_ammeters` ranks accuracy by relative error, consistency by
CV, and reliability by relative error with CV as the tie-breaker. RMSE remains
available in each individual device report:

```python
comparison = framework.compare_ammeters(
    "greenlee_test_id", "entes_test_id", "circutor_test_id"
)
```

To exercise error handling without changing an emulator, enable simulation and
select one or more one-based sample numbers:

```yaml
error_simulation:
  enabled: true
  type: timeout  # timeout, connection, or malformed
  fail_on_samples: [2]
```

Archived results can be retrieved or compared from Python:

```python
from src.testing.test_framework import AmmeterTestFramework

framework = AmmeterTestFramework()
available = framework.list_results()
saved = framework.load_result("test_id")
comparison = framework.compare_results("first_test_id", "second_test_id")
```

`list_results("greenlee")` optionally filters the archive by device. Results are
returned newest first, so UUIDs do not need to be found with filesystem tools.

## Sample results

The committed `sample_results/` directory contains three deterministic JSON
reports, a cross-device comparison, and an example PNG. They demonstrate
accuracy with explicit reference values and are labelled as software examples,
not physical calibration results.

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
Configuration failures, result listing, startup readiness, the direct example,
and committed sample artifacts also have regression coverage.

## Limitations

- Emulators process one connection at a time and have no explicit shutdown API.
- Integration tests isolate real emulators in short-lived processes and use
  dynamically allocated ports.
- Timing tests use a deterministic fake clock and do not assess real-time
  scheduling precision.
- JSON archiving is intentionally local and has no locking for concurrent runs.
- Accuracy rankings are meaningful only when reference currents come from a
  controlled external source and test conditions are comparable.
- The original unused `TestLogger` scaffold is not part of the execution path;
  console summaries and structured JSON provide result reporting.

## Design decisions

- The existing `AmmeterTestFramework` and YAML structure were completed instead
  of introducing a separate framework.
- Sampling fails fast: a failed request produces no misleading partial archive.
- Population standard deviation describes the complete collected run.
- JSON keeps archived results human-readable and dependency-free.
- Accuracy requires a user-supplied reference; consistency never substitutes
  for physical accuracy.
- Fake TCP servers remain limited to responses that real emulators cannot
  produce, while configurable error simulation exercises framework handling.
- Local PNG and JSON output is sufficient here; logging services, databases, and
  concurrent writers would add complexity without a requirement.

## Possible improvements

Add file locking if concurrent processes need to write the same result archive.
