# Original pipeline recovery

The upstream code and derived inputs were recovered from the public repository
[`ydchen0806/ai4FastEvolution`](https://github.com/ydchen0806/ai4FastEvolution) at
commit `171c9f516799b8bc90aa98b9274730ead7ae740e`. Its README describes the
same project title and the sequence used in the old manuscript:

1. derive patch-size and position tables from image masks;
2. attach weather data and interpolate gridded climate variables;
3. compute distances and PCA scores;
4. fit AutoGluon growth-rate models;
5. fit MGWR and cluster local environmental responses.

The current release preserves the key upstream scripts in
`legacy/original_code/`, the source tables and the recovered NetCDF weather
subsets in `data/source/original_pipeline/`. Running
`python analysis/audit_original_pipeline.py` verifies that the upstream
`mydata_0224.xlsx` and the recovered 854-row `raw_data.xlsx` have an exact
multiset match on `(year, size, X, Y, growth_rate)`. This establishes that the
854-row archive is a direct product of the upstream pipeline rather than an
unrelated reconstruction.

## Recovery status — updated 2026-10-07

The initial inspection covered a shallow clone of the upstream snapshot and the
then-available workspace, not every historical Git revision. A separate local
recovery has now restored the 15 full image/mask pairs, the historical `numvis`
folder and polygon annotation deliveries for 714 images. Their independent
checksum, raster, annotation and coordinate audits are recorded in
[RECOVERY_VALIDATION_2026-10-07.md](RECOVERY_VALIDATION_2026-10-07.md).

The raw archive is stored separately from this release. The original UAV
segmentation checkpoint, original training RGB photographs and fixed training /
validation / test split remain unrecovered, so the original model performance
cannot yet be independently reproduced. The recovered orthomosaics can support
new independent annotation and validation. The upstream repository's AutoGluon
predictor artifacts are growth-model artifacts, not the missing segmenter.

## Relevance to the scenario audit

The recovered upstream code explains the calibration workflow: `auto_ml_fit.py`
fits and evaluates predictions on the same training table by default, while the
random split is an optional helper. This is why the current release reports the
old high fit as calibration and adds independent year-held-out and spatial-block
audits. The upstream source does not contain the exporter that created the
seven `growth_rate_pred`/`growth_rate_simulation` scenario columns, so their
mechanistic interpretation remains unresolved.
