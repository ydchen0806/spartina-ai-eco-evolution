# RGB-to-mask temporal transfer audit (10 October 2026)

## Question

Can the archived RGB appearance–mask relationship be transported to a survey
that was not used for fitting? This is an AI reliability test. It is not an
independent segmentation-accuracy estimate because every target label is an
archived mask and no expert pixel labels are available.

## Design

Fifteen paired RGB orthomosaics and masks from 2014–2021 were used. For each
held-out survey, an Extra-Trees classifier was fitted to the other 14 surveys
using RGB, chromaticity and excess-green features. The training and balanced
test sets contained up to 3,000 archived-positive and 3,000 archived-zero
pixels per survey. The held-out survey was also sampled uniformly over its
full raster (4,000 pixels) to assess prevalence calibration under the actual
class imbalance. Coordinates were excluded from the features.

## Results

Across leave-one-survey-out folds, balanced-sample mean ROC-AUC was **0.855**,
mean IoU **0.673** and mean F1 **0.804**. These values describe reproduction of
the stored labels under balanced sampling. On the uniform full-raster samples,
the archived-positive prevalence averaged **0.32%**, whereas the fixed 0.5
classifier threshold predicted **28.83%**; the mean absolute prevalence bias was
**28.51 percentage points**. The weakest discrimination occurred for
2015-10-17 (ROC-AUC 0.580), while the strongest was 2015-08 ddyw (0.936).

The divergence between balanced discrimination and full-raster prevalence is a
direct calibration warning: a model can separate selected positive pixels from
selected zeros while producing a severely inflated landscape-positive area when
the archived positive class is sparse and acquisition conditions change.

## Reproducibility and interpretation

Run:

```bash
python analysis/audit_rgb_mask_transfer.py \
  --imagery /path/to/recovered_local_20261006/imagery_georeferenced \
  --masks /path/to/recovered_local_20261006/mask \
  --output data/derived/rgb_mask_transfer_20261010
```

The metrics, predictions, audit JSON and figure are in
`data/derived/rgb_mask_transfer_20261010/`. The result does not recover the
original segmentation model, establish pixel-level truth, or correct the
historical masks. It supports a narrower conclusion: temporal transfer and
prevalence calibration must be evaluated separately before AI-derived mask area
is used as an invasion census.
