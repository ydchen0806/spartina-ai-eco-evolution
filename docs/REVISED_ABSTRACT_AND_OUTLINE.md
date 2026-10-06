# Proposed Nature-style article frame

## Working title

**An aerial AI observatory reveals a shift from expansion to environmental tolerance in an invasive cordgrass**

## Draft abstract (evidence-calibrated)

Rapid phenotypic change can alter the ecological consequences of biological invasions, yet most evidence for rapid evolution comes from controlled experiments or retrospective genetic comparisons. We developed an auditable aerial-observation workflow that combines UAV imagery, semantic segmentation and spatially explicit patch tracking to reconstruct annual changes in an invasion front of *Spartina alterniflora* in coastal China. The recoverable patch-record archive contains 727 records from 2014–2021. Across the years for which parent-patch measurements are informative, newly recorded patches became progressively smaller relative to their putative parent patches, while the number of recorded patches fluctuated and did not show a significant monotonic trend. This shift was spatially heterogeneous and coincided with changes in the climatic context, motivating a machine-learning model for hypothesis-generating counterfactual simulations. The available observations support a transition in the spatial phenotype of the invasion process and identify environmental tolerance as a testable mechanism. They do not, on their own, establish heritability or causality; these claims require common-garden, transplant or genomic validation. Our framework turns archived aerial imagery into a quantitative observatory for testing eco-evolutionary hypotheses in invasions and provides a reproducible route from AI-derived phenotypes to falsifiable field experiments.

## One-sentence claim hierarchy

1. **Strong and currently supportable:** AI can recover a reproducible, spatially explicit patch record from aerial imagery.
2. **Supportable after raw-image reanalysis:** annual cohorts differ in patch-size and environmental-response distributions.
3. **Testable hypothesis:** the invasion process is shifting from rapid local expansion toward lower-growth, higher-tolerance strategies.
4. **Not supportable from the current archive alone:** the shift is heritable, caused by climate, or represents a genomic/epigenomic ecotype transition.

## Results paragraph order

1. **Aerial observatory.** Define study area, acquisition years, orthomosaic construction, training/holdout split, segmentation and matching uncertainty.
2. **Observed invasion phenotype.** Report detection-corrected patch occupancy, patch area, annual cohort composition and parent-normalized metrics with raw points and uncertainty.
3. **Environmental response.** Fit a hierarchical spatiotemporal model and report partial effects, spatial scales and held-out prediction; use MGWR as a sensitivity analysis.
4. **Counterfactual model.** Show calibrated predictions under observed, stable and extreme environments, with uncertainty and explicit non-causal language.
5. **Independent test.** Add common-garden/transplant or cross-site validation before using adaptation or heritability as a conclusion.

## Three sentences to remove from the current draft

- “This trait is heritable under natural selection.” Replace with: “The changing cohort distribution is consistent with selection on environmental sensitivity, but heritability remains to be tested.”
- “We treated each year as a new generation.” Replace with: “We analysed annual record cohorts; their correspondence to generations is an explicit uncertainty.”
- “The machine-learning model demonstrates the causal mechanism.” Replace with: “The model generates counterfactual predictions that prioritize mechanisms for experimental testing.”

