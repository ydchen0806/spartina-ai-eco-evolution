---
license: mit
task_categories:
  - tabular-regression
  - image-segmentation
tags:
  - biological-invasion
  - evolutionary-ecology
  - remote-sensing
  - reproducibility
---

# Spartina AI eco-evolutionary reanalysis

Code repository: [github.com/ydchen0806/spartina-ai-eco-evolution](https://github.com/ydchen0806/spartina-ai-eco-evolution)

Reproducible code, derived tables and audit figures for the *Spartina alterniflora* aerial-observation project. The release reconstructs the available 2014–2021 patch-record analysis and audits the recovered 2014–2020 environment–growth simulation archive.

## What is included

- `analysis/reanalyze_spartina.py` — one entry point for local data audit, external-context summaries, summary tables and figures.
- `analysis/model_holdout_audit.py` — independent leave-one-year-out and spatial-block predictive audit.
- `analysis/collect_external_context.py` — pinned GBIF accepted-name context and OpenAlex literature screen.
- `analysis/audit_original_pipeline.py` — verifies the upstream public pipeline and inventories the referenced image dates.
- `data/derived/` — derived tables and audit JSON generated from the local archive.
- `data/source/original_pipeline/` — raw patch-size/position matrices, station weather table, recovered NetCDF weather subsets and the upstream 854-row workbook.
- `legacy/original_code/` — source snapshots from the upstream `ai4FastEvolution` repository, preserved for provenance.
- `external_data/` — pinned NASA POWER and GBIF response files used for the exploratory context panel.
- `figures/` — vector and raster audit figures.
- `docs/` — evidence boundary, Nature-track narrative, captions, data dictionary and current state.
- `docs/LITERATURE_SYNTHESIS.md` — checked literature anchors and their implications for the claim hierarchy.

**Recovery update, 2026-10-07:** the server now holds 15 full RGB/mask pairs and annotation deliveries for 714 images (9,234 objects). Independent rehashing verified all 1,001 restored files. A fixed crop convention links 5,745 of 5,746 archived patch-date coordinates to the recovered masks; a candidate bounding-box counting rule reproduces 5,744 archived areas. See [the recovery validation and research plan](docs/RECOVERY_VALIDATION_2026-10-07.md) for the audit, figures, reproducible commands and remaining limits.

The 38.65 GB raw recovery is separate from this public package. The original segmentation checkpoint, original training RGB photographs, fixed split and scenario-export implementation remain unrecovered. Derived recovery audits are in `data/derived/recovery_20261007/`; inspection figures are in `figures/recovery_20261007/`. The earlier workbooks remain in the [companion Hugging Face dataset](https://huggingface.co/datasets/cyd0806/spartina-ai-eco-evolution-data).

## Reproduce

```bash
python -m pip install -r requirements.txt
python analysis/reanalyze_spartina.py --no-download
python analysis/model_holdout_audit.py
python analysis/collect_external_context.py --no-download
python analysis/audit_original_pipeline.py
```

The first command reproduces the patch-record and recovered-workbook audit from the files in this repository. The second command reproduces the held-out model audit. The third command reproduces the accepted-name GBIF country facets and the OpenAlex literature screen. To refresh NASA POWER and GBIF context data, run `python analysis/reanalyze_spartina.py`; the scripts use external sources only as labelled context and they do not replace the original ERA5/UAV inputs.

## Scientific boundary

The recovered archive supports descriptive annual growth differences and a model calibration audit. It does not independently establish generations, heritability, genomic adaptation or environmental causality. The seven scenario workbooks contain different `growth_rate_pred` columns, while their `growth_rate_simulation` vectors are identical; the output definitions must be recovered before interpreting counterfactual mechanisms.

## License

Code is released under the MIT License. Data remain subject to the provenance and terms recorded in the companion dataset metadata and source-provider licenses.
