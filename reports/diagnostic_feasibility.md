# Diagnostic synthesis: revised evidence feasibility

**Confirmatory status: not statistically defensible from the supplied evidence.** Seven tables represent six Kenet algorithms on shared windows and one Yu 2023 representative fold. Zero confirmed independent patient-level tables contribute to a confirmatory pooled fit. No unrestricted bivariate covariance or HSROC curve is estimated.

| study_id | model_name | tp | fp | fn | tn | sensitivity_recalculated | specificity_recalculated | ppv_recalculated | npv_recalculated | analysis_unit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| yu_2023 | rdn boost | 36 | 63 | 4 | 115 | 0.9 | 0.6460674157303371 | 0.36363636363636365 | 0.9663865546218487 | representative_fold_table_unit_unverified |
| kenet_2023 | logistic | 184 | 944 | 27 | 1904 | 0.8720379146919431 | 0.6685393258426966 | 0.16312056737588654 | 0.9860176074572761 | repeated_5_minute_window |
| kenet_2023 | svm | 206 | 965 | 5 | 1883 | 0.976303317535545 | 0.6611657303370787 | 0.17591801878736124 | 0.9973516949152542 | repeated_5_minute_window |
| kenet_2023 | random forest | 195 | 639 | 16 | 2209 | 0.9241706161137441 | 0.7756320224719101 | 0.23381294964028776 | 0.992808988764045 | repeated_5_minute_window |
| kenet_2023 | xgboost | 210 | 866 | 1 | 1982 | 0.995260663507109 | 0.6959269662921348 | 0.19516728624535315 | 0.9994957135653051 | repeated_5_minute_window |
| kenet_2023 | lightgbm | 205 | 850 | 6 | 1998 | 0.9715639810426541 | 0.7015449438202247 | 0.1943127962085308 | 0.9970059880239521 | repeated_5_minute_window |
| kenet_2023 | soft voting | 192 | 345 | 19 | 2503 | 0.909952606635071 | 0.8788623595505618 | 0.3575418994413408 | 0.992466296590008 | repeated_5_minute_window |


Every Kenet table totals 3,059 five-minute windows (211 positive, 2,848 negative) from a test cohort recorded as 229 patients with five CA patients. Window totals are not independent patient/arrest counts. No patient-level confusion matrix, intrapatient correlation or adequate clustering adjustment is supplied. Conditional reconciliation of 211 positive windows with a 3-hour/five-minute rule and five patients requires event multiplicity/labeling information; no one-arrest-per-patient assumption is asserted.

Yu 2023 has 36 TP, 63 FP, 4 FN and 115 TN, total 218 unresolved units. Rates recalculate to 90% sensitivity, 64.6067% specificity, 36.3636% PPV and 96.6387% NPV. Its model attribution was assumed by the extractor, and fold, threshold, exact horizon and unit remain unresolved. It is not silently linked to its 1-hour AUROC. No integer tables are reconstructed from percentages or cohort totals.

Lu has no eligible retained operating points after the three whole-model exclusions. Yu 2022 also has no model-level sensitivity/specificity. Bose's reported operating percentages do not identify an independent patient table. No naive window binomial intervals are reported in this descriptive layer.

The separate 96-scenario joint normal-logit GLS calculation fixes covariance assumptions rather than learning a full covariance from two sources. Counts and those assumptions are unchanged and the revision pipeline compares all scenarios against their saved previous values. It does not claim a fitted unrestricted bivariate/HSROC model or verified patient-level accuracy.
