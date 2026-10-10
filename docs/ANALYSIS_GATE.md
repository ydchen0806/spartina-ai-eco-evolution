# Evidence gate for the Nature-track manuscript

This release separates what the recovered archive shows from the experiments
needed to support an eco-evolutionary claim. It is intended to keep the paper
moving while preventing a model-export artefact from becoming a biological
conclusion.

| Claim | Evidence currently available | Status | Required next test |
|---|---|---|---|
| Aerial AI can produce a spatially explicit patch record | 727 archived patch records and reproducible audit tables | Descriptive | Re-run segmentation with spatial and year holdouts; report patch-level uncertainty and area bias |
| RGB labels transfer across surveys and yield calibrated landscape area | Leave-one-survey-out RGB audit: mean balanced ROC-AUC 0.855, but mean absolute uniform-raster prevalence bias 28.51 percentage points | Calibration failure | Obtain independent expert labels, sample negatives explicitly and calibrate probabilities by acquisition condition |
| Newly recorded patches changed in parent-normalized area | 2014–2019 median log10 area ratio declines; 2020–2021 parent sizes are structurally constant and excluded | Exploratory | Recover parent IDs and GSD; fit a detection-aware lineage model with threshold sensitivity |
| Environment predicts growth outside the training records | Best leave-one-year-out R² = 0.178; best spatial-block R² = 0.394 | Limited predictive evidence | Recover the original climate extraction and validate at an independent estuary |
| Scenario workbooks identify a causal environmental mechanism | `growth_rate_pred` varies, but `growth_rate_simulation` is invariant across seven workbooks | Unresolved export definition | Recover the original model code and re-run each scenario from saved inputs |
| The phenotype shift is heritable adaptation | No common-garden, transplant, pedigree or genomic evidence in the archive | Unsupported | Common-garden or reciprocal-transplant experiment with early and late cohorts; estimate cohort × environment interaction and heritability |

## Primary estimands for the next experiment

1. Detection-corrected annual change in patch area and occupancy.
2. Cohort × environment interaction for growth, survival and reproductive output.
3. Out-of-site predictive performance of the environmental-response model.

The current record table uses pixels and putative parent links. Until ground
sampling supplies a pixel-to-area calibration and the parent matching table is
recovered, these quantities remain proxies.

## Analysis rules

- Treat annual records as cohorts, not generations.
- Treat record counts as detections, not population size.
- Keep 2020–2021 parent-size plateau rows in the raw audit but exclude them from
  parent-normalized trend estimates.
- Report temporal and spatial holdout scores beside any calibration statistic.
- Describe `growth_rate_pred` as a candidate counterfactual output until the
  export code is recovered; do not infer causality from scenario differences.
