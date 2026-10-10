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

## Active manuscript and validation pilot

The full [working manuscript](docs/MANUSCRIPT_WORKING_DRAFT.md) is available as
[editable DOCX](manuscript/Spartina_working_draft_20261007.docx) and
[PDF](manuscript/Spartina_working_draft_20261007.pdf). It includes the completed
strict prediction baseline, sensitivity analyses and explicit evidence limits;
it is not a submission-ready claim of evolution.

The [external-evidence report](docs/EXTERNAL_EVIDENCE_2026-10-07.md) adds an
actual reanalysis of eight CCAV-10m annual vegetation maps, verified sample
provenance and a mechanism-focused review of common-garden and genetic studies.
[Satellite maps](data/derived/ccav_20261007/ccav_annual_site_maps.png),
[classified areas](data/derived/ccav_20261007/ccav_classified_area.png) and
[agreement across scales](data/derived/ccav_20261007/isolated_mask_ccav_agreement.png)
remain explicitly unvalidated locally. See [third-party attribution](THIRD_PARTY_DATA.md).

The [validation report](docs/VALIDATION_AND_MANUSCRIPT_2026-10-07.md) documents the
480-crop annotation pilot and frozen spatial splits. Crops and the annotation
page remain on the project server; this package contains sampling metadata,
generation code and the browser template. Expert labels remain uncompleted.

## External experimental reanalysis

The [new common-garden report](docs/CLONAL_COMMON_GARDEN_REANALYSIS_2026-10-07.md)
reanalyzes a verified public CSV with 400 records from eight source populations
and three gardens. It includes source-level exact permutation tests, crossed
bootstrap, missingness and block sensitivity, and whole-source predictive
holdouts. [Block sensitivity](data/derived/clonal_common_garden_20261007/clonal_block_sensitivity.png)
shows why a source–timing cline cannot yet be assigned an evolutionary mechanism.
The associated design metadata are incomplete; the two earlier Dryad raw-data
downloads remain unavailable. These statuses are explicitly distinguished.

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

## Endpoint and trajectory update

The [second-stage audit](docs/TRAJECTORY_ENDPOINT_AUDIT_2026-10-07.md) traces all
854 model records to annual transitions and identifies an unresolved growth
endpoint transformation affecting 2016 and 2018. It also reconstructs sample
selection, shared raster components and possible observation gaps. The
[61-case review gallery](figures/transition_review_20261007/index.html) provides
original RGB pairs, mask overlays and blank review forms. Download the folder
and open its HTML locally; GitHub's source viewer does not run the gallery.
These diagnostics precede biological event inference and new predictive claims.

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

### Xiamen literature and publication figures (7 October 2026)

See [the evidence and research update](docs/XMU_RESEARCH_REFINEMENT_2026-10-07.md).
Seven Xiamen-affiliated studies now anchor the distinctions among plasticity,
source-by-environment responses, self-thinning and genetic admixture.
The source register records affiliations, review scope and acquisition status.
A separate native-range genetic supplement supplies 935 stems and 223 inferred
lineages in ten field-defined patches; it does not validate local image objects.

```bash
# Rebuild unrestricted analyses and vector figure panels from archived sources.
python analysis/reanalyze_genet_ramet.py
python analysis/build_publication_figures.py
python analysis/build_working_manuscript.py --output manuscript/Spartina_working_draft_20261007.docx --pdf
# GCE raw files and these outputs are local-only pending reconciliation of terms.
python analysis/reanalyze_xmu_common_garden.py --source /path/to/gce_source --output /path/to/local_analysis
python analysis/verify_xmu_common_garden.py --source /path/to/gce_source --output /path/to/local_analysis
```

`download_genet_ramet.py` accepts an optional `MICAO_DOWNLOAD_PROXY` environment
variable. `download_xmu_common_garden.py` follows the original GCE registration
forms and requires user-supplied registration details; credentials and form
responses are not archived in this release. The manuscript remains a working
draft with independent validation incomplete. New core figures use 183 mm
width, editable vector text and separately saved source data. Review exports
place figures and their legends together.

### Additional external data (7 October 2026)

