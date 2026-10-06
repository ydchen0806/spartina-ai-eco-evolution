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

## What remains missing

The upstream matrices reference 15 image dates and paths such as
`./mask/201408ddyw.tif` and `./mask/20180729.tif`. The notebooks also reference
JPEGs under `E:\remote_data\numvis\`, including
`201408ddyw(1).jpg`. Neither the TIFF/JPEG pixels nor the original segmentation
masks were present in the upstream Git history or the local workspace scan.
The upstream repository contains AutoGluon predictor artefacts, but no UAV
segmentation checkpoint, annotation polygons or training/validation split.

The image-index inventory therefore supports an auditable observation timeline,
while the original AI segmentation metrics cannot yet be independently
recomputed. The next recovery request should target the `remote_data/numvis`
directory, the `mask` directory, annotation files and the segmentation training
repository/checkpoint. Until those arrive, the paper should report the
segmentation layer as archived provenance and keep detection uncertainty in the
main evidence boundary.

## Relevance to the scenario audit

The recovered upstream code explains the calibration workflow: `auto_ml_fit.py`
fits and evaluates predictions on the same training table by default, while the
random split is an optional helper. This is why the current release reports the
old high fit as calibration and adds independent year-held-out and spatial-block
audits. The upstream source does not contain the exporter that created the
seven `growth_rate_pred`/`growth_rate_simulation` scenario columns, so their
mechanistic interpretation remains unresolved.
