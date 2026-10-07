# Local Sentinel-2 Collection 1 windows

Contains modified Copernicus Sentinel data (2019–2025). The source is Sentinel-2
Collection 1 Level-2A via Element84 Earth Search, with rights governed by the
Copernicus Sentinel Data Legal Notice. See the notice and full attribution in
`external_data/local_sentinel_c1_20261007/` and `THIRD_PARTY_DATA.md` at release root.

`local_sentinel_c1_20261007.zip` is stored here in the Hugging Face dataset only.
It contains 335 files, including 154 original-DN native-grid spatial subsets,
74 candidate SCL screens, 16 selected-date metadata records, product XML, complete
catalogue responses and acquisition provenance. Five spectral bands were acquired
for each selected date. No full Sentinel tile or Site10 UAV image is included.

ZIP bytes: 8,783,659
SHA-256: a08f8d42be6ace11bb72eb54ff0095801f6fb4cc9720c5b744fa7b1dfae39b88

Extract to an empty directory and pass it as `--source` to
`analysis/analyze_local_sentinel.py`. The source ZIP preserves the experiment's
catalogue queries; fresh API queries may differ as provider processing changes.
Provider XML digests were verified. For pixel assets, source HTTP ranges and
ETags were verified and subset digests recorded; full-source-file hashes were
not verified. The HF ZIP LFS SHA-256 matches the local archive.
