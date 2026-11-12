# Revised data audit

Only the original extraction CSV, List of Variables (3 pages), PROSPERO snapshot (7 pages) and their existing derivatives are used. No new papers, external data or correspondence were obtained. Original-file hashes are unchanged. Source row means 1-based logical CSV record including both header records; physical multiline spans are separate. Original/curated sources remain immutable, with raw PDFs/CSV and private narratives excluded from Git.

## Recalculated counts

There are 27 post-header records, 26 populated original model entries and 6 original reports. One record is a cross-reference, with no extracted results, rather than a blank row. After 9 whole-model exclusions, **5 reports and 17 models remain**, including **8 Lu models**. There are **18 numerical AUROC evaluations**, because Bose contributes separate training and test results, and 8 unspecified Lu +/- quantities. Only one labelled AUROC CI is supplied. Seven complete candidate diagnostic tables still come from two sources.

Previous exclusions remain: five Yu 2026 models for composite adverse events and Yu 2023 Gaussian Naive Bayes for inadequate graphical numerical results. The new team decision excludes entire Lu 2025 XGBoost, gMLP and PEDCA-FT entries, including their AUROCs: **Research-team decision: model excluded because sensitivity and specificity were extracted graphically and considered insufficiently reliable.** This is a model-level eligibility decision based on the sensitivity/specificity extraction, not a claim that those AUROCs were necessarily graph-read. Missing sensitivity/specificity alone does not exclude the other Lu models.

## Every source decision

| source_row | study_id | model_id | record_type | retained | exclusion_reason |
| --- | --- | --- | --- | --- | --- |
| 3 | yu_2026 | yu_2026_decision_tree | populated_model | False | Composite adverse event performance, not cardiac arrest alone |
| 4 | yu_2026 | yu_2026_random_forest | populated_model | False | Composite adverse event performance, not cardiac arrest alone |
| 5 | yu_2026 | yu_2026_xgboost | populated_model | False | Composite adverse event performance, not cardiac arrest alone |
| 6 | yu_2026 | yu_2026_logistic | populated_model | False | Composite adverse event performance, not cardiac arrest alone |
| 7 | yu_2026 | yu_2026_svm | populated_model | False | Composite adverse event performance, not cardiac arrest alone |
| 8 | lu_2025 | lu_2025_knn_dtw | populated_model | True |  |
| 9 | lu_2025 | lu_2025_svc_gak | populated_model | True |  |
| 10 | lu_2025 | lu_2025_knn_unif | populated_model | True |  |
| 11 | lu_2025 | lu_2025_logistic | populated_model | True |  |
| 12 | lu_2025 | lu_2025_rf_gini | populated_model | True |  |
| 13 | lu_2025 | lu_2025_xgboost | populated_model | False | Research-team decision: model excluded because sensitivity and specificity were extracted graphically and considered insufficiently reliable. |
| 14 | lu_2025 | lu_2025_lightgbm | populated_model | True |  |
| 15 | lu_2025 | lu_2025_tabnn | populated_model | True |  |
| 16 | lu_2025 | lu_2025_tresnet | populated_model | True |  |
| 17 | lu_2025 | lu_2025_gmlp | populated_model | False | Research-team decision: model excluded because sensitivity and specificity were extracted graphically and considered insufficiently reliable. |
| 18 | lu_2025 | lu_2025_pedca_ft | populated_model | False | Research-team decision: model excluded because sensitivity and specificity were extracted graphically and considered insufficiently reliable. |
| 19 | bose_2019 | bose_2019_glm | populated_model | True |  |
| 20 | yu_2023 | yu_2023_rdn_boost | populated_model | True |  |
| 21 | yu_2023 | yu_2023_logistic_reference | cross_reference | False | Cross-reference only; no extracted result; links to populated Yu 2022 record 29 |
| 22 | yu_2023 | yu_2023_gnb | populated_model | False | Graphical results without adequately extractable numerical estimates |
| 23 | kenet_2023 | kenet_2023_logistic | populated_model | True |  |
| 24 | kenet_2023 | kenet_2023_svm | populated_model | True |  |
| 25 | kenet_2023 | kenet_2023_random_forest | populated_model | True |  |
| 26 | kenet_2023 | kenet_2023_xgboost | populated_model | True |  |
| 27 | kenet_2023 | kenet_2023_lightgbm | populated_model | True |  |
| 28 | kenet_2023 | kenet_2023_soft_voting | populated_model | True |  |
| 29 | yu_2022 | yu_2022_logistic | populated_model | True |  |


## Retained study/model counts

| study | retained models |
| --- | --- |
| lu_2025 | 8 |
| bose_2019 | 1 |
| yu_2023 | 1 |
| kenet_2023 | 6 |
| yu_2022 | 1 |


The original 42 source columns and two header records are preserved in the schema metadata. All 1,134 data-cell missingness states remain audited. Source records 13, 17 and 18 are excluded from retained tables, figures, ranges and pooled inputs. Their original text remains in source provenance and excluded inventory rows only. Lu retained AUROC range is **0.5472-0.7329**. No arithmetic model average is presented as a study estimate. Lu and Yu 2022 now have no eligible sensitivity/specificity observations; missing is never replaced by zero.

Seven diagnostic tables still have unchanged counts. The Kenet random-forest specificity discrepancy remains: reported 77.8%, counts 77.5632%. Yu integer percentages agree within their rounding tolerance. Other flags preserve possible Dallas reuse, missing external validation, clustered windows, mixed-age Kenet, inconsistent recruitment dates and unresolved Yu 2023 table linkage.
