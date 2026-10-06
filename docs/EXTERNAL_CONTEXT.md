# External context and literature screen

The project now includes two reproducible external layers.

## GBIF occurrence context

The accepted GBIF name is *Sporobolus alterniflorus* (the current accepted
name for *Spartina alterniflora*). The GBIF search returned 4,584 georeferenced
records. Country facets and a small first-page coordinate sample are pinned in
`external_data/`; the country summary is in
`tables/gbif_spartina_global_country_summary.csv`. The facets are useful for
checking the broad native and introduced-range context. They are affected by
sampling and reporting bias and are not a population census or an independent
estimate of invasion rate.

The earlier China-only query returned 12 coordinate-bearing records. That count
is retained in the original audit for provenance, while the accepted-name query
avoids losing records because the species is indexed under its current name.

## Literature screen

`analysis/collect_external_context.py` queries OpenAlex with three explicit
strings: `Spartina alterniflora invasion`, `rapid evolution invasive plants`,
and `remote sensing biological invasion machine learning`. The resulting 75
works, titles, years, DOI links and citation counts are saved in
`tables/external_literature_screen.csv`. This is a transparent discovery list,
not a systematic review or a claim that citation count measures evidence
quality. The records help anchor the Introduction and Discussion in prior work
on estuarine impacts, rapid evolution and remote sensing.

The synthesis plot is `figures/fig_external_context_synthesis.pdf`. External
records are used for framing and independent context; all causal and
eco-evolutionary claims in the manuscript remain tied to the local archive and
the planned common-garden or transplant validation.
