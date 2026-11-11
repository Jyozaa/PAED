# Protocol discrepancies and exploratory scope

Registered reference: supplied PROSPERO snapshot **CRD420251241478, version 3.0 (1 August 2026), printed 4 November 2026**, pages 2, 4-5 and 7. No amendment was performed by this project. The working decisions below are supplied by the research team in this task, not inferred from apparent performance.

## Registered wording and working decisions

Page 2 limits the population to paediatric patients under 18 in cardiac intensive care and excludes models without external validation or reported accuracy metrics. Page 7 explicitly records narrowing to cardiac intensive care. Page 5 also lists NICU/PICU subgroups, which creates internal ambiguity but does not establish that the restrictive population criterion was waived.

The team explicitly retained **Kenet 2023 general PICU** because cardiac arrest prediction is the working focus. The current five-study cohort is therefore **exploratory and not fully protocol-concordant**. General PICU inclusion does not automatically authorize adult inclusion: Kenet's extraction includes **38 patients aged 18+** with zero CA, with no age-restricted accuracy tables. That additional discrepancy requires confirmation or paediatric-only results.

The team excluded all Yu 2026 models because outcomes combine arrest and therapeutic/composite events, and excluded Yu 2023 Gaussian Naive Bayes because numerical performance cannot be adequately extracted. Yu 2023 RDN Boost remains. Record 21 is a cross-reference to Yu 2022, not a separate quantified logistic model.

## External validation remains unresolved

| study | setting | external_validation | strict_status | reason |
| --- | --- | --- | --- | --- |
| yu_2026 | CICU | not_reported | excluded_outcome_and_external_validation_not_demonstrated | Composite adverse events, and no demonstrated external validation |
| lu_2025 | CICU | explicitly_absent | excluded_no_external_validation | Single-centre internal cross-validation only |
| bose_2019 | CICU | explicitly_absent | excluded_no_external_validation | Single-centre train/test split; external validation explicitly absent |
| yu_2023 | CICU | not_reported | external_validation_not_demonstrated | Five-fold internal CV only recorded; external-validation requirement not demonstrated |
| kenet_2023 | general_PICU | not_reported | excluded_setting_mixed_age_and_external_validation_not_demonstrated | General PICU outside registered CICU scope, mixed age (38 aged 18+), and no demonstrated external validation |
| yu_2022 | CICU | not_reported | external_validation_not_demonstrated | Neither internal independent validation nor external validation established in extraction |


No retained study **demonstrates** external validation in the supplied extraction. Lu and Bose explicitly lack it; Yu 2022, Yu 2023 and Kenet are recorded NR or only internally validated. NR is not proof that no external validation exists, but it cannot satisfy an affirmative eligibility requirement. Internal held-out testing and cross-validation are not external validation.

Under strict application with demonstrated eligibility required, **0 studies / 0 models** can be confirmed eligible from these files. Four retained CICU study reports / 14 models pass the setting restriction alone; six Kenet models fail that restriction. If the external-validation requirement were explicitly revised, the CICU-only descriptive subset would contain those four reports, with probable overlap in the two Dallas publications. Its AUROC pooling still lacks sufficient independent variances; only one candidate confusion matrix remains, with unresolved linkage. No protocol-concordant pooled analysis is possible now.

## Further issues requiring explicit methodological resolution

- The extraction framework allows multiple models per paper and multiple thresholds. These are repeated results, not independent studies. The present pipeline adds dependency and analysis-unit checks.
- The registration combines AUROC extraction with AUC from HSROC or trapezoidal integration. A study's threshold-integrated AUROC and area under a cross-study summary ROC are different estimands. A single sensitivity/specificity pair cannot recover a study's AUROC.
- Protocol sensitivity/specificity wording mentions neonates despite broader paediatric eligibility. Specificity concerns non-arrest units, not the proportion of arrest cases detected. SMD is mentioned without a defined contrast and is not used here.
- The full-protocol citation in the snapshot is the PRISMA 2020 reporting statement, not an accessible study-specific full protocol. A complete search strategy, screening totals and independent extraction decisions are not supplied. The dataset flow is not represented as a full PRISMA flow.
- QUADAS-2 and adapted GRADE remain registered. No tool replacement, dual-reviewer assessment or formal certainty grade is asserted.

## Team confirmation before publication

Confirm and document the general-PICU change; resolve mixed-age Kenet eligibility; clarify whether to retain the external-validation requirement, seek missing external studies or formally revise the protocol; obtain patient/cluster-adjusted results and genuine AUROC uncertainty; confirm Dallas overlap; confirm representative models and non-peak-driven horizon choices; verify the Yu 2023 table's model, fold, threshold, horizon and unit; independently assess bias/certainty and reconcile any changes with the register. This report does not claim a waiver or amended PROSPERO record.
