# Model card

## Model and purpose

Histogram gradient-boosting regression estimates hourly NO2 concentration from metal-oxide sensor
responses, weather measurements and cyclical time features. The project is an educational study of
calibration under field drift, not a regulatory monitoring instrument.

## Validation boundary

Rows remain in timestamp order. The oldest 80% trains the pipeline, the following 10% calibrates a
split-conformal interval, and the newest 10% is evaluated once. Imputation is fitted only on training
data. A training-median baseline is reported beside the model.

## Risks

- The test R² is only 0.049 despite improvement in MAE and RMSE over the baseline.
- The 90% interval is conservative and wide at ±73.58 µg/m³.
- Strong feature drift means performance can change after deployment.
- The dataset represents one device, location and historical period.

Real deployment requires new co-location measurements, scheduled recalibration, live drift alarms,
sensor health checks and review by air-quality specialists.

