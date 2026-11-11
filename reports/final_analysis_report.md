# AI prediction of paediatric cardiac arrest: statistical analysis of the supplied systematic-review extraction

Analysis reference date: 11 November 2026. Registered review: CRD420251241478. **Exploratory working cohort; not fully protocol-concordant.** This is a completed analysis of the supplied extraction, not a claim that a new comprehensive database search, full-text re-extraction or dual-reviewer systematic review has been completed.

## 1. Research question and objectives

How accurately do AI and machine-learning algorithms predict cardiac arrest in paediatric intensive care? Primary objectives were feasibility-tested random-effects AUROC synthesis and bivariate/HSROC sensitivity-specificity synthesis. Secondary objectives were descriptive comparisons of architecture, lead time, validation, ICU setting and input modality, with dependency, bias and clinical-use assessment.

AUROC is threshold-integrated ranking discrimination. Sensitivity is TP/(TP+FN) at an operating threshold; specificity is TN/(TN+FP). PPV is the fraction of positive predictions that are true positives in the evaluated sample. These are different estimands. The analysis unit must accompany each: repeated windows are not independent children or independent arrests.

## 2. Data sources and study eligibility

All three supplied sources were fully read: the 42-column CSV with two header records, the 3-page List of Variables, and 7-page PROSPERO snapshot version 3.0. Original files remain local; SHA-256 hashes are in the run manifest. Logical CSV record numbers include the two headers; physical line spans account for multiline cells. The public curated inputs contain only whitelisted aggregate facts, metric texts and source identifiers. Private correspondence content, raw PDFs/CSV, personal contact details and unpublished free-text notes are excluded.

The data contain **27 post-header records, six study reports and 26 populated model entries**. Record 21 contains a cross-reference rather than extracted numerical results. It points to the Yu 2022 logistic model in record 29. There are zero fully blank records. No original study full texts, raw patient data, independent reviewer forms, database search logs or full screening totals were supplied. Source study facts below are extraction-based and not independently reverified against full reports. Internet checks were restricted to methodological guidance, not additions to the included-study dataset.

## 3. Agreed exclusions and protocol discrepancies

All five Yu 2026 models were excluded because accuracy concerns composite adverse events rather than arrest alone. Yu 2023 Gaussian Naive Bayes was excluded because numerical results were not adequately extractable. The working cohort retains **five reports and 20 models**: Lu 2025 (11), Bose 2019 (1), Yu 2023 RDN Boost (1), Kenet 2023 (6), Yu 2022 (1).

PROSPERO restricts the population to under-18 cardiac ICU inpatients and excludes models without external validation. The team explicitly accepted general PICU, retaining Kenet. Its 38 adult participants create an additional unresolved eligibility issue. Lu and Bose explicitly lack external validation; none of the other reports demonstrates it in the extraction. Thus **zero studies/zero models demonstrate all strict criteria**. NR is not proof that validation never occurred, and no formal waiver or register amendment is claimed. Restriction to CICU setting alone leaves four reports/14 models. See [protocol deviations](protocol_deviations.md) for the registered wording, affected studies and required decisions.

## 4. Data cleaning and validation

The deterministic pipeline preserves grouped header metadata, source metric text and separate numerical fields. It standardizes percentages and proportions, semantically separates Bose training/test AUROCs, parses the labelled Yu 2023 CI, and retains unspecified +/- variation without treating it as SE or CI. Approximate distal Yu 2022 graphical ranges are not manufactured into hourly observations. Missing, not reported, not applicable, ambiguous and zero states are distinct; 1,134 source data-cell states are auditable. No missing value is set to zero and no 2x2 is reconstructed from rounded percentages.

Seven complete count tables are recalculated using standard formulas, with reported and count-derived values retained separately. One comparison exceeds the study-appropriate rounding tolerance: **Kenet random-forest specificity reported 77.8%, count-derived 77.5632%**. Yu 2023 integer percentages agree within rounding. Each numerical AUROC and count table retains study/model IDs, source record, DOI via the model table, metric source, horizon context, validation and dependency identifiers.

Yu 2022/2023 share institution, recruitment period (November 2010-January 2019), and 160 CA/711 control counts. They are conservatively assigned one potential dependency group. This does not determine exact overlap or permit their variances to be combined. Five reports therefore form at most **four potential independent cohort groups** under this working assumption.

## 5. Characteristics of included studies

