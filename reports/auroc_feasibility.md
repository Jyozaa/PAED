# Analysis A: AUROC random-effects synthesis

**Status: Not statistically defensible from the supplied data.** The feasibility workflow completed; no inferential fit was attempted after failed eligibility checks. No pooled AUROC, p-value, tau-squared, I-squared or prediction interval exists.

## Estimand and selection

An exploratory pooled logit AUROC across different algorithms would describe discrimination of selected, validated model estimates in comparable paediatric CA cohorts at comparable horizons. It would not estimate a single deployable AI tool, detection sensitivity, or the fraction of preventable arrests.

Hierarchy is recorded in `config/analysis.json` before the fitting stage: explicitly named index model or sole model; external validation preferred, then patient-disjoint test, then patient-grouped CV; separate horizons; one estimate per independent cohort. No automatic maximum-AUROC rule is used. Lu's PEDCA-FT is the named index tool even though gMLP has higher AUROC. Kenet's performance-selected “best” XGBoost is not automatically designated the primary model. Extracted 1-hour peaks in Yu reports are retained descriptively, not represented as prespecified cross-study endpoints.

| study_id | representative_model | selection_reason | genuine_variance_estimates | reason |
| --- | --- | --- | --- | --- |
| lu_2025 | lu_2025_pedca_ft | Named index tool PEDCA-FT in study aim, despite gMLP having higher AUROC | 0 | No usable genuine AUROC variance |
| bose_2019 | bose_2019_glm | Single model; select held-out test AUROC, retain training AUROC descriptively | 0 | No usable genuine AUROC variance |
| yu_2023 | yu_2023_rdn_boost | Named index RDN Boost; numerical AUROC at extracted 1h peak, not chosen by cross-model ranking | 1 | Only one variance-bearing cohort in entire dataset |
| kenet_2023 | selection_required | XGBoost called best based on performance; no clearly prospectively designated primary model, so do not automatically select it | 0 | No usable genuine AUROC variance |
| yu_2022 | yu_2022_logistic | Single multivariable model; validation unclear and potential overlap blocks pooling alongside Yu 2023 | 0 | No usable genuine AUROC variance |


## Actual evidence and variance

Five study reports / 20 models / 21 numerical evaluations, including Bose training (0.91) and held-out test (0.75). Twenty nontraining/other reported model points range **0.5472-0.9710**; these are descriptive extremes, not a pooled range or CI. AUROC evaluation units differ: admission with patient-grouped CV (Lu), minute scores with patient split (Bose), representative/hourly EHR contexts (Yu), and repeated five-minute windows (Kenet). Four conservative potential dependency groups exist; exact between-study overlap is unverified.

Only Yu 2023 RDN Boost at the extracted 1-hour peak has a genuine CI: **0.85 (95% CI 0.79-0.90)**. The endpoint approximation gives original-scale SE **0.02806174**, logit-scale SE **0.22252939**. The CI construction and the assumptions behind logit normality are not supplied, so even this variance would need methodological verification for pooling. Eleven Lu +/- values have unspecified statistical meaning; 73.29 +/- 2.47 becomes estimate 0.7329 and unspecified variation 0.0247, never SE. Fold variation would not automatically be independent sampling error because CV training sets overlap. Bose describes bootstrap uncertainty, but numerical AUROC limits/SE are absent in the extraction. Kenet and Yu 2022 have no usable AUROC variance.

## Feasibility checks and conditional model

Only **one variance-bearing independent cohort** is available; clinical/validation/horizon comparability is not established; Yu 2022/2023 may reuse the same 160 CA and 711 control patients in Dallas during 2010-2019. There are **0 contributing studies / 0 model estimates in a fitted meta-analysis**. Missing variance is not approximated from AUROC alone or from unrelated patient denominators.

The conditional R workflow `scripts/meta_analysis.R` uses established `metafor::rma.uni`, REML on logit AUROC and a modified Hartung-Knapp interval (t critical value; variance scale bounded below by the conventional inverse-information variance). It requires at least three independent, explicitly selected comparable estimates, usable genuine logit SEs and no duplicated dependency groups. This is a conservative project safeguard, not a universal sample-size rule. An eligibility-authorized fit would back-transform the estimate/CI, report tau-squared on logit scale, record session information and save its genuine forest plot. Current input stops before fitting. This future fitting route is not claimed as empirically validated on the supplied evidence.

No variance-imputation sensitivity analysis, leave-one-out, subgroup model, meta-regression, funnel test, Egger regression, prediction interval or heterogeneity statistic is scientifically supported. Raw AUROC and genuine CI plots remain available without a summary diamond. See [metafor documentation](https://wviechtb.github.io/metafor/reference/rma.uni.html) for the underlying estimator.
