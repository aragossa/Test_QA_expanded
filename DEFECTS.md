# Defects

Only reproducible defects are listed here. Suspected issues remain in the
`Open observations` section of `TEST_PLAN.md` until a test confirms them.

## D01 — TCP client cannot provide a bounded, validated measurement

- **Status:** Fixed
- **Severity:** High
- **Detected by:** T01, T02, T04, T06, T07, T08, T12
- **Affected file:** `Ammeters/client.py`
- **Expected:** The caller receives a finite `float`, and waiting is bounded by
  a configurable timeout.
- **Actual:** The client only printed the raw response, returned `None`, and had
  no socket timeout or response validation.
- **Minimal fix:** Return a parsed finite `float`, set a default socket timeout,
  and raise `ValueError` for empty, malformed, or non-finite responses.
- **Verification:** `tests/test_tcp_measurements.py`

## D02 — Main script does not request measurements

- **Status:** Fixed
- **Severity:** High
- **Detected by:** Required usage scenario in the exercise specification
- **Affected file:** `main.py`
- **Expected:** Running `main.py` obtains and prints data from all three ammeters.
- **Actual:** All client calls were commented out and their example commands did
  not match the emulator protocols.
- **Minimal fix:** Request each emulator using its `get_current_command` property
  and print the returned current.
- **Verification:** `.venv/bin/python main.py` returned one current value from
  Greenlee, ENTES, and CIRCUTOR.

## D03 — Documentation does not match the implemented TCP protocol

- **Status:** Fixed
- **Severity:** Medium
- **Detected by:** T01 protocol review
- **Affected file:** `README.md`
- **Expected:** Documented ports and commands match the working usage scenario.
- **Actual:** README ports conflicted with `main.py`, and the documented CIRCUTOR
  command omitted the required `-current` suffix.
- **Minimal fix:** Document the ports used by `main.py` and the exact command
  exposed by each emulator.
- **Verification:** Commands in README match each `get_current_command` property.

## D04 — Default pytest discovery fails on an unfinished source scaffold

- **Status:** Fixed
- **Severity:** Medium
- **Detected by:** Full test run
- **Affected file:** `src/testing/test_framework.py`
- **Expected:** `python -m pytest` collects and runs the delivered test suite.
- **Actual:** Pytest also collected `src/testing/test_framework.py` by filename
  and failed on its package-relative import before running the suite.
- **Minimal fix:** Add `pytest.ini` with `testpaths = tests`; the unrelated,
  unfinished framework remains unchanged.
- **Verification:** Full test run completes successfully.

## D05 — Required sampling, analysis, and result management are not implemented

- **Status:** Fixed
- **Severity:** High
- **Detected by:** Specification traceability review
- **Affected file:** `src/testing/test_framework.py`
- **Expected:** The framework supports configurable sampling, required metrics,
  unique result metadata, archiving, retrieval, and comparison.
- **Actual:** `run_test` contained only `pass`; the configuration values were
  empty and device definitions were commented out.
- **Minimal fix:** Complete the existing framework with standard-library
  sampling, statistics and JSON management, and activate the existing YAML
  configuration.
- **Verification:** T13–T15 in `tests/test_framework.py`.
