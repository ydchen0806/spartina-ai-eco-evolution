# Current state — Spartina Nature-track project

**Date:** 2026-10-06  
**Working root:** `/mnt/ydchen/micao_paper`  
**Active evidence:** `230521paper/240102/paper/Chen et al 0419.docx` plus the local patch CSVs.

## Completed this turn

Ran:

```bash
python nature_manuscript/analysis/reanalyze_spartina.py
python -m py_compile nature_manuscript/analysis/reanalyze_spartina.py
```

The script audited 727 local patch records, downloaded NASA POWER daily climate context for 117.60 E, 23.95 N (2014–2021), downloaded the 12 coordinate-bearing GBIF records returned by the query `scientificName=Spartina alterniflora&country=CN`, generated annual summaries and rendered PDF/PNG candidates.

The same scan also recovered `external_data/legacy_simulation_archive/230214simulation/raw_data.xlsx` from the historical simulation ZIP. It contains 854 environmental-growth records from 2014–2020, including the observed and simulated growth-rate columns. The archive's seven scenario workbooks have different `pca*_simulation` inputs and different `growth_rate_pred` columns, but byte-identical `growth_rate_simulation` vectors. The definition and export path of those two outputs must be recovered before using the old counterfactual figures as mechanism evidence.

The recovered archive gives observed-versus-exported simulation RMSE 0.699 and Pearson *r* 0.905. Annual observed growth means decrease from 2.303 (2014) to 1.504 (2020), but the year-level rank trend is descriptive (Spearman ρ = −0.714, n = 7, P = 0.071). Candidate `growth_rate_pred` scenario means range from 1.961 (pressure) to 2.157 (all features).

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
- `briefing/PROJECT_AUDIT_2026-10-06.md`: evidence boundary, Nature-level narrative and experiment plan.
- `briefing/REVISED_ABSTRACT_AND_OUTLINE.md`: calibrated title, abstract and Results order.

## Outstanding blockers

The repository still does not contain the UAV orthomosaics/masks, source climate and tide downloads, segmentation checkpoints, matching tables or training logs described by the manuscript. The recovered environment-growth table supports a descriptive 2014–2020 growth series and a calibration audit, but it cannot independently establish generations, heritability, genomic adaptation or environmental causality. The 2020 and 2021 parent-size plateau is flagged and excluded from parent-normalized trend estimates; the scenario-output definitions must be resolved before using those counterfactuals.

The next scientific gate is recovery of the P0 raw evidence chain, followed by spatial/year holdout validation and a detection-error-aware hierarchical model. Common-garden or reciprocal-transplant data are required before using “heritable adaptation” as a main-text conclusion.
