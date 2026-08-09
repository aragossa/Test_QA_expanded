# Sample Results

These deterministic artifacts demonstrate the result schema and bonus comparison
without presenting random emulator output as a physical accuracy experiment.
Each device uses its own explicitly documented reference current. The samples
show that the most consistent device is not necessarily the most accurate one.

- Greenlee: reference `1.0 A`, measurements `0.98 A`.
- ENTES: reference `100.0 A`, measurements `99.0`, `100.0`, `101.0 A`.
- CIRCUTOR: reference `0.05 A`, measurements `0.048`, `0.05`, `0.052 A`.

`comparison.json` ranks accuracy by relative error, consistency by coefficient
of variation, and reliability by relative error with consistency as tie-breaker.
These are illustrative software results, not calibration certificates.

