# GSM original raster archive

Original data by Yuyang Wang, Ivan Valiela and Kelsey Chenoweth, Figshare v1,
https://doi.org/10.6084/m9.figshare.30068944.v1, **CC-BY-4.0**.
Associated article: https://doi.org/10.1016/j.envc.2026.101453.

The following unmodified original rasters are stored alongside this README in
the Hugging Face dataset, and are excluded from the Git code repository:

- `GSM_20230811.tif`: original four-band NAIP imagery, 0.3 m, 2,017,587,198 bytes.
- `GSM_boundary_2023_clipped.tif`: source image subset, 55,874,872 bytes.
- `GSM_2023_RF_classified_AOI2015_minus_forest.tif`: published classified map, 10,996,209 bytes.

Provider MD5 checks and local SHA-256 hashes are in `source_manifest.json`.
HF LFS SHA-256 values were verified after upload. The other 16 source files and
provider metadata are in `external_data/gsm_competition_20261007/` at repository
root. Derived audits and plots are in `data/derived/gsm_competition_20261007/`.

Retain the original author attribution and CC-BY-4.0 licence. Our transformations
and conclusions are not endorsed by the data creators. Source reference labels
are interpretations of imagery; community classes are not species masks.
Training shapefile attributes and CRS sidecars are absent from the source release.
