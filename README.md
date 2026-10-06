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

Reproducible code, derived tables and audit figures for the *Spartina alterniflora* aerial-observation project. The release reconstructs the available 2014–2021 patch-record analysis and audits the recovered 2014–2020 environment–growth simulation archive.

## What is included

- `analysis/reanalyze_spartina.py` — one entry point for local data audit, external-context summaries, summary tables and figures.
- `analysis/model_holdout_audit.py` — independent leave-one-year-out and spatial-block predictive audit.
- `data/derived/` — derived tables and audit JSON generated from the local archive.
- `external_data/` — pinned NASA POWER and GBIF response files used for the exploratory context panel.
- `figures/` — vector and raster audit figures.
- `docs/` — evidence boundary, Nature-track narrative, captions, data dictionary and current state.

The UAV orthomosaics, segmentation masks, original weather/tide downloads, trained segmentation checkpoint and original simulation code are not present in this release. The recovered `raw_data.xlsx` and seven scenario workbooks are published in the [companion Hugging Face dataset](https://huggingface.co/datasets/cyd0806/spartina-ai-eco-evolution-data), with hashes and provenance in `metadata/data_sources.json`.

## Reproduce

```bash
python -m pip install -r requirements.txt
python analysis/reanalyze_spartina.py --no-download
python analysis/model_holdout_audit.py
```

The first command reproduces the patch-record and recovered-workbook audit from the files in this repository. The second command reproduces the held-out model audit. To refresh NASA POWER and GBIF context data, run `python analysis/reanalyze_spartina.py`; the script uses those sources only as labelled external context and they do not replace the original ERA5/UAV inputs.

## Scientific boundary

The recovered archive supports descriptive annual growth differences and a model calibration audit. It does not independently establish generations, heritability, genomic adaptation or environmental causality. The seven scenario workbooks contain different `growth_rate_pred` columns, while their `growth_rate_simulation` vectors are identical; the output definitions must be recovered before interpreting counterfactual mechanisms.

## License

Code is released under the MIT License. Data remain subject to the provenance and terms recorded in the companion dataset metadata and source-provider licenses.
