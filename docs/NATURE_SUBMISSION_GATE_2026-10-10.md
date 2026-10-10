# Nature-track submission gate (10 October 2026)

This audit records the evidence needed for a high-impact invasion and
eco-evolution submission. It is deliberately stricter than a reproducibility
checklist: a clean archive or attractive figure cannot replace independent
biological validation.

## Gates passed or substantially advanced

| Gate | Evidence in the release | Assessment |
|---|---|---|
| Image-to-table provenance | 1,001 recovered files independently rehashed; 15 RGB/mask pairs and 714 polygon deliveries reconciled | Passed as a provenance audit |
| Landscape counterpart | ScienceDB V4: 10 RGB orthomosaics and 10 distribution maps, 20 cm, 2013–2022; provider MD5 and HF LFS digests verified | Passed as a source and accounting audit |
| Fixed-footprint landscape result | 248.935 ha common support; mapped-positive area series and endpoint partitions conserve area | Passed as a numerical result; labels remain unvalidated |
| Temporal AI reliability | 15 leave-one-survey-out folds; balanced mean ROC-AUC 0.855, mean IoU 0.673; uniform prevalence bias 28.51 percentage points | Passed as a falsification/calibration result |
| Predictive leakage control | Within-fold preprocessing, temporal and buffered spatial holdouts | Passed for the stated predictive estimand |
| Public reproducibility | GitHub commit 4e7f541, HF digest verification, scripts, manifests and derived tables | Passed for the released scope |

## Decisive gates still open

| Gate | Why Nature reviewers will require it | Minimal completion package |
|---|---|---|
| Independent segmentation accuracy | Archived masks are the target of every current AI metric; label consistency is not truth | Two independent expert annotations of the frozen 480-crop pilot, including negative crops; report IoU, precision–recall, calibration and inter-annotator agreement on spatially held-out strata |
| Registration and event identity | A 0/1 transition can be misregistration, tide, phenology or label revision | Ground-control or feature-control-point registration uncertainty for each adjacent survey; manually adjudicate a blinded sample of retained, removed, added and merged candidates |
| Endpoint definition | 188 model rows conflict with area-derived relative gain in 2016/2018 | Recover the exporter or original code; pre-register one endpoint and repeat every temporal/spatial holdout under that endpoint |
| Mechanism and evolution | Image trends and climate associations do not establish heritability or adaptation | Replicated common-garden or reciprocal-transplant cohorts with source identity, environment, survival, biomass and reproductive output; genomic or pedigree evidence if adaptation is claimed |
| External-site transfer | Same-estuary public images partly overlap the recovered source and are not independent replication | A genuinely independent estuary or flight campaign with raw RGB, labels and acquisition metadata; evaluate the frozen model without retuning |

## Submission decision

The project currently supports a strong methodological and ecological
observation paper about how AI-derived invasion records fail under temporal
transfer, observation gaps and changing spatial units. It does **not** yet
support a Nature-level claim of rapid local adaptation, demographic invasion
rates or validated landscape occupation. The manuscript should be submitted as
a biological discovery paper only after the decisive gates above are closed.

## Reproducible entry points

- Main working draft: `manuscript/Spartina_working_draft_20261010.pdf`
- AI transfer audit: `docs/RGB_MASK_TRANSFER_AUDIT_2026-10-10.md`
- UAV recovery and fixed-support analysis: `docs/ZHANGJIANG_UAV_RECOVERY_2026-10-07.md`
- Numerical verification: `data/derived/rgb_mask_transfer_20261010/verification.json`
- Public release: <https://github.com/ydchen0806/spartina-ai-eco-evolution>
