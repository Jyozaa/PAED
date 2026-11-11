# Analysis B: bivariate/HSROC diagnostic synthesis

**Status: Not statistically defensible from the supplied data.** Count validation and the hierarchical eligibility workflow completed. There is no fitted bivariate model, HSROC curve, pooled sensitivity/specificity, convergence assessment, CI or heterogeneity estimate.

## Seven tables, two study sources, no confirmed eligible independent patient-level tables

| study_id | model_name | tp | fp | fn | tn | sensitivity_recalculated | specificity_recalculated | ppv_recalculated | npv_recalculated | analysis_unit | table_horizon |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| yu_2023 | rdn boost | 36 | 63 | 4 | 115 | 0.9 | 0.6460674157303371 | 0.36363636363636365 | 0.9663865546218487 | representative_fold_table_unit_unverified | not_established |
| kenet_2023 | logistic | 184 | 944 | 27 | 1904 | 0.8720379146919431 | 0.6685393258426966 | 0.16312056737588654 | 0.9860176074572761 | repeated_5_minute_window | within_3h_window_label |
| kenet_2023 | svm | 206 | 965 | 5 | 1883 | 0.976303317535545 | 0.6611657303370787 | 0.17591801878736124 | 0.9973516949152542 | repeated_5_minute_window | within_3h_window_label |
| kenet_2023 | random forest | 195 | 639 | 16 | 2209 | 0.9241706161137441 | 0.7756320224719101 | 0.23381294964028776 | 0.992808988764045 | repeated_5_minute_window | within_3h_window_label |
| kenet_2023 | xgboost | 210 | 866 | 1 | 1982 | 0.995260663507109 | 0.6959269662921348 | 0.19516728624535315 | 0.9994957135653051 | repeated_5_minute_window | within_3h_window_label |
| kenet_2023 | lightgbm | 205 | 850 | 6 | 1998 | 0.9715639810426541 | 0.7015449438202247 | 0.1943127962085308 | 0.9970059880239521 | repeated_5_minute_window | within_3h_window_label |
| kenet_2023 | soft voting | 192 | 345 | 19 | 2503 | 0.909952606635071 | 0.8788623595505618 | 0.3575418994413408 | 0.992466296590008 | repeated_5_minute_window | within_3h_window_label |


Each Kenet table totals **3,059 windows = 211 positive + 2,848 negative**, shared across six algorithms. These belong to a **229-patient test set with five CA patients**, not 3,059 independent patients or 211 independent arrests. Overall cohort totals (1,145 patients, 15 CA; 14,714 windows, 516 positive) are distinct from test totals. Patient-disjoint train/test splitting prevents certain leakage but does not remove within-patient dependence among test windows. A further denominator-reconciliation question is that 211 positive windows exceed 5 x 36 = 180 under an **unstated one-arrest-per-patient assumption** and a 3h/five-minute labeling rule. Repeated arrests, exact labeling and segment inclusion must be checked; this is a conditional consistency flag, not proof of an error or a reconstructed event count. No intrapatient correlation, cluster-adjusted covariance, patient-level predictions or patient-level confusion table is supplied. No Wilson/binomial interval is displayed for windows.

The Yu 2023 matrix is a representative fold: **36 TP, 63 FP, 4 FN, 115 TN**, total **218 units**. Sensitivity = 0.9000; specificity = 0.646067; PPV = 0.363636; NPV = 0.966387. The extractor **assumed** model attribution to RDN Boost; exact fold, threshold, horizon and whether units are patients/events/windows are not established. Its 40 positive units exceed 160/5 = 32, so a simple equally divided patient-fold reconstruction is not justified; this does not prove an error. The matrix is not silently linked to the 1-hour AUROC. It cannot be reconstructed or reweighted from cohort totals.

## Thresholds and conditional synthesis

Kenet thresholds were chosen at validation-ROC operating points, with numeric values unavailable. Bose uses bootstrap-dependent ROC thresholds; example scores 0.5/0.56 are not a common operating point. Yu thresholds are missing; Yu 2022's NIRS predictor cutoff is not a multivariable classifier threshold. Lu's three operating points are graph-read and have no verified count denominators or thresholds. These points are descriptive only.

A full bivariate model has two mean logits, two between-study variances and a correlation. Even granting independence to the **two source cohorts**, covariance estimation would be exceptionally fragile. Here Kenet clustering and Yu linkage fail before this statistical question arises: **0 eligible datasets; 0 independent studies / 0 model estimates contribute to an inferential fit**. Models are not separate studies. Separate univariate pooling cannot solve this dependency or recover a universal threshold.

The conditional R code implements established `mada::reitsma` for eligible interior proportions with REML and zero continuity correction, requires at least five independent datasets plus explicit model/unit/comparability confirmation, checks finite covariance, and records the true summary and fitted SROC only after a successful model. The minimum is an analyst safeguard, not an identifiability theorem. For zero-cell sparse independent data it stops and calls for a binomial HSROC implementation rather than silently correcting counts. No zero cells exist in these seven tables, but their analysis units fail the gate. No artificial convergence attempt or fixed correlation is used.

[Primary simulation research](https://pmc.ncbi.nlm.nih.gov/articles/PMC5564999/) shows that complex hierarchical fits can be problematic with few/sparse studies; simpler models may be considered when scientifically suitable, but cannot make clustered or unlinked extraction rows independent. [Package documentation](https://rdrr.io/cran/mada/man/reitsma.html) defines the candidate bivariate implementation.

Sensitivity/specificity forest-style point plots and a **non-pooled** ROC-space scatter are generated. No smooth curve is drawn through heterogeneous model points. Denominator or clustering uncertainty is not disguised as narrow error bars.
