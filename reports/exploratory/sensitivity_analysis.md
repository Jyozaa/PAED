# EXPLORATORY: sensitivity analysis

The supplied extraction is authoritative for this task and has not been independently verified against original papers. No new studies, external confidence intervals, author correspondence or patient-level records were consulted. Reported source values are unchanged. Original confirmatory feasibility conclusions and descriptive outputs are preserved. The numbers here are **conditional pooled calculations**, not the primary evidence-supported findings or established clinical accuracy.

The following are matched-scenario contrasts, changing one configured factor at a time. They are not causal model comparisons or hypothesis tests. All paired scenarios and numerical deltas are in [sensitivity_contrasts.csv](../../results/exploratory/sensitivity_contrasts.csv). The table reports maximum absolute changes over the configured grid only; larger changes under unexamined assumptions remain possible.

| analysis | assumption changed | matched pairs | max absolute delta AUROC | max absolute delta sensitivity (pp) | max absolute delta specificity (pp) |
| --- | --- | --- | --- | --- | --- |
| auroc | Assumed AUROC SE | 18 | 0.070867 |  |  |
| auroc | Kenet model | 18 | 0.041046 |  |  |
| auroc | Dallas substitution | 9 | 0.042934 |  |  |
| diagnostic | Between-source covariance | 180 |  | 3.308 | 8.404 |
| diagnostic | Yu variance inflation | 45 |  | 3.563 | 9.115 |
| diagnostic | Kenet design effect | 90 |  | 6.591 | 13.400 |
| diagnostic | Kenet model | 96 |  | 10.949 | 20.671 |
| diagnostic | Within-source correlation | 9 |  | 0.172 | 0.784 |


## 1. Assumed AUROC SE

Increasing assumed original-scale uncertainty changes transformed variances, study weights and estimated tau². The pooled result need not move monotonically or its interval widen monotonically, because relative weights and estimated random heterogeneity change together. The genuine Yu 2023 CI is retained while other SEs vary. Across all 18 configurations, pooled AUROC spans 0.7689-0.8451; this is not an uncertainty interval over a probability model of assumptions.

## 2. Representative Kenet model

All logistic, soft-voting and XGBoost choices are reported; no observed maximum is selected as the preferred conclusion. A constant original-scale SE corresponds to a larger logit SE near AUROC=1, so high reported AUROC does not guarantee high inverse-variance weight. The full weight ledger makes this visible. Model-selection sensitivity does not establish an architecture winner.

## 3. Substitute Yu 2022

Yu 2022 replaces, never accompanies, Yu 2023. This changes both the source estimate (0.83 versus 0.85) and uncertainty provenance: Yu 2023 has a labelled CI, while Yu 2022's variance is assumed. The matched contrast is a joint substitution, not an isolated estimate of a publication-year or algorithm effect.

## 4. Kenet clustering assumptions

D=1 is the naive independence scenario, not an endorsed analysis of windows. D=5/20 inflate source covariance while preserving counts and logit points. Relative source influence changes and conditional logit-mean variances increase when only a source covariance is inflated at fixed T/rho. Summary point estimates can shift toward Yu, with the direction depending on the selected Kenet model. The illustrative D values do not identify real ICCs or validate an effective patient count.

## 5. Between-source and within-source covariance

T0 assumes no between-source heterogeneity; T05 assumes SDs=0.5 with three correlations; T1 assumes SDs=1 with zero correlation. All are fixed, not estimated. Yu inflation and within-rho checks are separate sensitivity axes. These assumptions change the joint weights, means and intervals; correlation is in sensitivity/FPR coordinates. The transformed conditional summaries span sensitivity 0.8730-0.9824, specificity 0.6560-0.8750. Separate extremes are not one simultaneous operating point. Known-assumed-covariance intervals omit uncertainty about T, D and rho.

## 6. Relatively stable conclusions

Within this grid AUROC summaries remain above 0.5, but that numerical pattern is conditional on selected reported points, assumed uncertainty and model form. The source-data facts remain stable: genuine AUROC uncertainty is scarce; Kenet observations are repeated windows; Yu linkage remains unresolved; no confirmed external validation or universal threshold is added. Numerical stability does not validate clinical accuracy.

## 7. Results too assumption-dependent for clinical interpretation

There is no unique pooled AUROC or diagnostic operating point that can be selected as the evidence-supported answer. The apparently precise T0/D1 result assumes independence and zero heterogeneity that the extraction does not establish. Wider scenarios are not automatically adequate either. These summaries cannot determine patient-level missed arrests, alert burden, deployment safety or prospective benefit.

EXPLORATORY — uncertainty assumptions supplied by analyst; not validated pooled clinical accuracy.

EXPLORATORY — clustered windows, unresolved analysis units and assumed statistical parameters.
