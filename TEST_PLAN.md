# Test Plan

## Scope

The tests cover the TCP measurement path for Greenlee, ENTES, and CIRCUTOR,
configurable sampling, statistical analysis, and JSON result archiving.

## Out of scope

Performance benchmarking, interactive visualization, advanced statistical
research, and a database-backed result service are outside this compact QA
exercise.

## Assumptions

- Each emulator's `get_current_command` property defines its actual protocol.
- An empty response means that the request was rejected.
- `nan` and infinite values are not valid current measurements.
- Formula ranges are derived from the input ranges in the emulator source.
- Timeout tests verify bounded waiting, not precise timing.
- When count and duration are both configured, sampling stops at the first limit.
- Sampling errors fail the run immediately; incomplete results are not archived.
- Standard deviation is calculated for the complete collected population.

## Checks

| ID | Check | Type | Environment | Priority | Status |
|---|---|---|---|---|---|
| T01 | Correct command returns a measurement for every ammeter | Integration | Real emulators | P0 | Passed |
| T02 | Response is a finite `float` | Integration | Real emulators | P0 | Passed |
| T03 | Measurement is within the formula-derived range | Integration | Real emulators | P0 | Passed |
| T04 | Wrong command is rejected predictably | Integration | Real emulators | P0 | Passed |
| T05 | Connection failure is propagated | Integration | No server | P0 | Passed |
| T06 | Silent server triggers a timeout | Integration | Fake server | P0 | Passed |
| T07 | Empty or malformed response is rejected | Integration | Fake server | P0 | Passed |
| T08 | `nan` and infinite responses are rejected | Integration | Fake server | P1 | Passed |
| T09 | Greenlee implements `I = V / R` | Unit | Deterministic inputs | P1 | Passed |
| T10 | ENTES implements `I = B * K` | Unit | Deterministic inputs | P1 | Passed |
| T11 | CIRCUTOR integrates ten `V * dt` samples | Unit | Deterministic inputs | P1 | Passed |
| T12 | Repeated measurements survive one rejected request | Integration | Real emulators | P1 | Passed |
| T13 | Count-, duration-, and frequency-based sampling is deterministic | Unit + integration | Stubbed clock and real emulators | P0 | Passed |
| T14 | Mean, median, population deviation, minimum, and maximum are correct | Unit | Fixed measurements | P0 | Passed |
| T15 | Results have ID/metadata and can be archived, listed, loaded, and compared | Unit | Temporary directory | P0 | Passed |

## Observation workflow

An incidental issue is recorded first as an observation. It is treated as a
defect only after a deterministic test reproduces it. The regression test is
linked to the check responsible for that behavior, even if another check first
exposed the symptom. Findings outside the stated scope are not investigated
unless they block a P0 check.

## Open observations

None.

## Bonus checks

| ID | Check | Type | Priority | Status |
|---|---|---|---|---|
| B01 | PNG visualization contains measurements, mean, and optional reference | Integration | P1 | Passed |
| B02 | Measurement consistency is evaluated with range and coefficient of variation | Unit | P1 | Passed |
| B03 | Accuracy and cross-ammeter rankings use explicit reference currents | Unit | P1 | Passed |
| B04 | Timeout, connection, and malformed-response errors can be simulated deterministically | Unit | P1 | Passed |

## Stop criteria

All P0 and P1 checks pass, `main.py` obtains one measurement from every emulator,
confirmed defects are documented, and the final repository diff contains no
unrelated changes.

## Last execution

- Command: `.venv/bin/python -m pytest -q`
- Result: `52 passed`
- Date: 2026-08-09