All five reports describe retrospective single-centre US populations. Four are cardiac/cardiovascular ICU reports and one is general PICU. Samples vary from Bose's 64 analysed patients (20 held-out test patients, five CA) to Lu's 3,566 patients/4,672 admissions. Kenet has 1,145 retained patients (15 CA) after 1,019 exclusions, including 57 CA; test set is 229 patients with five CA. Both Dallas reports contain 160 cases and 711 controls, with probable patient reuse. The 18.37% Dallas selected-sample fraction is not a natural population incidence. These denominators cannot be summed as independent patient recruitment.

| study_id | models | unit |
| --- | --- | --- |
| lu_2025 | 11 | admission_with_patient_grouped_cv |
| bose_2019 | 1 | minute_risk_scores_patient_split_uncertainty |
| yu_2023 | 1 | representative_fold_table_unit_unverified |
| kenet_2023 | 6 | repeated_5_minute_window |
| yu_2022 | 1 | hourly_repeated_observations_validation_unreported |


[Full Table 1](table1_study_characteristics.html) includes age, sex, setting, outcome definitions, recruitment discrepancies, input modalities, architectures, training/validation, horizon/frequency, units and limitations. [Full Table 2](table2_model_performance.html) includes all 20 model results, original and recalculated performance, genuine CI, counts and available precision-recall metrics.

## 6. Descriptive predictive performance

There are **21 exact numerical AUROC evaluations from 20 models**, because Bose reports training 0.91 and held-out test 0.75. The 20 nontraining/other reported model evaluations span **0.5472-0.9710**. This is a descriptive minimum/maximum across heterogeneous dependent results; it is not a pooled estimate, confidence interval or cross-study architecture ranking. Lu's 11 AUROCs span 0.5472-0.7504; named index PEDCA-FT is 0.7399 with unspecified variation 0.0316, while gMLP is 0.7504 with unspecified variation 0.0352. Kenet AUROCs range 0.867-0.971 on repeated windows. Yu 2022 is 0.83 at the extracted 1-hour peak; Yu 2023 is 0.85 (95% CI 0.79-0.90) at 1 hour.

Sensitivity and specificity are numerically supplied for 11 retained models, with an additional entire-dataset specificity for Bose. Three Lu operating points are graph-read: XGBoost 39.04%/83.14%, gMLP 8.22%/97%, PEDCA-FT 42.47%/84.69%; they have unknown thresholds and no verifiable integer tables. These show why high AUROC need not mean high sensitivity at the chosen operating point.

Kenet XGBoost's table gives sensitivity **99.5261%**, specificity **69.5927%**, PPV **19.5167%** (210 TP, 866 FP, 1 FN, 1,982 TN). Soft voting gives sensitivity **90.9953%**, specificity **87.8862%**, PPV **35.7542%** (192 TP, 345 FP, 19 FN, 2,503 TN). The difference describes window-level threshold trade-offs in a shared sample; inferential paired comparisons are not possible without joint predictions. Six reported AUPRCs range 0.529-0.797; selected negative windows shape these precision/recall values and PPVs.

## 7. AUROC meta-analysis: methods, feasibility, results

**Status: Not statistically defensible from the supplied data.** Five reports/20 models supply 21 points; **one independent cohort supplies a labelled AUROC CI**. **Zero studies and zero model estimates contribute to a pooled fit.** Units and horizons are heterogeneous; the strict-protocol confirmed subset is empty.

The model-selection hierarchy prefers explicitly named/sole index models and appropriate independent validation, with no highest-AUROC rule. Kenet's representative-model decision is unresolved. Yu peak horizons are not treated as prospectively selected for cross-study synthesis. From Yu 2023's labelled CI, endpoint normal approximation yields SE 0.02806174 on AUROC scale and 0.22252939 on logit scale. Its CI construction is not established. Eleven unspecified Lu +/- quantities and narrative bootstrap descriptions cannot supply valid inverse-variance weights.

The guarded established-package route is REML `metafor::rma.uni` on logit AUROC with modified Hartung-Knapp t CI and back-transformation, but the eligibility gate stops before optimization. No mean is substituted, variance invented, or pooled diamond drawn. Tau-squared, I-squared, prediction interval and meta-analytic p-values are not estimable here. [Full AUROC feasibility assessment](auroc_feasibility.md) documents all checks.

## 8. Sensitivity/specificity meta-analysis: methods, feasibility, results

