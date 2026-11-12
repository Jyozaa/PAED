# Revised exploratory meta-analysis methods

This eligibility revision wholly excludes Lu 2025 XGBoost, gMLP and PEDCA-FT because their sensitivity/specificity was graphically extracted and considered insufficiently reliable. Their AUROCs are excluded with the entries; this does not assert that those AUROCs were graphical. The revised extraction retains five reports and 17 models, including eight Lu models. Other Lu models remain eligible despite missing operating points. Only the supplied sources and existing derivatives are used. Original source hashes are unchanged and no new papers, clinical data or correspondence were obtained. Confirmatory pooling remains unsupported; every pooled number here is explicitly conditional on analyst assumptions.

## Versioned eligibility and provenance

The parent `exploratory-pooling` branch preserves the previous 20-model results. Immutable aggregate snapshots supply the before/after comparisons and are checked against their parent Git commit. The original integrity record is retained in `config/baselines/analysis_20_model_integrity.json` and validated against its historical Git tree. A separate 17-model baseline protects current scientific outputs/configuration/data, following descriptive validation. Original raw and curated source data are never rewritten to accommodate exclusions. The revision explicitly replaces outdated expectations rather than disabling them.

## AUROC selections and scenario families

Core scenarios use Lu logistic regression **0.6292**, Bose held-out GLM **0.7500**, Yu 2023 RDN Boost **0.8500** or Yu 2022 logistic **0.8300**, and one Kenet model (logistic **0.8670**, XGBoost **0.9710**, soft voting **0.9570**). Lu logistic is an analyst-selected conventional baseline after exclusion of the named index, not an original verified primary designation. All 18 core scenarios cross 2 mutually exclusive Dallas choices, 3 Kenet choices and 3 missing-SE assumptions.

Every other retained Lu numerical AUROC is substituted in source-record order, with the same full cross. This produces 126 additional scenarios, 144 total, one Lu model per scenario. No model is selected to maximize the pooled result, and the potentially overlapping Dallas reports never contribute together. Four source groups are assumed independent for calculation, not proven independent clinical cohorts.

| estimate | source row | individual AUROC | uncertainty |
| --- | --- | --- | --- |
| lu_2025_logistic_a1 | 11 | 0.6292 | hypothetical original-scale SE 0.02/0.04/0.08 |
| bose_2019_glm_a2 | 19 | 0.75 | hypothetical original-scale SE 0.02/0.04/0.08 |
| yu_2023_rdn_boost_a1 | 20 | 0.85 | genuine 95% CI 0.79-0.9 |
| kenet_2023_logistic_a1 | 23 | 0.867 | hypothetical original-scale SE 0.02/0.04/0.08 |
| kenet_2023_xgboost_a1 | 26 | 0.971 | hypothetical original-scale SE 0.02/0.04/0.08 |
| kenet_2023_soft_voting_a1 | 28 | 0.957 | hypothetical original-scale SE 0.02/0.04/0.08 |
| yu_2022_logistic_a1 | 29 | 0.83 | hypothetical original-scale SE 0.02/0.04/0.08 |
| lu_2025_knn_dtw_a1 | 8 | 0.5527000000000001 | hypothetical original-scale SE 0.02/0.04/0.08 |
| lu_2025_svc_gak_a1 | 9 | 0.5472 | hypothetical original-scale SE 0.02/0.04/0.08 |
| lu_2025_knn_unif_a1 | 10 | 0.5740999999999999 | hypothetical original-scale SE 0.02/0.04/0.08 |
| lu_2025_rf_gini_a1 | 12 | 0.7329000000000001 | hypothetical original-scale SE 0.02/0.04/0.08 |
| lu_2025_lightgbm_a1 | 14 | 0.6142 | hypothetical original-scale SE 0.02/0.04/0.08 |
| lu_2025_tabnn_a1 | 15 | 0.6215999999999999 | hypothetical original-scale SE 0.02/0.04/0.08 |
| lu_2025_tresnet_a1 | 16 | 0.7221 | hypothetical original-scale SE 0.02/0.04/0.08 |


## Random-effects estimator and intervals

