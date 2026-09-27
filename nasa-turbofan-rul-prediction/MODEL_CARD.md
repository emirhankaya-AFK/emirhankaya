# Model card

## Purpose

Compare tabular degradation features and a short sequence model for remaining-useful-life prediction on NASA C-MAPSS FD001. This is a prognostics benchmark, not an aircraft maintenance product.

## Data and split

FD001 is simulated and contains one operating condition and one high-pressure-compressor degradation mode. Complete engine identities are separated in validation. The final reported test uses NASA's 100 official truncated engine trajectories and RUL targets.

## Evidence

- median baseline test MAE: 35.90 cycles
- Histogram Gradient Boosting test MAE: 13.90 cycles
- 30-cycle GRU test MAE: 11.15 cycles
- classical 90% conformal interval empirical coverage: 86%

## Risks

Late predictions can defer maintenance, so the evaluation includes NASA's asymmetric score and late-prediction rate. Point error alone is insufficient. The interval under-covers its nominal target and should not be treated as a certified uncertainty estimate.

## Unsupported uses

- operational aircraft maintenance decisions
- different engine families without retraining and validation
- multiple or previously unseen fault modes
- safety-critical alarms
- claims based on real flight-recorder data