**Status: Not statistically defensible from the supplied data.** **Seven model tables from two study sources; zero confirmed eligible independent patient-level datasets; zero studies/model estimates in a pooled fit.** Six tables count repeated five-minute windows from the same Kenet sample; one Yu 2023 table is a representative fold with unresolved model attribution, threshold, horizon and unit. No clusters or patient-level data can be recovered from marginal aggregate counts.

All six Kenet tables total 3,059 windows (211 positive, 2,848 negative), not patients. Its test set has five CA patients. Yu 2023's table totals 218 units and recalculates to sensitivity 0.9000, specificity 0.646067, PPV 0.363636 and NPV 0.966387. This is not assumed to be a 1-hour operating point corresponding to its AUROC. No naive binomial confidence limits are calculated from windows or unresolved units.

The conditional bivariate implementation uses `mada::reitsma` with REML for independent interior proportions, with no unnecessary count correction. It requires explicit selection and comparability confirmation and a conservative minimum of five independent datasets; binomial HSROC would be needed for sparse boundary data. Even an optimistic two-study fit cannot reliably characterize the full random-effects covariance here, and its underlying unit/linkage assumptions fail first. No model convergence, pooled sensitivity/specificity or fitted summary ROC is claimed. [Full diagnostic feasibility assessment](diagnostic_feasibility.md) includes all validated matrices.

## 9. Heterogeneity and sensitivity analyses

The pairwise matrix examines all 10 report pairs. ICU mix, age, disease spectrum, arrest definitions, case/control selection, input representation, lead time, model selection, validation and sampling unit vary substantially. Mean warning time (Bose), first-24h input (Lu), fixed extracted pre-arrest peak points (Yu) and within-3h positive windows (Kenet) represent different targets. Thematic inputs include vitals, ECG/HRV, labs, NIRS, medication and demographic context, with no universal shared variable set.

The exploratory cohort is compared with CICU-only (four reports/14 models) and strict demonstrated-eligibility (zero) subsets; neither supports pooling. Potential Dallas reuse prevents independent treatment of Yu 2022/2023. No meta-regression, quantitative subgroup fitting, leave-one-out, Egger regression, funnel-asymmetry test or unstable heterogeneity statistic is performed. See [heterogeneity report](heterogeneity.md) and matrix CSV.

## 10. Risk of bias and certainty

