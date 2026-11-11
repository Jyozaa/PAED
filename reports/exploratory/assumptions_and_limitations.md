# EXPLORATORY: assumptions and limitations

The supplied extraction is authoritative for this task and has not been independently verified against original papers. No new studies, external confidence intervals, author correspondence or patient-level records were consulted. Reported source values are unchanged. Original confirmatory feasibility conclusions and descriptive outputs are preserved. The numbers here are **conditional pooled calculations**, not the primary evidence-supported findings or established clinical accuracy.

## Assumptions introduced for AUROC

EXPLORATORY — uncertainty assumptions supplied by analyst; not validated pooled clinical accuracy.

Select exactly four source groups: named Lu PEDCA-FT, Bose held-out GLM, one Dallas report and one Kenet algorithm. Kenet logistic regression is an analyst-selected conventional baseline, not a claim it was the original study's primary model. XGBoost and soft voting are separately assessed; all alternatives are reported. Yu 2022 replaces Yu 2023, never accompanies it. Selection is not optimized for a favourable pooled result. First-hour Yu peaks, varying warning times and other forecast contexts are not equivalent endpoints.

Only Yu 2023 provides a labelled AUROC 95% CI. All other missing SEs are hypothetical 0.02/0.04/0.08 on original AUROC scale. These ranges are illustrative, not empirically calibrated or exhaustive bounds. Lu's +/- value is never used as sampling SE. Its meaning remains unknown. Delta transformation can magnify a fixed original-scale SE near AUROC=1; this is mathematically expected and makes model weights assumption-dependent. The normal-logit approximation is not validated by these files. Conditional intervals do not include uncertainty about the chosen SE assumptions, cohort independence or selection.

## Assumptions introduced for diagnostic summaries

EXPLORATORY — clustered windows, unresolved analysis units and assumed statistical parameters.

Exactly two source summaries are used per scenario: one Kenet model and the Yu 2023 table. They are assumed mutually independent for calculation. Within-source sampling covariance is based on normal-logit delta approximations and explicit design-effect/correlation assumptions; the counts are not converted to observed effective patient samples. Kenet design effects 1/5/20 and Yu multipliers 1/5 are analyst assumptions, not measured ICCs or corrections known to be adequate. Scaling Yu variance probes sensitivity to uncertainty but cannot identify its counted unit, model, fold, horizon or threshold. Classification thresholds differ or are unknown.

The between-source covariance T is fixed at the configured values, not estimated. The joint normal GLS mean and its conditional covariance can be computed with two sources under that constraint. This is **not** an unrestricted fitted bivariate random-effects model or fitted HSROC. Normal-logit variances are particularly uncertain with sparse cells: Yu has FN=4, Kenet XGBoost FN=1. Known-assumed-covariance normal intervals and joint confidence ellipses exclude uncertainty about covariance parameters, source-data validity and the original selection process. No distribution of future clinical accuracy is inferred.

## Inherent source restrictions

Kenet matrices count repeated five-minute windows (3,059 per table, 211 positive), not independent patients/arrests. The test cohort contains 229 patients with five CA patients. Positive windows exceed 180 under an unstated one-arrest-per-patient assumption and three-hour/five-minute labeling rule; event multiplicity/labeling remain unresolved. Its whole cohort includes 38 adults; no paediatric-only accuracy is available. General PICU is team-agreed but broader than registered CICU eligibility. None of the retained reports demonstrates all strict protocol criteria, including external validation. Formal eligibility amendments, QUADAS-2 and adapted GRADE decisions are not supplied or presumed.

Yu 2022/2023 probably overlap by institution, period and 160 CA/711 controls, and are never independent contributors to the same scenario. Missing AUROC uncertainty, internal-only or unreported validation, selected controls/negative windows and heterogeneous inputs/outcomes remain. No original-paper verification is possible in this task. Private source narratives remain withheld. The original five-report/20-model inventory and exclusions remain intact.

## Interpretation boundaries

Pooled AUROC is the back-transformed mean of selected AUROC logits under assumed variances and random effects. It is not one tool's discrimination, a newly measured study AUROC, or sensitivity. Diagnostic summaries are back-transformed GLS mean logits for mixed-unit, different-threshold source summaries; they do not measure a common clinically validated operating point. A transformed mean logit is not generally the arithmetic mean probability over a random-effects distribution.

Differences across scenarios quantify **assumption sensitivity**, not sampling CIs, effectiveness comparisons or validation. Stable digits cannot resolve bias, indirectness, wrong units, unmeasured clustering or absent external validation. No clinical deployment or safety recommendation follows. Actual false alarms per patient-day, missed children, calibration, net benefit and improved outcomes cannot be inferred.
