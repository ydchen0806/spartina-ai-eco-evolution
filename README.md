# Spartina AI eco-evolutionary reanalysis

Reproducible code, derived tables and audit figures for the *Spartina alterniflora* aerial-observation project. The release reconstructs the available 2014–2021 patch-record analysis and audits the recovered 2014–2020 environment–growth simulation archive.

## What is included

- `analysis/reanalyze_spartina.py` — one entry point for local data audit, external-context downloads, summary tables and figures.
- `data/derived/` — derived tables and audit JSON generated from the local archive.
- `figures/` — vector and raster audit figures.
- `docs/` — evidence boundary, Nature-track narrative, captions and current state.

The UAV orthomosaics, segmentation masks, original weather/tide downloads, trained segmentation checkpoint and original simulation code are not present in this release. The recovered `raw_data.xlsx` and seven scenario workbooks are published in the companion Hugging Face dataset; see `metadata/data_sources.json` after the dataset release is created.

## Reproduce

```bash
python -m pip install -r requirements.txt
python analysis/reanalyze_spartina.py --no-download
```

To refresh NASA POWER and GBIF context data, run without `--no-download`. The script uses those sources only as labelled external context; they do not replace the original ERA5/UAV inputs.

## Scientific boundary

The recovered archive supports descriptive annual growth differences and a model calibration audit. It does not independently establish generations, heritability, genomic adaptation or environmental causality. The seven scenario workbooks contain different `growth_rate_pred` columns, while their `growth_rate_simulation` vectors are identical; the output definitions must be recovered before interpreting counterfactual mechanisms.

## License

Code is released under the MIT License. Data remain subject to the provenance and terms recorded in the companion dataset metadata and source-provider licenses.