Twenty QUADAS-2 domain evidence records and applicability prompts were prepared. All formal judgements remain pending independent reviewer assessment. Concerns needing review include spectrum selection, large missing-data exclusions, sparse events, threshold/model selection, differential time anchoring, repeated observations, model leakage and validation. Reported detail is not proof of low risk, and missing detail is not proof of high risk. [PROBAST+AI](https://www.bmj.com/content/388/bmj-2024-082505) may be a useful additional prediction-model-specific framework; it has not replaced the registered QUADAS-2 tool.

Adapted GRADE domains are documented without an unsupported final grade. Bias, indirectness, precision and inconsistency cannot be resolved by apparently high AUROC. Search/reporting-bias evidence is incomplete. No software-based claim of independent dual review is made. See [risk-of-bias report](risk_of_bias.md) and [certainty worksheet](certainty_of_evidence.md).

## 11. Clinical interpretation

These studies suggest discriminatory signal in selected retrospective data, while documenting substantial operating-point trade-offs. Kenet's high sensitivity concerns positive five-minute windows, not the proportion of children whose arrests were successfully anticipated. A false-positive window is not automatically a distinct clinical alarm. The negative-window sampling scheme, alarm suppression, treatment actions and prospective CA incidence affect actual workload and PPV. Selected case-control or window PPVs cannot be transported directly to an unselected ICU population.

No evidence here establishes calibration, acceptable alarms per patient-day, clinical net benefit, prospective prevention of arrests, improved survival or safe deployment. External and prospective evaluation at clinically useful horizons, with patient/cluster-aware uncertainty and explicit thresholds, is required to assess clinical usability.

## 12. Limitations

This is analysis of a supplied aggregate extraction, with no independently verified original full texts, IPD, complete search/screening logs or full protocol. Extraction assumptions and graphical readings are traceable but remain uncertain. Private correspondence is withheld rather than treated as public corroboration. Only one genuine AUROC CI exists; eleven variability quantities are unspecified. Multiple models/horizons and probable cohort reuse create dependency. Seven tables do not yield seven independent studies. Kenet clustering, five test CA patients and adult participants limit interpretation; positive-window counts also need reconciliation with event multiplicity and the three-hour labeling rule; Yu 2023 linkage is unresolved. Case/control and negative-window sampling affect transportability; bias/certainty assessment remains incomplete. Conditional R fitting code is provided, but no ineligible inferential model was run or validated as a current result.

## 13. Evidence-based conclusion

**Neither planned inferential meta-analysis is statistically defensible from the supplied evidence.** The completed descriptive synthesis retains five reports and 20 models, preserves 21 AUROC evaluations, one genuine CI and seven complete candidate diagnostic tables, and explains their provenance, dependency and limitations. These data cannot establish a universal AUROC, sensitivity/specificity pair, architecture winner or clinical readiness. This is a feasibility outcome, not a technical model-fitting failure or evidence that all AI prediction is ineffective.

## 14. Outstanding questions for the review team

1. Confirm/document the scope broadening to general PICU and decide how to handle Kenet's 38 adults; obtain paediatric-only performance if needed.
2. Resolve the registered external-validation requirement through additional evidence or an explicit documented methodological decision; no waiver is presumed.
3. Verify all included-study facts against public full reports, especially Lu outcome/target interval, graphical operating points and +/- definition; keep private correspondence private.
4. Confirm Dallas patient overlap and evaluation independence, including whether comparator estimates are reused.
5. Obtain genuine AUROC SEs/CIs and their construction; do not use fold SD as sampling SE without justification.
6. Confirm Yu 2023's table model, threshold, fold, horizon and unit; reconcile its 40 positive units with cohort/fold descriptions without reconstruction assumptions.
7. Obtain patient-level or cluster-adjusted Kenet diagnostic estimates and prospective alarm-rate denominators; confirm model selection without choosing observed maxima.
8. Reconcile recruitment-date discrepancies, model-specific quality templates and random-forest specificity; resolve exact horizon selection before pooling.
9. Supply search strategy/screening counts and complete independent QUADAS-2/adapted GRADE assessments with consensus.

## 15. Reproducibility information

The command `make all` rebuilds curated-data analyses, CSV tables, figures, Markdown/HTML reports and the run manifest, then runs the full test suite and verifies output completeness. `make raw` re-ingests all three local originals and regenerates the public curated data. Python source separates ingestion, semantic cleaning, feasibility/independence checks, figures and reporting. Conditional R code has its own early eligibility gates and is not needed to reproduce the current no-pooling findings.

Input SHA-256 hashes, software versions, counts, configuration, analysis status, warnings, output hashes, actual commands, execution timestamps, test results and the available source Git revision are in `run_manifest.json`. Public-only reproduction cannot prove fidelity of withheld originals; original-source audit requires local source files. Re-running numerical tables/figures is deterministic; execution timestamps, test duration and source Git metadata naturally change. The manifest Git SHA identifies the source revision at run time, not a claim of containing its own future publication-commit hash.

## Descriptive figures

![AUROC estimates](../figures/auroc_descriptive.png)

![Sensitivity points](../figures/sensitivity_descriptive.png)

![Specificity points](../figures/specificity_descriptive.png)

![ROC-space scatter](../figures/sroc_descriptive.png)

![Comparability overview](../figures/heterogeneity_overview.png)

![Dataset flow](../figures/inclusion_flow.png)

See [full captions](figure_captions.md); all plots are descriptive and no pooled-estimate figure is implied.

## Methodological references

- [Takwoingi et al., performance of diagnostic accuracy meta-analysis with few studies/sparse data](https://pmc.ncbi.nlm.nih.gov/articles/PMC5564999/) supports caution about complex hierarchical fitting in small syntheses; it does not validate pooling the current clustered tables.
- [Cochrane DTA handbook, Chapter 10](https://methods.cochrane.org/sites/methods.cochrane.org.sdt/files/uploads/Chapter%2010%20-%20Version%201.0.pdf) describes bivariate/HSROC models and restrictions on heterogeneity exploration.
- [PROBAST+AI original tool publication](https://www.bmj.com/content/388/bmj-2024-082505) supports considering a prediction-model-specific assessment in addition to the registered tool.
- [metafor package author documentation](https://wviechtb.github.io/metafor/reference/rma.uni.html) and [mada package documentation](https://rdrr.io/cran/mada/man/reitsma.html) define the conditional estimators. Methods sources were checked online; included-study metrics remain based exclusively on supplied extraction.
