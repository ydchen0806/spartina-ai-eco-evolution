# Third-party data and attribution

The repository's MIT licence applies to original analysis code. It does not
replace the terms of third-party data, article texts or upstream source code.

CCAV-10m V4: Yuying Li, Ting Liu, Lina Yuan, Zijiang Song, Shuang Yang, Zilong Zhu
and Min Liu (2026), Science Data Bank, https://doi.org/10.57760/sciencedb.31077.
Licence: **CC-BY-4.0**, https://creativecommons.org/licenses/by/4.0/.
Associated paper: https://doi.org/10.5194/essd-18-2907-2026.

`external_data/ccav_20261007/` contains the unchanged official sample workbook,
class key and provenance. The national ZIP and extracted national rasters remain
local and are excluded from Git. `data/derived/ccav_20261007/` contains our
transformed/adapted outputs: coordinate deduplication, local clipping, nearest
neighbour reprojection, class statistics, plots and comparisons with our historical
masks. Retain the above attribution and CC-BY-4.0 terms for CCAV-derived content.
Our analyses and conclusions are not endorsed by the source authors.

Dryad records 10.5061/dryad.2rbnzs7q7 and 10.5061/dryad.j3tx95xsc declare CC0.
Only metadata and download-failure manifests are currently present. No raw
files or reanalysis results from those two Dryad datasets are claimed.

Retrieved scholarly XML/texts and metadata in `external_evidence_20261007/`
retain the authorship and publisher licensing stated in those sources. Citations
and review scope are recorded in the manuscript and literature evidence register.
Full HTML discovery caches are excluded from the public release.

Clonal common-garden data: Xincong Chen (2026), *clonal traits data of the invasive
Spartina alterniflora in China*, Figshare version 1,
https://doi.org/10.6084/m9.figshare.33329481.v1. Licence: **CC-BY-4.0**.
The unchanged original CSV and version metadata are in
`external_data/clonal_common_garden_20261007/`. Derived tables, statistical
reanalyses and figures in `data/derived/clonal_common_garden_20261007/` are our
adaptations of that source; retain this attribution and licence. The source
author has not endorsed our analyses or interpretation. No linked journal article
was identified in the dataset metadata, and this release does not claim one.

Genet/ramet supplemental data: Jewel Tomasula, Seamus Caslin, Gina M. Wimp and
Matthew B. Hamilton (2026), *Mating portfolio and neutral mechanisms are primary
causes of genet-ramet frequencies and spatial distributions in smooth cordgrass
(Spartina alterniflora) along salt marsh tidal gradients*, Frontiers in Genetics
17, 1810782. Article https://doi.org/10.3389/fgene.2026.1810782; supplement
https://doi.org/10.3389/fgene.2026.1810782.s002; Figshare article 32141245 v1,
file 64150624. Licence **CC-BY-4.0**. The original ZIP and metadata are in
`external_data/xmu_literature_20261007/genet_ramet/`; our derived tables and
figure in `data/derived/genet_ramet_20261007/` retain this attribution and licence.
We reused the supplied lineage assignments and did not re-estimate genetic
clusters. The source authors have not endorsed this reanalysis.

GCE-LTER BOT-GCED-1912, Steven C. Pennings and collaborators (2019), associated
with Liu et al., New Phytologist (2020), https://doi.org/10.1111/nph.16371:
only descriptive metadata and our general analysis scripts are released here.
Raw CSVs and newly computed numerical results remain outside this release.
Dataset-specific EML states CC-BY-4.0; the legacy GCE download agreement adds
redistribution restrictions and a notification requirement. Public redistribution
is deferred until this discrepancy is resolved. No messages to authors were sent.
Source metadata and contributor names remain attached. EDI metadata discovery
and GCE original-file downloads are distinguished; no byte equivalence between
repository revisions has been established.

GSM competition and remote-sensing archive: Yuyang Wang, Ivan Valiela and
Kelsey Chenoweth, Figshare v1, https://doi.org/10.6084/m9.figshare.30068944.v1.
Dataset licence **CC-BY-4.0**; associated paper
https://doi.org/10.1016/j.envc.2026.101453 has separate article terms.
All 19 originals were provider-MD5 verified. Sixteen small originals and metadata
are in `external_data/gsm_competition_20261007/`; three unchanged rasters are on
Hugging Face under `external_sources/gsm_competition_20261007/`, with the manifest
in both releases. Our adaptations in `data/derived/gsm_competition_20261007/`
retain attribution and CC-BY-4.0. The authors have not endorsed our analyses.

GCE-LTER long-term monitoring: Steven C. Pennings, PLT-GCES-1609 (2016), v7.0,
https://doi.org/10.6073/pasta/935872ae9b32d59d2c59b26856f0ea95; and
POR-GCES-2106 (2021), v4.0,
https://doi.org/10.6073/pasta/89075cf18fa3761b0cb17646845e5ab9. Georgia Coastal
Ecosystems LTER Project, University of Georgia. Only metadata, provenance and
our scripts are released. Raw tables and newly computed numerical results remain
local because EML CC-BY-4.0 and legacy portal redistribution/notification terms
differ. No notifications to authors were sent. The derived biomass and flowering
summaries overlap with the original observation table and are not extra samples.

Chinese coastal patch traits: Yiwen Liu, Qian Dong, Ziyu Zheng, Wensi Hu,
Yuxiang Li, Chi Xu and Shuqing N. Teng (2026), *Environmental stress and
plant-plant interactions jointly shape intertidal cordgrass traits across broad
spatial scales*, https://doi.org/10.3389/fpls.2026.1913369; supplement
https://doi.org/10.3389/fpls.2026.1913369.s001, Figshare 33251937, file 67534884.
Article XML and supplement **CC-BY-4.0**, archived in
`external_data/china_patch_traits_20261007/`. Our table extraction, area
conversions, overlap screen and plots in `data/derived/china_patch_traits_20261007/`
are adaptations under the same attribution and licence; not endorsed by the
source authors. Only published aggregate data are included. Raw imagery and
individual trait measurements were not acquired.

Local Sentinel-2 extension: Copernicus Sentinel-2 Collection 1 Level-2A,
Earth Search `sentinel-2-c1-l2a`, collection-supplied citation
https://doi.org/10.5270/S2_-742ikth. **Contains modified Copernicus Sentinel data
[2019–2025]**. The Copernicus Sentinel Data Legal Notice permits reproduction,
distribution and modification with attribution; it is archived with the source
metadata. The catalogue's generic `proprietary` label is not substituted for that
linked legal notice. No MIT or CC-BY licence is asserted for these source pixels.
Native-grid spatial subsets retain original DN; spectral indices, composites,
quality masks and plots are our adaptations. Source metadata and hashes are in
`external_data/local_sentinel_c1_20261007/`, results in
`data/derived/local_sentinel_c1_20261007/`, and the complete 8.78 MB acquisition
archive on HF under `external_sources/local_sentinel_c1_20261007/`. Provider
product XML hashes were verified; full-band source checksums were not, because
only intersecting source tiles were acquired. CCAV map strata retain the Li et al.
attribution above. These analyses are not endorsed by ESA, the EU or Element 84.