For source i, y_i=logit(AUC_i), v_i=SE_logit²; y_i follows a conditional normal random-effects model with mean mu and variance v_i+tau². Genuine Yu 2023 CI-derived logit SE remains 0.22252939, with unverified CI construction. For every missing SE, s=0.02/0.04/0.08 is **assumed on the AUROC scale**, and delta SE_logit=s/[p(1-p)]. None of Lu's unspecified +/- quantities is used as an SE.

The estimator remains **Paule-Mandel**, implemented in `statsmodels.stats.meta_analysis.combine_effects(method_re="iterated")`, not REML. It solves Q(tau²)=k-1 for a positive root or uses a valid zero boundary if Q(0)<=k-1. Every accepted root/boundary is checked. If the library iteration fails that check, the failure is preserved and the same equation is solved using configured SciPy `brentq`, with no input or estimator changes. Unsuccessful final fits have no numerical pooled estimate or forest.

Weights are 1/(v_i+tau²); mu=sum(w_i*y_i)/sum(w_i). Modified Hartung-Knapp variance is max[1/sum(w_i),Q(tau²)/((k-1)*sum(w_i))], using t(3) for four source groups. Pooled point/conditional 95% endpoints are back-transformed by expit. Tau² is estimated on logit scale conditional on hypothetical sampling variances. Zero tau² does not establish clinical homogeneity. No clinical prediction interval, I² or p-value is used to establish validity.

EXPLORATORY — uncertainty assumptions supplied by analyst; not validated pooled clinical accuracy.

## Diagnostic constrained joint model

All 96 prior diagnostic configurations are **rerun unchanged**: one Kenet table plus the Yu representative-fold table. Kenet variance inflation D=1/5/20; Yu inflation=1/5; five fixed between-source covariance choices give 90 scenarios. Six focused within-correlation alternatives (-0.5/+0.5 for both sources, Kenet D=5, Yu D=1, T05R0) give 96 total. Counts remain observed integers in their window/unresolved units, never invented effective patient samples.

For each table z_i=(log(TP/FN),log(FP/TN))', the sensitivity/FPR logits. S_i has diagonal D*(1/TP+1/FN) and D*(1/FP+1/TN), and covariance rho_within*sqrt(S11*S22). Primary within rho is zero. Between-source covariance T is **fixed, not estimated**:

| T | SD sensitivity | SD FPR | rho sensitivity/FPR | fixed covariance matrix |
| --- | --- | --- | --- | --- |
| T0 | 0.0 | 0.0 | 0.0 | [[0.0, 0.0], [0.0, 0.0]] |
| T05Rneg | 0.5 | 0.5 | -0.5 | [[0.25, -0.125], [-0.125, 0.25]] |
| T05R0 | 0.5 | 0.5 | 0.0 | [[0.25, 0.0], [0.0, 0.25]] |
| T05Rpos | 0.5 | 0.5 | 0.5 | [[0.25, 0.125], [0.125, 0.25]] |
| T1R0 | 1.0 | 1.0 | 0.0 | [[1.0, 0.0], [0.0, 1.0]] |


With V_i=S_i+T and P_i=V_i^(-1), GLS gives C=(sum P_i)^(-1), mu=C*sum(P_i*z_i). Sensitivity=expit(mu_1), specificity=expit(-mu_2). Marginal conditional 95% intervals transform normal limits using C; specificity reverses the FPR sign correctly. Joint confidence regions use chi-square(2,0.95) ellipses in logit coordinates, transformed to ROC space. They are not fitted HSROC curves or study prediction regions.

Positive covariance, normal-equation residuals and condition numbers are checked. The conditional residual quadratic has two residual degrees of freedom under known-assumed covariance; it does not empirically estimate T. With two paired sources, unrestricted covariance estimation remains unstable; the residual scatter has rank at most one. Parameter counting alone is not asserted as a structural-identifiability theorem. Sparse cells and large conditional residuals are recorded, not suppressed.

EXPLORATORY — clustered windows, unresolved analysis units and assumed statistical parameters.

## Reproduction

`make revised` rebuilds descriptive outputs, all 144 AUROC/96 diagnostic scenarios, comparisons and the LaTeX PDF, then runs the full tests and verifies hashes. `make exploratory` runs the scenario layer against already revised descriptive data; `make verify-exploratory` checks its provenance and outputs. Core forests are provided for 18 scenarios; all 126 alternatives are fully tabulated and plotted in a dedicated comparison. Runtime, versions, commands, failures and assumptions appear in execution manifests.
