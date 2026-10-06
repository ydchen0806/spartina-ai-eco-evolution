# Results draft (evidence-calibrated)

## Aerial patch archive

The recovered patch table contains 727 records spanning 2014–2021. Annual
record counts ranged from 36 to 141 and therefore describe the detection record,
not population size. The median new-record area proxy varied non-monotonically
from 234 to 492 pixels. The parent-size field was structurally constant in 2020
and 2021, so those years were retained for quality control but excluded from
parent-normalized comparisons.

Among the informative years (2014–2019), the median log10(new-record area /
putative-parent area) declined monotonically (Spearman ρ = −0.943, n = 6,
P = 0.0048). This is evidence for a change in the recorded spatial phenotype of
new patches. It is not evidence that each annual cohort represents a biological
generation, and it does not establish heritability.

## Recovered environment–growth archive

The independent workbook contains 854 records from 2014–2020. Mean observed
growth rate declined from 2.303 in 2014 to 1.504 in 2020 (year-level Spearman
ρ = −0.714, n = 7, P = 0.071). The exported simulation is correlated with the
observed index (Pearson r = 0.905; RMSE = 0.699), which is a calibration result.
When models are evaluated on held-out years, the best R² is 0.178 (RMSE 1.383);
under spatial-block holdout the best R² is 0.394 (RMSE 1.187). These scores set
the current limit on claims about environmental extrapolation.

## Scenario export audit

The seven scenario workbooks contain different PCA inputs and different
`growth_rate_pred` means (1.961–2.157), whereas their `growth_rate_simulation`
vectors are identical. We therefore treat `growth_rate_pred` as a candidate
counterfactual output and the invariant column as an unresolved export or
baseline column. Mechanistic interpretation waits for the original model code
and an independent scenario re-run.

## Discussion boundary

Together these data motivate a testable hypothesis: the invasion process may be
shifting from rapid local expansion toward a phenotype that persists under a
changing environment. The archive supports that hypothesis as an ecological
pattern and prioritises a common-garden or reciprocal-transplant test. It does
not yet support the terms *heritable adaptation*, *ecotype*, *genomic
adaptation* or *causal climate effect*.
