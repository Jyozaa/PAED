# Protocol discrepancies and revised working eligibility

Registered reference: supplied PROSPERO CRD420251241478 version 3.0, published 1 August 2026, printed 4 November 2026. No register amendment or external-validation waiver was performed or inferred.

The population wording on page 2 specifies under-18 cardiac-ICU inpatients and excludes models without external validation or accuracy metrics. Page 7 records narrowing to cardiac intensive care. Page 5 nevertheless lists NICU/PICU subgroups; this ambiguity does not demonstrate a waiver of the restrictive wording. The team accepts general PICU for this working analysis, retaining Kenet. Its 38 adults remain an additional unresolved discrepancy with paediatric-only eligibility.

Previous exclusions remain: five Yu 2026 models for composite adverse events and Yu 2023 Gaussian Naive Bayes for inadequate graphical numerical results. The new team decision excludes entire Lu 2025 XGBoost, gMLP and PEDCA-FT entries, including their AUROCs: **Research-team decision: model excluded because sensitivity and specificity were extracted graphically and considered insufficiently reliable.** This is a model-level eligibility decision based on the sensitivity/specificity extraction, not a claim that those AUROCs were necessarily graph-read. Missing sensitivity/specificity alone does not exclude the other Lu models.

| study | setting | external validation | strict status | reason |
| --- | --- | --- | --- | --- |
| yu_2026 | CICU | not_reported | excluded_outcome_and_external_validation_not_demonstrated | Composite adverse events, and no demonstrated external validation |
| lu_2025 | CICU | explicitly_absent | excluded_no_external_validation | Single-centre internal cross-validation only |
| bose_2019 | CICU | explicitly_absent | excluded_no_external_validation | Single-centre train/test split; external validation explicitly absent |
| yu_2023 | CICU | not_reported | external_validation_not_demonstrated | Five-fold internal CV only recorded; external-validation requirement not demonstrated |
| kenet_2023 | general_PICU | not_reported | excluded_setting_mixed_age_and_external_validation_not_demonstrated | General PICU outside registered CICU scope, mixed age (38 aged 18+), and no demonstrated external validation |
| yu_2022 | CICU | not_reported | external_validation_not_demonstrated | Neither internal independent validation nor external validation established in extraction |


The revised working cohort contains 5 reports/17 models. Restricting setting alone leaves 4 CICU reports/11 models. No retained report demonstrates every strict criterion, particularly external validation; NR is not proof that validation never occurred. Lu and Bose explicitly lack external validation. The confirmatory strict subset remains zero demonstrated eligible reports/models.

The extraction framework permits multiple models/thresholds but not independent treatment of repeated results. AUROC across thresholds differs from an area under a cross-study SROC; a single operating point does not recover an AUROC. Protocol specificity wording is imprecise: specificity concerns non-arrest units. The full-protocol citation is the PRISMA statement rather than an accessible study-specific protocol. Search/screening totals and independent reviewer decisions are absent. QUADAS-2 and adapted GRADE remain registered; no replacement or completed dual review is claimed.

Before manuscript publication, the team must resolve scope, adult inclusion, external validation, overlapping Dallas patients, model/horizon selection, source uncertainty and Yu table linkage, and complete independent risk-of-bias/certainty review. The present revision is transparent team-directed eligibility, not a protocol amendment. Historical 20-model results remain on the parent branch and are explicitly separated in the before/after report.