The [external-data expansion report](docs/EXTERNAL_DATA_EXPANSION_2026-10-07.md)
documents a complete 2.08 GB marsh imagery/competition archive, 24 years of GCE
plant monitoring with soil data, and published summaries from ten Chinese coastal
sites. It distinguishes source records, repeated measurements, geographic overlap
and independent validation. [GSM figure](data/derived/gsm_competition_20261007/gsm_external_evidence.png)
and [Chinese site context](data/derived/china_patch_traits_20261007/published_site_context.png)
have PDF/SVG counterparts and source tables. Three large original GSM rasters are
on [Hugging Face](https://huggingface.co/datasets/cyd0806/spartina-ai-eco-evolution-data/tree/main/external_sources/gsm_competition_20261007),
with verified hashes. GCE originals and new numerical analyses remain local
pending reconciliation of provider terms.

```bash
# All 19 GSM files: ~2.08 GB; optional MICAO_DOWNLOAD_PROXY for Figshare.
python analysis/download_mechanism_sources.py --dataset gsm --output /path/to/gsm_source
python analysis/reanalyze_gsm_competition.py --source /path/to/gsm_source --output data/derived/gsm_competition_20261007
# Published Chinese supplement and full Methods are already archived.
python analysis/audit_china_patch_sites.py --source external_data/china_patch_traits_20261007 --output data/derived/china_patch_traits_20261007
# GCE download uses GCE_REGISTRATION_NAME and GCE_REGISTRATION_EMAIL.
# Keep both directories outside the public release.
python analysis/download_mechanism_sources.py --dataset gce --output /path/to/local_gce_source
python analysis/audit_gce_longterm.py --source /path/to/local_gce_source --output /path/to/local_gce_analysis
```

The China source downloader (`--dataset china`) verifies archived SHA-256 values;
if the publisher changes its XML snapshot, use the reviewed copy here or review
and document the new version before updating the pinned hash.

### Local image footprint extended to September 2025

The [local spectral-extension report](docs/LOCAL_SPECTRAL_EXTENSION_2026-10-07.md)
describes a new experiment using 16 selected Sentinel-2 Collection 1 dates within
the actual UAV footprint. It includes fixed spatial support, cloud-buffer and
observation-count sensitivity, and all 2019×2025 acquisition-date pairs. The
[figure](data/derived/local_sentinel_c1_20261007/local_sentinel_extension.png) and
[RGB inspection sheet](data/derived/local_sentinel_c1_20261007/local_sentinel_rgb.png)
are accompanied by vector outputs and source tables. The working manuscript now
includes these results and Extended Data Figure 9. Missing September 2022 data
remain a gap, and spectral changes are not interpreted as species turnover or
evolution. Original Site10 UAV/trait data remain unavailable publicly.

Download and extract the [native-window archive](https://huggingface.co/datasets/cyd0806/spartina-ai-eco-evolution-data/resolve/main/external_sources/local_sentinel_c1_20261007/local_sentinel_c1_20261007.zip)
into an empty source directory, or acquire the sources with the first command:

```bash
python analysis/download_local_sentinel.py --source /path/to/local_sentinel_c1
python analysis/verify_local_sentinel_radiometry.py --source /path/to/local_sentinel_c1
python analysis/analyze_local_sentinel.py --source /path/to/local_sentinel_c1 --output data/derived/local_sentinel_c1_20261007
python analysis/build_working_manuscript.py --output manuscript/Spartina_working_draft_20261007.docx --pdf
```

The archived STAC responses pin the experiment; empty-source downloads query the
live catalogue, which can change as reprocessing continues. Use the archived ZIP
for exact acquisition replay. Contains modified Copernicus Sentinel data
[2019–2025]; see `THIRD_PARTY_DATA.md` for terms.

### Same-estuary 20 cm UAV originals recovered from a public data paper

The [new retrieval and analysis report](docs/ZHANGJIANG_UAV_RECOVERY_2026-10-07.md)
documents ten orthomosaics and ten distribution maps from 2013–2022, **1.84 GB**,
all provider-MD5 verified. All map rectangles lie within our full UAV footprint.
The December 2021 and June 2022 products add acquisition months absent from the
original 15-date archive. Earlier same-month images are near-identical to recovered
imagery and are not treated as independent replication. The
[new figure](data/derived/zhangjiang_uav_20261007/zhangjiang_uav_extension.png)
and updated working manuscript distinguish landscape-positive labels from
isolated objects, biological events and source independence.

Originals are on [HF](https://huggingface.co/datasets/cyd0806/spartina-ai-eco-evolution-data/tree/main/external_sources/zhangjiang_uav_20261007),
under **CC-BY-NC-SA-4.0**, also retained by our adaptations. These are Huang et al.'s
ScienceDB V4 data, not the still-unobtained raw 2025 Site10 material. Source zeros
are NoData/unlabelled, not verified species absence.

```bash
python analysis/download_zhangjiang_uav.py --output /path/to/zhangjiang_uav
python analysis/analyze_zhangjiang_uav.py --source /path/to/zhangjiang_uav --output data/derived/zhangjiang_uav_20261007
```


### Cross-survey AI transfer audit

The RGB-to-mask temporal audit holds out each of 15 paired surveys in turn. It reproduces archived labels on balanced pixels (mean ROC-AUC 0.855), but overpredicts full-raster archived-positive prevalence by 28.51 percentage points on uniform samples. This is a calibration warning, not an independent segmentation accuracy estimate. See [audit report](docs/RGB_MASK_TRANSFER_AUDIT_2026-10-10.md) and the relevant external Spartina benchmark metadata (`external_data/xmu_literature_20261007/crossref_pone_0358464.json`) and [results](data/derived/rgb_mask_transfer_20261010/temporal_transfer_metrics.csv).
