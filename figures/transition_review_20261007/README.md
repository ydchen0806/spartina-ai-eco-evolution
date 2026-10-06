# Diagnostic transition review pack

Seed: 20261007. One random archived observation is sampled per source survey and
automated screening category, plus up to four high-fill cases. This deliberately
enriched sample is for discovering failure modes; it cannot estimate event
prevalence, segmentation accuracy or generalization performance.

Start with `raw_pairs/` and `blank_review_form.csv`. These pairs show the same
array-index window in successive original orthomosaics. They have not been
registered. Open `overlay_pairs/` only after an initial RGB review; pink marks
the archived binary mask. `diagnostic_sample_manifest.csv` contains the screening
categories and full-image window coordinates. The window is centred on the
source bounding box, not necessarily the next archived coordinate. Month-only
survey filenames do not establish a known acquisition day.

All forms are blank: no expert annotation or independent performance estimate
is implied. A subsequent probability sample including old-mask-negative regions
is required for formal validation. Preserve ambiguous and unobservable cases;
do not force death/merger labels from missing masks.
