# Active Results draft — 2026-10-07

Supersedes earlier growth/tolerance conclusions. Full Methods and references: [MANUSCRIPT_WORKING_DRAFT.md](MANUSCRIPT_WORKING_DRAFT.md).



## Reconstructing the image-to-table evidence chain

We independently rehashed all 1,001 files in the recovered archive, comprising 38,654,767,408 bytes, and found no checksum discrepancies. Fifteen paired RGB images and binary masks had identical array dimensions of 26,606 by 24,443 pixels. RGB rasters carried a shared EPSG:4326 transform, whereas masks lacked a geographic reference. Equal dimensions and header transforms establish a common array convention but do not establish the accuracy of registration.

Two annotation deliveries contained matching polygon sets after standardizing ring start, orientation and redundant closing vertices: 714 images and 9,234 objects. Polygon rasterization and 79 delivered PNG masks had a median intersection over union of 0.9965. This comparison measures consistency between annotation encodings, not the accuracy of the segmentation model. The original training photographs, segmentation checkpoint and fixed training/validation/test split have not been recovered, and the original model performance remains unverified.

A fixed region of interest, inferred from the first survey and then held constant, linked 5,745 of 5,746 archived patch-date positions to recovered mask bounding boxes. Archived x and y represented bounding-box row and column within this crop, rather than full-image centroids. An exclusive-maximum rectangular foreground count reproduced 5,744 historical areas. This rule omits the final bounding-box row and column and can include foreground belonging to nearby objects. We consequently retain historical areas as archived measurements rather than validated component areas.

### The response and sample definition change the apparent temporal pattern

The annual matrix contained 2,459 candidate trajectory rows, of which 1,769 appeared in only one survey. Connecting successive observed years within rows produced 957 transitions. All had consecutive annual labels, although the selected survey dates varied within years. These transitions are conditional on the archived tracking procedure and do not constitute a census of demographic events.

All 854 records in the modelling workbook matched annual transitions on starting year, initial area, area increment and next-survey bounding-box position, preserving the frequency of repeated keys. Four records had multiple matching candidates, so the mapping did not establish a unique biological identity for every record. The retained set was exactly reproduced by the rule 0 < (A₁ − A₀)/A₀ < 10. This excluded 50 nonpositive changes and 53 relative increments of at least ten. The model thus described a selected set of growing, successfully tracked objects.

The stored growth_rate was inconsistent with (A₁ − A₀)/A₀ for all 138 records starting in 2016 and all 50 starting in 2018. The other five years agreed within numerical tolerance. No recovered transformation explained these differences. Accordingly, recomputation is a sensitivity analysis, rather than a claim to recover the intended original endpoint.

For the same 854 records, the Spearman correlation between year and annual mean endpoint was −0.714 for stored values and −0.107 for area-derived relative increments, with exact two-sided rank-permutation P values of 0.088 and 0.840, respectively (seven annual means). Including all 957 archived transitions gave a correlation of −0.607 for area-derived relative increments (exact P = 0.167). The latter mean is sensitive to extreme changes from small initial areas. These comparisons show that a mechanistic account of a temporal trend requires a resolved endpoint and an explicit sampling population; none of the comparisons independently establishes such a mechanism.

### Objects, trajectories and observation gaps

Eight-connected component extraction produced 8,280 components across the 15 cropped masks, including small components. Component areas summed exactly to independently calculated mask foreground counts in each survey. Eighty component-date objects were shared by 167 archived observations, giving 87 excess rows relative to unique objects. Shared endpoints may reflect branching tracks or duplicate assignments. Their cause remains to be determined, and these observations cannot be treated as independent individuals.

An unregistered adjacent-survey overlap screen examined 5,459 source observations. Of these, 1,386 continued to an archived successor that passed the overlap criterion, and 1,123 continued to a successor that did not. Another 177 lacked a next-row observation but overlapped another mask object; 2,772 lacked both a next-row observation and a qualifying overlap. One source bounding box was unresolved. These categories are diagnostic candidates, not rates of survival, recruitment, splitting or merging.

Eighty observations without a next-row record had at least 95% exact black or white RGB values at their preceding foreground locations in the next image. Inspection of diagnostic crops confirmed that complete black coverage gaps occur. This result demonstrates an observation problem without establishing that all flagged locations are missing data. Death cannot be assigned from absence in an unvalidated mask alone. The distinction parallels the separation of occurrence and detection in ecological observation models [6], although the current surveys do not by themselves satisfy the replicate-observation assumptions required for a fitted detection model.

Automatic feature matching did not resolve the alignment problem. Six of 14 adjacent image pairs supplied sufficient matches for a partial-affine diagnostic fit. Spatially held-out feature residuals remained substantial, and no pair passed the descriptive diagnostic gate. Features may include changing vegetation or erroneous matches; these residuals are not independent ground-control errors. No fitted transform was applied to the imagery or used to classify biological events.

### Prediction with starting information and explicit holdouts

We established a fixed benchmark using log initial area and initial bounding-box coordinates, excluding next-survey locations and legacy principal components. Three exactly repeated transitions were removed, leaving 954 observations in 661 dependency groups. Groups joined annual trajectory rows sharing a dated bounding-box position. We evaluated a training-mean baseline, ridge regression and extremely randomized trees using within-fold preprocessing, forward-year prediction and buffered spatial holdouts [7].

For the primary endpoint, log(A₁/A₀), pooled forward-year R² values were −0.591 for the training mean, −0.941 for ridge regression and −1.116 for trees (455 predictions across 2016–2020). Performance differed by year; for example, positive R² in some earlier folds did not extend to 2019 and 2020. Both fitted models had lower pooled mean absolute error than the mean baseline, while their squared errors were larger. The benchmark therefore reveals sensitivity to large prediction errors and temporal transfer, rather than supporting a uniform statement about all loss functions.

Within-site buffered spatial R² values for log area ratio were −0.017, 0.051 and 0.086, respectively, over 954 predictions. For relative area increment, trees achieved a spatial R² of 0.278 but a forward-year R² of −0.601. Initial area also enters both response definitions, so apparent size dependence need not identify a biological mechanism. These benchmarks do not evaluate climate effects or establish independent-site transfer. They identify the performance of starting-geometry baselines on archived, still unvalidated labels.
