# Revised scenario sensitivity and before/after comparison

This eligibility revision wholly excludes Lu 2025 XGBoost, gMLP and PEDCA-FT because their sensitivity/specificity was graphically extracted and considered insufficiently reliable. Their AUROCs are excluded with the entries; this does not assert that those AUROCs were graphical. The revised extraction retains five reports and 17 models, including eight Lu models. Other Lu models remain eligible despite missing operating points. Only the supplied sources and existing derivatives are used. Original source hashes are unchanged and no new papers, clinical data or correspondence were obtained. Confirmatory pooling remains unsupported; every pooled number here is explicitly conditional on analyst assumptions.

| measure | previous | revised |
| --- | --- | --- |
| Retained study reports | 5 | 5 |
| Retained models | 20 | 17 |
| Retained Lu models | 11 | 8 |
| Lu reported AUROC range | 0.5472-0.7504 | 0.5472-0.7329 |
| Core AUROC scenarios | 18 | 18 |
| Core conditional pooled AUROC range | 0.7689-0.8451 | 0.7241-0.8305 |
| Additional retained-Lu AUROC scenarios | 0 | 126 |
| All revised Lu-choice conditional pooled AUROC range | Not previously assessed | 0.7120-0.8441 |
| Diagnostic scenarios | 96 | 96 |
| Conditional diagnostic sensitivity (%) | 87.2956-98.2449 | 87.2956-98.2449 |
| Conditional diagnostic specificity (%) | 65.5968-87.4968 | 65.5968-87.4968 |


| analysis | factor | matched pairs | max absolute delta AUROC | max absolute sensitivity change (pp) | max absolute specificity change (pp) |
| --- | --- | --- | --- | --- | --- |
| auroc | Assumed AUROC SE | 144 | 0.102521 |  |  |
| auroc | Kenet model | 144 | 0.050236 |  |  |
| auroc | Dallas substitution | 72 | 0.044747 |  |  |
| auroc | Lu representative | 504 | 0.061532 |  |  |
| diagnostic | Between-source covariance | 180 |  | 3.308 | 8.404 |
| diagnostic | Yu variance inflation | 45 |  | 3.563 | 9.115 |
| diagnostic | Kenet design effect | 90 |  | 6.591 | 13.400 |
| diagnostic | Kenet model | 96 |  | 10.949 | 20.671 |
| diagnostic | Within-source correlation | 9 |  | 0.172 | 0.784 |


Matched contrasts change one configured factor at a time; they are not superiority tests or sampling confidence intervals. The expanded Lu-choice grid is distinguished from the 18 revised core scenarios. Saved predecessor results and all paired changes are independently checked against the parent Git commit.

1. Changing assumed AUROC SE changes logit precision, weights and estimated tau². Changes need not be monotonic, and conditional intervals need not widen monotonically as the estimated random variance also changes.
2. Changing Kenet model is always a separate scenario, not extra independent data. No architecture winner is inferred.
3. Substituting Yu 2022 changes both its point and uncertainty provenance, since all four variances then become hypothetical. Dallas reports never appear together.
4. Inflating Kenet covariance changes its influence and conditional logit-mean covariance while preserving all counts; the design effects are unmeasured assumptions.
5. T, Yu inflation and correlation choices remain hypothetical. The diagnostic grid is numerically unchanged by the Lu exclusions, not newly validated by numerical reproduction.
6. All original source-data limitations persist across assumptions. Stable numbers do not establish clinical validity.
7. No unique pooled clinical accuracy is supported. Wider or apparently precise scenarios are not automatically adequate corrections for bias, clustering, thresholds or unverified units.

## Additional Lu selection sensitivity

| lu_model_id | individual_auroc | scenario_count | pooled_min | pooled_max | max_absolute_change_from_matched_lu_logistic |
| --- | --- | --- | --- | --- | --- |
| lu_2025_logistic | 0.6292 | 18 | 0.7240731071621067 | 0.8305023589110181 | 0.0 |
| lu_2025_knn_dtw | 0.5527000000000001 | 18 | 0.7127655421224767 | 0.8210303676945517 | 0.020428806993685877 |
| lu_2025_svc_gak | 0.5472 | 18 | 0.7119517745376744 | 0.820346029449468 | 0.021728795179537075 |
| lu_2025_knn_unif | 0.5740999999999999 | 18 | 0.7159313582816196 | 0.8236824921328535 | 0.015193310238810875 |
| lu_2025_rf_gini | 0.7329000000000001 | 18 | 0.7659480078673743 | 0.8440928251643599 | 0.04187490070526756 |
| lu_2025_lightgbm | 0.6142 | 18 | 0.7218597124098084 | 0.8286391697187089 | 0.0044322806190745245 |
| lu_2025_tabnn | 0.6215999999999999 | 18 | 0.7229521528741276 | 0.8295571084633281 | 0.002277697844302984 |
| lu_2025_tresnet | 0.7221 | 18 | 0.7611830589808515 | 0.8425747545892683 | 0.03710995181874477 |


EXPLORATORY — uncertainty assumptions supplied by analyst; not validated pooled clinical accuracy.

EXPLORATORY — clustered windows, unresolved analysis units and assumed statistical parameters.

See [full before/after comparison](../revisions/exclusion_comparison.md), all source/weight/covariance ledgers, and the complete scenario tables. No missing source information was invented.
