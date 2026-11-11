# Full extraction audit

All 3 supplied files were read completely before analysis: the CSV, the 3-page extraction framework, and the 7-page PROSPERO snapshot. PDF text was extracted page by page and its layout checked locally. No original study full texts or patient data were supplied. Original files and extracted PDF text remain local and ignored by Git.

## Counts and source numbering

- 42 columns; two header records (group labels and original field names).
- 27 records after headers: 26 populated model entries, **1 cross-reference record, 0 completely blank records**.
- Six original study reports: Yu 2026 (5 models), Lu 2025 (11), Bose 2019 (1), Yu 2023 (2 populated, plus 1 unpopulated cross-reference), Kenet 2023 (6), Yu 2022 (1).
- Five Yu 2026 models excluded for composite outcomes, plus one Yu 2023 Gaussian Naive Bayes model excluded for insufficient numerical results.
- The cross-reference at logical record 21 points to Yu 2022 record 29; it is not counted as a seventh exclusion from the 26 populated models and is not forward-filled into an extra result.
- Retained: **5 studies, 20 models**, four conservative potential cohort groups (Yu 2022/2023 grouped for possible reuse).
- Numerical AUROC: 21 estimates across 20 retained models; Bose contributes distinct training and held-out test values. Only 1 estimate has a labelled 95% CI. Eleven Lu values have unspecified +/- variation.
- Seven complete candidate 2x2 tables: six Kenet models and one Yu 2023 representative fold; two study sources, zero confirmed independent patient-level tables eligible for pooling.

The preliminary “one blank row” checkpoint is corrected to a cross-reference with two non-empty cells. All other preliminary study/model counts reconcile. Source row denotes the **logical record** starting with header record 1; physical multiline spans are retained in `data_audit.csv` and the curated JSON.

## Record decisions

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
| 13 | lu_2025 | lu_2025_xgboost | populated_model | True |  |
| 14 | lu_2025 | lu_2025_lightgbm | populated_model | True |  |
| 15 | lu_2025 | lu_2025_tabnn | populated_model | True |  |
| 16 | lu_2025 | lu_2025_tresnet | populated_model | True |  |
| 17 | lu_2025 | lu_2025_gmlp | populated_model | True |  |
| 18 | lu_2025 | lu_2025_pedca_ft | populated_model | True |  |
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


## Scope and metrics

Inventories enumerate every populated original model, study, metric text, outcome context, horizon, validation and dependency identifier. `source_cell_states.csv` audits all 27 x 42 = 1,134 data cells without publishing private text. Excluded results are not used for descriptive working-cohort performance ranges. No 2x2 reconstruction or CI imputation was made.

The supplied framework prioritizes TP/FP/FN/TN and repeated-model extraction. The CSV adds AUROC but lacks dedicated AUROC CI-method, threshold-specific evaluation-unit and cluster-covariance fields. See the complete dictionary and feasibility reports for the consequences.

## Numerical validation

1 retained model/metric discrepancy exceeds the documented rounding tolerance: Kenet random-forest specificity, reported 0.778 versus 0.77563202 from counts (difference -0.00236798). Yu 2023 specificity 65% and PPV/NPV 36%/97% agree with exact count-derived values within integer-percentage rounding. Source values are never overwritten.

Other flags include probable Dallas cohort reuse; missing external validation; Kenet repeated-window clustering and 38 adult participants; graph-read Lu operating points; duplicated KNN quality text across Lu models; conflicting recruitment dates; approximate distal AUROC ranges; and uncertain linkage of the Yu 2023 representative-fold table.
