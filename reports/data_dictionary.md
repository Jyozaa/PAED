# Data dictionary

Source CSV has 42 columns, two header records and multiline cells. Both exact header rows are preserved in `config/source_schema.json`; section labels are forward-filled only as metadata. Source row means **1-based logical CSV record including both headers**. Physical start/end line numbers are separately retained; these are not interchangeable.

## Source-to-analysis mapping

| source_column_index | section | original_column_name | analysis_field | publication_policy |
| --- | --- | --- | --- | --- |
| 0 | Basic information | Title  | title | whitelisted aggregate |
| 1 | Basic information | Full text URL  | full_text_url | whitelisted aggregate |
| 2 | Basic information | DOI | doi | whitelisted aggregate |
| 3 | Basic information | Study ID (First Author, Date) | study_label | whitelisted aggregate |
| 4 | Basic information | Authors | authors | withheld or separately curated |
| 5 | Basic information | Year  | year | whitelisted aggregate |
| 6 | Basic information | Country published  | country | whitelisted aggregate |
| 7 | Paper details | Study aim  | study_aim | whitelisted aggregate |
| 8 | Paper details | Study design | design | whitelisted aggregate |
| 9 | Paper details | Setting  | setting | whitelisted aggregate |
| 10 | Paper details | Recruitment period (dd/mm/yyyy) | recruitment | whitelisted aggregate |
| 11 | Population Characteristics | Mean/ median age  | age | whitelisted aggregate |
| 12 | Population Characteristics | Age group  <br>○Neonates (≤28 days) <br>○ Infants (29-365 days) <br>○ Children (1-18 years)  | age_groups | whitelisted aggregate |
| 13 | Population Characteristics | Sex (no. and % female) | sex | whitelisted aggregate |
| 14 | Population Characteristics | Sample size  | sample_size | whitelisted aggregate |
| 15 | Population Characteristics | Cardiac arrest prevalence | ca_prevalence | whitelisted aggregate |
| 16 | Population Characteristics | Underlying conditions <br>e.g. Congenital heart disease, Sepsis, Resp failure | conditions | whitelisted aggregate |
| 17 | Model characteristics | Model type <br>○ Logistic regression (baseline comparator) <br>○ Random forest <br>○ Neural network <br>○ Gradient boosting <br>○ Deep learning architectures | architecture_raw | whitelisted aggregate |
| 18 | Model characteristics | Input data modality: <br>- Vital signs<br>- ECG<br>- Labs<br>- Multimodal | modality_raw | whitelisted aggregate |
| 19 | Model characteristics | Feature selection method (if reported) | feature_selection | whitelisted aggregate |
| 20 | Model characteristics | Number of predictors | predictors | whitelisted aggregate |
| 21 | Model characteristics | Whether time-series data is used | time_series | whitelisted aggregate |
| 22 | Validation details | Internal validation, e.g. CV, bootstrapping | internal_validation | whitelisted aggregate |
| 23 | Validation details | External validation | external_validation_raw | whitelisted aggregate |
| 24 | Validation details | Training vs validation dataset sizes | split_sizes | whitelisted aggregate |
| 25 | Timing and clinical usability | Prediction lead time: E.g., 1h, 6h, 12h before arrest | lead_time_raw | withheld or separately curated |
| 26 | Timing and clinical usability | Outcome definition: <br>“Impending arrest” vs “actual arrest”  | outcome_raw | withheld or separately curated |
| 27 | Timing and clinical usability | Frequency of predictions (continuous vs snapshot)  | frequency_raw | whitelisted aggregate |
| 28 | Essential outcome data | True positives (TP) | tp_raw | whitelisted aggregate |
| 29 | Essential outcome data | False positives (FP) | fp_raw | whitelisted aggregate |
| 30 | Essential outcome data | False negatives (FN) | fn_raw | whitelisted aggregate |
| 31 | Essential outcome data | True negatives (TN) | tn_raw | whitelisted aggregate |
| 32 | Essential outcome data | Sensitivity | sensitivity_raw | whitelisted aggregate |
| 33 | Essential outcome data | Specificity | specificity_raw | whitelisted aggregate |
| 34 | Essential outcome data | AUROC | auroc_raw | whitelisted aggregate |
| 35 | Features used in Models | <br>Thematic analysis: <br>- Vital signs (HR, RR, BP, SpO2) <br>- Lab values <br>- Demographic (even if later excluded analytically) <br>- Clinical events | feature_themes_raw | withheld or separately curated |
| 36 | Secondary objectives | Comparator Data <br>Where available: <br>- PEWS <br>- Other monitoring systems <br> + their respective TP/FP/FN/TN, sensitivity, specificity, AUROC | comparator_raw | withheld or separately curated |
| 37 | Secondary objectives | Risk of bias/quality (QUADAS-2 inputs) <br>- Patient selection criteria <br>- Index test (ML model) <br>- Reference standard (definition of cardiac arrest) <br>- Flow and timing <br>Note: <br>- Missing data handling  <br>- Blinding (if any is blinded)  | raw_risk_of_bias | withheld or separately curated |
| 38 | Secondary objectives | Meta-regression: <br>Covariates: <br>- Mean/median age <br>-  % neonates <br>- Prevalence of cardiac arrest <br>- % congenital heart disease <br> For heterogeneity: <br>- Threshold used <br>- Data imbalance handling (oversampling, etc) <br>- Study setting differences | raw_meta_regression | withheld or separately curated |
| 39 | Other | Limitations of paper  | raw_limitations | withheld or separately curated |
| 40 | Other | Additional notes about the paper | additional_notes | withheld or separately curated |
| 41 | Other | Any assumptions made? | assumptions | withheld or separately curated |


