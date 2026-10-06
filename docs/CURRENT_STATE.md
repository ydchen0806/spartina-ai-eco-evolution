# Current state — Spartina invasion and eco-evolution project

Updated 2026-10-07. The active raw evidence now includes the recovered archive at
`/mnt/ydchen/micao_paper/raw_inputs/recovered_local_20261006/` as well as the legacy
patch matrices and environment–growth workbooks. Earlier statements that all
original imagery, masks and annotation polygons were missing are superseded.

## Latest advance: endpoint and trajectory audit

See `TRAJECTORY_ENDPOINT_AUDIT_2026-10-07.md` for the full new report. All 854
model records link to annual matrix transitions, preserving repeated-key counts.
The selected set exactly matches 0 < relative area increment < 10 among 957
transitions (50 nonpositive and 53 extreme positive transitions excluded).
All 138 records starting in 2016 and 50 starting in 2018 have stored growth_rate
values inconsistent with area-derived relative gain; the transformation remains
unresolved. For the same 854 records, the annual rank correlation changes from
-0.714 to -0.107 after recomputing this endpoint. These are sensitivity checks,
not validated replacement biological results.

Eight-connected component reconstruction also found 167 archive observations
sharing 80 component-date objects (87 excess rows). The unregistered transition
screen flagged 80 possible coverage gaps, and a 61-case diagnostic RGB review
pack is available at `figures/transition_review_20261007/index.html` in the release.
Expert review forms are blank. Automatic feature registration did not meet the
descriptive spatial-holdout quality gate, so no correction was applied. Raw
mask overlaps are review candidates, not demographic events.

The next modelling gate is to resolve the endpoint transformation, observation
coverage, registration and non-independent tracks. Previous temporal-trend and
AI calibration summaries below are archived results whose scientific
interpretation is now additionally limited by these findings.

## Verified recovery

- Independently rehashed 1,001 files / 38,654,767,408 bytes: zero failures.
- Restored 15 full RGB / binary-mask pairs, each 26,606 × 24,443, plus additional imagery.
- Confirmed equivalent polygon deliveries: 714 images and 9,234 objects.
- Fixed crop coordinates reproduce 5,745 / 5,746 archived patch-date positions.
- Exclusive-maximum bounding-box counting reproduces 5,744 archived areas. This is a numerical reconstruction of the old extraction convention, not a corrected biological area estimate. Two anomalous records remain flagged.

See `RECOVERY_VALIDATION_2026-10-07.md` for the full report, manuscript draft
paragraphs, figure captions and ordered experiment plan. In the public release,
the report is under `docs/`, derived tables under `data/derived/recovery_20261007/`
and figures under `figures/recovery_20261007/`. The raw 38.65 GB archive remains
outside that package. Local changes are not evidence of a completed online sync.

## Scientific interpretation

Masks primarily describe isolated patches and do not cover all continuous
vegetation. Mask area decline cannot be treated as declining total invasion area
or genetic adaptation. Observation coverage, season/tide, patch coalescence and
sample selection must be resolved before revising biological conclusions.

The earlier 854-row audit remains informative: annual mean growth was 2.303 in
2014 and 1.504 in 2020; the seven-year rank trend was descriptive (rho = -0.714,
P = 0.071). The old r = 0.905 / RMSE = 0.699 is calibration. Exploratory temporal
and spatial holdouts gave best R² = 0.178 and 0.394; global imputation / existing
PCA inputs mean these are not the final leakage-controlled evaluation.
Seven scenario workbooks still have identical `growth_rate_simulation` despite
varying `growth_rate_pred`; their exporter and output definitions are unresolved.
The separate 727-row parent table has flagged constant parent areas in 2020/2021.

The external-context collection is preliminary. The GBIF value 4,584 is a
reported query total, not a cleaned downloaded dataset; only ten global example
records were retrieved, and the China query still returned twelve. The NASA
POWER point is east of the recovered imagery and is context pending spatial
verification. Literature discovery lists do not substitute for checked citations.

## Next scientific gate

1. Validate cross-date registration and common valid observation footprint.
2. Rebuild component areas and centroids; audit trajectory continuity, splitting,
   merging and censoring with independent RGB review.
3. Freeze a spatially independent annotation sample, including areas outside old
   positive masks, to measure detection and area error.
4. Compare environmental / density / coalescence explanations with preprocessing
   inside training folds and complete year / spatial holdouts.
5. Add tide and satellite context targeted at those hypotheses. Heritable
   adaptation requires independent common-garden / transplant / genetic evidence.

Original segmentation checkpoint, training RGB photographs and fixed split are
still unrecovered. This does not block new validation using the recovered
orthomosaics. Original inputs and archived tables have not been overwritten.

Public code: https://github.com/ydchen0806/spartina-ai-eco-evolution

Public data: https://huggingface.co/datasets/cyd0806/spartina-ai-eco-evolution-data
