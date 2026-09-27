# Model card

## Model

Class-weighted logistic regression with median imputation, explicit missing-value indicators,
zero-variance removal, and standardization. The artifact predicts the probability that a SECOM
manufacturing example belongs to the failed class.

## Intended use

Educational and portfolio-grade analysis of rare-event classification in high-dimensional industrial
data. It demonstrates evaluation and decision-threshold practices; it is not intended to release or
scrap physical products.

## Evaluation design

The newest 20% of timestamped rows is held out. All feature filtering, imputation, scaling, fitting,
and threshold selection exclude this test period. Five-fold stratified out-of-fold predictions on the
earlier 80% set the threshold. Confidence intervals resample only the final holdout.

## Risks and limitations

- Sensor meanings are anonymized, preventing causal or physical interpretation.
- Only 17 failures occur in the chronological holdout; metrics have material uncertainty.
- Recall drops from 50.6% out-of-fold to 35.3% on the later holdout.
- Probabilities are not sufficiently calibrated for direct economic decisions.
- The 10:1 missed-failure cost ratio is illustrative, not supplied by a fabrication plant.

Production use would require current fab data, equipment and lot identifiers, group-aware validation,
calibration, drift monitoring, engineering review, and a documented intervention policy.