## Derived fields and table schemas

Every generated result column, its observed data type, missing-value encoding and meaning is enumerated in [data_dictionary_derived.csv](../results/data_dictionary_derived.csv). This complements the original 42-field mapping. Public minimum aggregate records reside in `data/curated/source_rows.json`; no private notes are needed to rerun the analysis.

- `auroc` is discrimination on 0-1. `reported_variation` is the scaled +/- quantity, **not** a sampling standard error unless its type is established. Here it is unspecified.
- `se_raw_approx=(upper-lower)/(2*1.95996398454)`; `se_logit_approx=(logit(upper)-logit(lower))/(2*1.95996398454)` only for a labelled 95% CI with interior endpoints. Endpoint method and asymmetry remain limitations.
- Sensitivity = TP/(TP+FN); specificity = TN/(TN+FP); PPV = TP/(TP+FP); NPV = TN/(TN+FN); accuracy = (TP+TN)/N. Zero denominators yield missing, not zero.
- Proportions and percentages are 0-1; counts are nonnegative integers in their recorded **analysis unit**. Cohort patients, arrests and repeated windows have distinct denominators.
- Empty CSV cells mean unavailable. `missing_state` distinguishes missing, not_reported, not_applicable, ambiguous, observed_zero and observed. Raw missing markers are retained. A numeric 0 is genuine only when supplied or validly derived.
- `source_nonempty_cells` counts all nonempty cells in each original record; `nonempty_public_fields` counts a different, sanitized export and must not be interpreted as raw extraction completeness.
- `cohort_id` identifies a study-reported cohort; `dependency_group` conservatively groups probable overlaps. This does not assert the exact overlap fraction.
- `pooled_eligible=False` means the current evidence does not support inferential contribution; it is not a judgement that a model performs poorly.
- Rounding tolerance is 0.00055 for Kenet percentage comparisons (allowing effective 0.1 percentage-point rounding) and 0.005 for Yu 2023 integer percentages. Both reported and exact derived values remain available. No statistical test of these differences is implied.
- Lu correspondence-derived outcome/horizon text and free-text notes are withheld. `withheld` is not numerical missingness and does not constitute a public-source verification. Domain evidence summaries are analyst-curated from the extraction with column provenance, not independent full-text verification.
