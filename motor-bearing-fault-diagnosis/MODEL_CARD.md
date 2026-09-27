# Model card

## Intended use

Educational analysis of load transfer and signal representations on the CWRU bearing dataset. The models can support reproducible experiments and code review. They are not intended to trigger maintenance or safety actions on physical equipment.

## Training domain

- CWRU 2 hp test motor
- drive-end accelerometer sampled at 12 kHz
- normal bearing and three 0.007-inch EDM fault classes
- steady operating loads from 0 to 3 hp

## Evaluation protocol

The classical benchmark holds out one complete motor load per fold. Source recordings therefore do not cross the train/test boundary. The CNN trains on 0–1 hp, uses 2 hp for early stopping, and evaluates once on 3 hp.

## Current evidence

- Clean leave-one-load-out Extra Trees macro-F1: 1.000
- Clean 3 hp CNN macro-F1: 1.000
- 3 hp Extra Trees macro-F1 at 0 dB additive Gaussian noise: 0.7049
- 3 hp Extra Trees expected calibration error: 0.0256
- 3 hp Extra Trees multiclass Brier score: 0.0041

These numbers apply only to the checked-in data manifest and generated evaluation artifacts.

## Known gaps

- artificially seeded faults rather than natural degradation
- one laboratory rig and sensor placement
- steady speed and isolated single faults
- no external-machine validation
- no compound faults, CT/accelerometer faults, clipping or variable-speed ramps

An industrial trial would require representative sensors, machine-specific baselines, natural fault history, out-of-distribution detection and a human-reviewed maintenance workflow.
