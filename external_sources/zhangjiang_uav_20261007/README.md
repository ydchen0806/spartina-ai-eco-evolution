# Zhangjiang Estuary UAV archive, V4

Minmin Huang, Yihui Zhang, Zeyou Zhou and Xudong Zhu (2023), *A dataset of the
UAV remote sensing spatial distribution of Spartina alterniflora in the
Zhangjiang Estuary of Fujian Province from 2013 to 2022*. Science Data Bank V4.
DOI: https://doi.org/10.57760/sciencedb.o00119.00069
Paper: https://doi.org/10.11922/11-6035.csd.2023.0011.zh

**CC-BY-NC-SA-4.0**: https://creativecommons.org/licenses/by-nc-sa/4.0/
Retain attribution, noncommercial and share-alike terms for original/adapted
source material. The code repository's MIT licence does not cover these data.
No endorsement by the source authors is implied.

All 20 original TIFF files are stored in this directory's `DOM/` and `classified/`
subdirectories on the companion Hugging Face dataset; large originals are excluded
from Git. Ten orthomosaics and ten distribution maps, 20 cm, 2013–2022, total
1,844,072,803 bytes. Provider MD5 was verified for every file; `source_manifest.json`
records local SHA-256. Uploaded HF LFS SHA-256 values also match.

Data are spatially overlapping with our UAV footprint. Old same-month imagery
must not be assumed independent of the recovered archive. The December 2021 and
June 2022 RTK-named products add acquisition months absent from the recovered
15-date sequence. A filename does not verify physical registration accuracy.
Class maps use 1 for mapped foreground and 0 tagged as NoData: zero is not a
verified absence, and positive-label transitions are not mortality/recruitment.

The source metadata, reproducible downloader and reanalysis are in
`external_data/zhangjiang_uav_20261007/`, `analysis/download_zhangjiang_uav.py`
and `analysis/analyze_zhangjiang_uav.py`. Our adapted results, including figures,
retain CC-BY-NC-SA-4.0 with this source attribution.
