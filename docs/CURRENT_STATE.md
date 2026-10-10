# Current state — Spartina invasion and eco-evolution project

Updated 2026-10-10. The active raw evidence now includes the recovered archive at
`/mnt/ydchen/micao_paper/raw_inputs/recovered_local_20261006/` as well as the legacy
patch matrices and environment–growth workbooks. Earlier statements that all
original imagery, masks and annotation polygons were missing are superseded.

## Latest advance: temporal AI transfer and prevalence calibration audit

See `RGB_MASK_TRANSFER_AUDIT_2026-10-10.md` and
`data/derived/rgb_mask_transfer_20261010/`. Fifteen paired RGB/mask surveys were
analysed with leave-one-survey-out Extra-Trees models using RGB and chromaticity
features. Balanced held-out label reproduction gave mean ROC-AUC 0.855, mean IoU
0.673 and mean F1 0.804. When the fixed threshold was applied to uniform
full-raster samples, archived positives averaged 0.32% but predictions averaged
28.83%, with 28.51 percentage points mean absolute prevalence bias. This is a
calibration and transfer failure, not an independent accuracy estimate: all
targets are historical masks and expert labels remain unavailable. Extended Data
Figure 11 and the 10 October working manuscript now make this failure mode an
explicit AI result.

The manuscript has 25 checked references, 15 figures and a 32-page working PDF.
The submission gate is recorded in `NATURE_SUBMISSION_GATE_2026-10-10.md`; independent expert labels, event adjudication, the endpoint exporter and mechanism-level replication remain open.
The recent PLOS ONE Spartina segmentation benchmark (DOI
10.1371/journal.pone.0358464) is included as a methodological comparator; its
site-held-out performance likewise motivates spatial and temporal validation.

## Latest advance: downloaded clonal common-garden data and robustness analysis

See `CLONAL_COMMON_GARDEN_REANALYSIS_2026-10-07.md`. Figshare dataset
10.6084/m9.figshare.33329481.v1 was downloaded using an existing proxy and verified
against the provider MD5. It contains 400 rows, eight source populations and three
gardens; ramet/emergence missingness is 56/62 rows. These are distinct from the
two still-unavailable Dryad datasets.

Source-balanced Zhanjiang minus Dongying differences are +5.05 ramets and -31.58
recorded days; crossed source/block bootstrap 95% intervals are [2.67, 7.47] and
[-48.70, -15.44]. Additive block sensitivity retains garden contrasts but changes
the Zhanjiang emergence–latitude slope from +1.992 to -0.043. Block semantics,
calendar origin, genotype/family identities and missingness causes are missing;
these results cannot establish temperature causation or local adaptation.

All 40,320 source permutations, multiplicity adjustment, 5,000 bootstrap draws,
missingness scenarios, block sensitivity and complete source-held-out predictions
are archived. Source-wise cross-validation improves unadjusted emergence means
with a simple latitude model; neither that model nor trees improve ramet counts
over garden means. Positive timing skill remains conditional on observation
composition. No expert pilot labels or local genetic evidence have been added.

The proxy restored HF access. The previous release (GitHub 2f5fb8e) was synced in
small batches and remote Git/LFS digests matched every tracked file. Later sync
status is recorded in `../briefing/HF_SYNC_LATEST.json` relative to this release.
No credentials or proxy addresses are embedded in the published scripts.

## Latest advance: external satellite analysis and mechanism-focused literature

See `EXTERNAL_EVIDENCE_2026-10-07.md` for completed analyses, literature scope and
falsifiable competing hypotheses. CCAV-10m V4 (DOI 10.57760/sciencedb.31077) was
downloaded: 3 files / 198,223,375 bytes, all provider MD5 checks passed, 8 annual
rasters for 2016–2023. The pre-existing vegetation workbook is byte-identical to
the official release. Its 106 local rows collapse to 99 coordinates, all labelled
mangrove; none is a local Spartina validation label, and sample splits are unknown.

Fixed 10 m grids cover the full image and historical ROI, with four grid phases.
ROI Spartina-class area is nonmonotonic: 97.62 ha (2016), 24.82 (2019), 71.64
(2022), 35.22 (2023). These are mapped classes, not error-adjusted biological
areas. Source grids differ and NoData is not habitat absence. Historical positive
masks have 20.1–65.0% same-year satellite Spartina-class agreement over 12 dates;
this cross-scale comparison is not accuracy. All 64 class partitions, 14 temporal
transition totals and 12 independent foreground totals pass conservation checks.

The manuscript now includes 8 figures and 11 references. Three new papers were
read in full; one Oikos study was checked through metadata/abstract and Dryad
methods. Two common-garden CC0 datasets were located, but all 7 public file
requests failed with HTTP 403; no raw-data reanalysis is claimed. The core question
now explicitly contrasts observation error, crowding/coalescence, community
change, environmental response and heritable source differences. Expert pilot
labels remain zero; local evolutionary mechanisms remain untested.

## Latest advance: strict baseline, frozen pilot and full working draft

The active full manuscript is `docs/MANUSCRIPT_WORKING_DRAFT.md`, with editable
DOCX and PDF in `manuscript/`. It reports completed analyses and explicitly
marks the missing independent validation; it is not submission-ready.

A fixed starting-geometry benchmark used 954 unique annual pairs, 661 dependency
groups, within-fold preprocessing, forward-year evaluation and buffered spatial
holdouts. For log area ratio, Extra Trees obtained forward R²=-1.116 (455
predictions) and spatial R²=0.086 (954 predictions). Ridge gave -0.941/0.051.
No claim of climate causation or independent-site transfer is supported.

A mask-independent pilot selected 32 sites across 16 spatial strata and all 15
dates: 480 native RGB crops in `../validation_pilot_20261007/` relative to the
release root. The browser annotation tool is ready and tested; **zero expert
labels are complete**. Spatially held-out strata and a training buffer are
frozen. Sampling metadata are in `data/derived/validation_pilot_20261007/`.

NASA POWER context now includes 2,922 daily records at the recovered image centre
(117.418563 E, 23.925454 N), with no missing values in four variables. It is
coarse gridded context, not tidal or local elevation measurement. Eight DOI
records were checked through Crossref metadata/available abstracts.

Small-n annual rank tests now also enumerate all 5,040 rank permutations:
stored endpoint P=0.088, same-record recomputed P=0.840, all-transition P=0.167.
Earlier P values below are the archived asymptotic approximations, not the
updated exact calculation. Exchangeability remains an assumption.

See `VALIDATION_AND_MANUSCRIPT_2026-10-07.md` for the full report and next
experiments. Needed inputs remain endpoint conversion code, independent image
labels/control points, independent-site data, and common-garden/transplant/genetic
evidence if evolutionary mechanisms remain the principal claim.

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
records were retrieved, and the China query still returned twelve. The earlier NASA
POWER point was east of the recovered imagery; it has been superseded by the
verified image-centre collection above. Literature discovery lists do not substitute for checked citations.

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
