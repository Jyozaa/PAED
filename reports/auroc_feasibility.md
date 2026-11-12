# AUROC synthesis: revised evidence feasibility

**Confirmatory status: not statistically defensible from the supplied evidence.** 5 reports/17 models supply 18 AUROC evaluations, but just one cohort has genuine numerical uncertainty. The 8 retained Lu +/- values are unspecified, not SEs. No confirmatory pooled AUROC, CI, p-value, tau-squared, I-squared or prediction interval is produced.

The descriptive nontraining/other reported range is 0.5472-0.9710; Lu's 8 retained values span **0.5472-0.7329**. Bose training 0.91 and held-out test 0.75 remain separate. Yu 2023 is 0.85 (95% CI 0.79-0.90); approximate SE is 0.02806174 on AUROC scale and 0.22252939 on logit scale. The CI construction is unverified.

| study_id | representative_model | selection_reason | genuine_variance_estimates | reason |
| --- | --- | --- | --- | --- |
| lu_2025 | lu_2025_logistic | Analyst-selected conventional logistic-regression baseline after whole-entry team exclusion of the named index model; not an original verified primary-model designation | 0 | No usable genuine AUROC variance |
| bose_2019 | bose_2019_glm | Single model; select held-out test AUROC, retain training AUROC descriptively | 0 | No usable genuine AUROC variance |
| yu_2023 | yu_2023_rdn_boost | Named index RDN Boost; numerical AUROC at extracted 1h peak, not chosen by cross-model ranking | 1 | Only one variance-bearing cohort in entire dataset |
| kenet_2023 | selection_required | XGBoost called best based on performance; no clearly prospectively designated primary model, so do not automatically select it | 0 | No usable genuine AUROC variance |
| yu_2022 | yu_2022_logistic | Single multivariable model; validation unclear and potential overlap blocks pooling alongside Yu 2023 | 0 | No usable genuine AUROC variance |


Lu logistic regression is now the analyst-selected conventional representative after the whole-model exclusions. Its AUROC is 0.6292, with unspecified +/- 0.0192. This is not the original paper's verified primary-model designation. No highest-AUROC selection rule is used. Yu 2022/2023 potentially share the same Dallas cohort; horizons, units, definitions and validation differ. Bootstrap narrative does not provide missing numerical AUROC uncertainty. Conventional inverse-variance pooling remains unsupported.

The separately labelled exploratory scenario layer adds hypothetical SEs and fits Paule-Mandel random effects with modified Hartung-Knapp conditional intervals. Those calculations do not change this confirmatory conclusion. They use one model per source group and never combine the Dallas reports. See [revised exploratory report](exploratory/consolidated_exploratory_report.md).
