# Current state — Spartina Nature-track project

**Date:** 2026-10-06  
**Working root:** `nature_manuscript/public_release`  
**Active evidence:** the recovered patch CSV and simulation workbooks in `data/source/`.

## Completed this turn

Ran from the release root:

```bash
python analysis/reanalyze_spartina.py --no-download
python -m py_compile analysis/reanalyze_spartina.py analysis/model_holdout_audit.py
python analysis/model_holdout_audit.py
python analysis/collect_external_context.py --no-download
python analysis/audit_original_pipeline.py
```

The script audited 727 local patch records using the pinned NASA POWER daily climate context for 117.60 E, 23.95 N (2014–2021) and the 12 coordinate-bearing GBIF records returned by the query `scientificName=Spartina alterniflora&country=CN`, then generated annual summaries and rendered PDF/PNG candidates.

The same scan also recovered `external_data/legacy_simulation_archive/230214simulation/raw_data.xlsx` from the historical simulation ZIP. It contains 854 environmental-growth records from 2014–2020, including the observed and simulated growth-rate columns. The archive's seven scenario workbooks have different `pca*_simulation` inputs and different `growth_rate_pred` columns, but byte-identical `growth_rate_simulation` vectors. The definition and export path of those two outputs must be recovered before using the old counterfactual figures as mechanism evidence.

The recovered archive gives observed-versus-exported simulation RMSE 0.699 and Pearson *r* 0.905. Annual observed growth means decrease from 2.303 (2014) to 1.504 (2020), but the year-level rank trend is descriptive (Spearman ρ = −0.714, n = 7, P = 0.071). Candidate `growth_rate_pred` scenario means range from 1.961 (pressure) to 2.157 (all features).

An independent model audit using leave-one-year-out and spatial-block holdout found best R² = 0.178 (RMSE 1.383) for temporal extrapolation and R² = 0.394 (RMSE 1.187) for spatial extrapolation. The in-sample/export calibration value must therefore be labelled calibration, not generalisation.

## Current artifacts

- `analysis/reanalyze_spartina.py`: reproducible audit, download, summary and plotting entry point.
- `tables/reanalysis_audit.json`: counts, trend statistics and structural anomaly flags.
- `tables/patch_records_audited.csv`: local records with derived ratios and audit flags.
- `tables/patch_year_summary.csv`: annual descriptive summary.
- `tables/nasa_power_year_month_summary.csv`: downloaded climate context aggregated by year and month.
- `tables/gbif_spartina_china.csv`: external occurrence context.
- `figures/generated_candidates/fig_patch_dynamics_audit.pdf`: four-panel audit figure.
- `figures/generated_candidates/fig_gbif_external_context.pdf`: GBIF context map.
- `figures/generated_candidates/fig_recovered_simulation_audit.pdf`: recovered 854-row archive, calibration and scenario-export audit.
- `tables/recovered_raw_growth_environment.csv`: recovered 854-row environment-growth table.
- `tables/recovered_growth_year_summary.csv`: annual observed/simulated growth summary.
- `tables/recovered_scenario_export_audit.csv`: scenario workbook comparison.
- `tables/model_holdout_summary.csv`: independent held-out model comparison.
- `tables/model_holdout_predictions.csv`: held-out predictions.
- `tables/model_holdout_audit.json`: holdout audit metadata.
- `analysis/model_holdout_audit.py`: time/spatial holdout model audit.
- `analysis/collect_external_context.py`: accepted-name GBIF context and OpenAlex literature screen.
- `tables/gbif_spartina_global_country_summary.csv`: country facets for 4,584 georeferenced GBIF records.
- `tables/external_literature_screen.csv`: 75-work reproducible literature discovery list.
- `figures/fig_external_context_synthesis.pdf`: external occurrence and literature-context plot.
- `docs/EXTERNAL_CONTEXT.md`: source definitions and interpretation limits.
- `analysis/audit_original_pipeline.py`: upstream source-link and image-index audit.
- `tables/original_pipeline_audit.json`: exact 854-row upstream/recovered key match and missing-pixel boundary.
- `tables/original_pipeline_image_inventory.csv`: 15 referenced UAV image dates and non-missing row counts.
- `figures/fig_original_pipeline_inventory.pdf`: recovered image-index timeline.
- `docs/ORIGINAL_PIPELINE_RECOVERY.md`: upstream commit, code path and missing image/checkpoint inventory.
- `docs/LITERATURE_SYNTHESIS.md`: literature anchors for the revised Introduction and Discussion.

The upstream public repository `ydchen0806/ai4FastEvolution` was recovered at
commit `171c9f5`. Its 3,237-row image-index matrices, 15 referenced image dates,
station weather table and NetCDF weather subsets are now included under
`data/source/original_pipeline/`. The upstream 854-row `mydata_0224.xlsx` has an
exact multiset match with the recovered environment-growth archive on
`(year, size, X, Y, growth_rate)`. The actual TIFF/JPEG pixels, segmentation
masks and segmentation checkpoint are still absent; the missing paths and
recovery request are documented in `docs/ORIGINAL_PIPELINE_RECOVERY.md`.
- `docs/ANALYSIS_GATE.md`: evidence boundary, estimands and next falsifiable experiment.
- `docs/RESULTS_DRAFT.md`: evidence-calibrated Results and Discussion wording.
- `docs/PROJECT_AUDIT_2026-10-06.md`: evidence boundary, Nature-level narrative and experiment plan.
- `docs/REVISED_ABSTRACT_AND_OUTLINE.md`: calibrated title, abstract and Results order.

## Outstanding blockers

The repository still does not contain the UAV orthomosaics/masks, source climate and tide downloads, segmentation checkpoints, matching tables or training logs described by the manuscript. The recovered environment-growth table supports a descriptive 2014–2020 growth series and a calibration audit, but it cannot independently establish generations, heritability, genomic adaptation or environmental causality. The 2020 and 2021 parent-size plateau is flagged and excluded from parent-normalized trend estimates; the scenario-output definitions must be resolved before using those counterfactuals.

The release is now self-contained for the current audit: pinned NASA POWER and
GBIF response files are in `external_data/`, `metadata/data_dictionary.csv`
defines all recovered fields, and `docs/ANALYSIS_GATE.md` records the claim
boundary and the next falsifiable experiment.

The next scientific gate is recovery of the P0 raw evidence chain, followed by spatial/year holdout validation and a detection-error-aware hierarchical model. Common-garden or reciprocal-transplant data are required before using “heritable adaptation” as a main-text conclusion.
