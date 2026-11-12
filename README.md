# Paediatric cardiac arrest prediction: revised evidence synthesis

The current revision excludes Lu 2025 XGBoost, gMLP and PEDCA-FT in full following the research team's decision that their graphically extracted sensitivity/specificity was insufficiently reliable. This does not imply that their AUROCs were graph-derived. Other Lu models remain eligible despite missing operating points.

| Result | Previous analysis | Revised analysis |
| --- | --- | --- |
| Retained study reports | 5 | 5 |
| Retained models | 20 | 17 |
| Lu models | 11 | 8 |
| Retained Lu reported AUROC | 0.5472–0.7504 | 0.5472–0.7329 |
| Core conditional pooled AUROC range | 0.7689–0.8451 | 0.7241–0.8305 |
| AUROC scenarios | 18 | 18 core + 126 other Lu choices |
| All revised conditional pooled AUROC scenarios | Not assessed | 0.7120–0.8441 |
| Diagnostic scenarios | 96 | 96; numerically identical |
| Conditional pooled sensitivity range | 87.30–98.24% | Unchanged |
| Conditional pooled specificity range | 65.60–87.50% | Unchanged |

Ranges are spreads across assumption-dependent scenarios, not confidence intervals. The original CSV contains six reports, 26 populated model entries and one cross-reference. Previous exclusions remain five Yu 2026 composite-outcome models and Yu 2023 Gaussian Naive Bayes with graphical results. Original input files and curated source records are unchanged.

Read the [descriptive report](reports/final_analysis_report.md), [complete exploratory report](reports/exploratory/consolidated_exploratory_report.md), [before-and-after comparison](reports/revisions/exclusion_comparison.md), and [short compiled report](output/pdf/short_report.pdf). LaTeX is in [reports/short_report.tex](reports/short_report.tex). Styled HTML versions accompany the Markdown reports.

## Reproduce the complete revision

Use a full clone: integrity checks require the original historical Git commits. Tested with Python 3.14.7; code requires Python >=3.11 and compatible dependency wheels. Exact Python dependency versions are pinned in `requirements.txt`. Install Tectonic for LaTeX compilation; this run used Tectonic 0.17.0 (`brew install tectonic` on macOS). Its first invocation downloads the standard TeX bundle.

```bash
git clone --branch exclude-graph-derived-lu-models https://github.com/Jyozaa/PAED.git
cd PAED
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
make revised
make verify-revised
```

Equivalent complete commands:

```bash
.venv/bin/python scripts/run_revision.py --run-tests
.venv/bin/python scripts/verify_revision.py
```

This runs descriptive analysis, all 144 AUROC scenarios, all 96 diagnostic scenarios, comparisons with saved results, compact AUROC rendering, LaTeX compilation, the full test suite and manifest verification. Tests rebuild the complete analysis twice in fresh directories and require identical scientific artifacts, reports, figures and PDF bytes. Execution timestamps, test durations and Git metadata are intentionally run-specific. Tests do not recursively invoke themselves. No R installation is required.

Individual stages remain available as `make all`, `make exploratory`, `make short-report`, `make verify` and `make verify-exploratory`. For publication or full reproducibility, use `make revised` because the final report links outputs from all stages. `scripts/meta_analysis.R` retains the original guarded confirmatory routes and exits without fitting on these scientifically ineligible inputs; it is separate from the executed exploratory methods.

## Recheck the original input files locally

Only the supplied extraction CSV, `List of Variables.pdf` and `PROSPERO.pdf` were used. No new clinical sources were retrieved. The original files are not committed. Place them beneath a local source directory with their original basenames and run:

```bash
.venv/bin/python scripts/run_revision.py --input-dir /path/to/local/sources --run-tests
make verify-revised
```

With the originals in the repository root, `make revised-raw` runs this audit. Input discovery rejects duplicate matching names. Ingestion preserves logical CSV records, physical multiline spans, both source headers, metric text and missingness. Private notes and correspondence-derived text remain withheld. Public reproduction uses existing sanitized aggregate records and cannot independently recheck fidelity to confidential originals. `raw_sources_verified_this_run` distinguishes these modes; the three original SHA256 hashes are retained in all manifests.

## Statistical methods and limits

The 18 core AUROC scenarios select Lu logistic regression (0.6292), Bose's held-out test GLM (0.7500), either Yu 2023 RDN Boost (0.8500, genuine CI 0.79–0.90) or Yu 2022 logistic regression (0.8300), and one Kenet model: logistic (0.8670), XGBoost (0.9710) or soft voting (0.9570). Lu logistic is an analyst-selected conventional baseline, not a verified original primary-model designation. Each of the other seven retained Lu algorithms is crossed with those same 18 configurations, with one representative per source group.

AUROC uses Paule–Mandel random effects on logits and modified Hartung–Knapp t intervals. Missing original-scale SEs are assumed to be 0.02, 0.04 or 0.08; genuine Yu 2023 uncertainty is retained. Lu's unspecified ± values are never treated as SEs. A checked bracketed-root solution of the same Paule–Mandel equation replaces 11 rejected library numerical attempts without changing inputs or estimator. All attempts and warnings remain recorded.

Diagnostic pooling uses unchanged Yu 2023 and Kenet confusion matrices. Each scenario solves joint normal-logit GLS with prespecified between-source covariance, within-source correlation and variance inflation. It does not estimate unrestricted bivariate heterogeneity or fit HSROC. Design effects are illustrative assumptions, not empirically estimated corrections. All 96 result rows, input ledger and both diagnostic figures (PNG/SVG) reproduce the previous branch byte for byte.

Confirmatory pooling remains unsupported: only one genuine AUROC CI is available; Kenet counts repeated five-minute windows and includes 38 adults; Yu 2023's representative-fold linkage/unit is unresolved; Yu 2022 and Yu 2023 may overlap; horizons and thresholds differ; external validation is unverified. The general-PICU scope exceeds strict PROSPERO cardiac-ICU criteria. Risk-of-bias and certainty assessments remain pending independent reviewers. These calculations cannot establish clinical deployment safety, calibration, alarm burden or patient-level missed arrests.

## Provenance and outputs

- `config/revision.json`: exact team exclusion reason, original input hashes and saved-parent references.
- `config/baselines/analysis_20_model_integrity.json`: previous 67-file integrity record, checked against its historical Git tree.
- `config/exploratory_baseline_hashes.json`: revised 76-file scientific baseline. Original curated/source hashes remain enforced; it is never silently refreshed on rerun.
- `data/history/analysis_20_models/`: immutable saved public aggregate results used for comparisons and checked against parent commit `38815dec5fa9d5d67c895739fa27a0a33dc8d88d`.
- `results/`: revised inventories, exclusions, metrics, tables, feasibility decisions and data dictionaries.
- `results/exploratory/`: 144 AUROC results and contributor ledgers, 96 diagnostic results and ledgers, attempts, assumptions, comparisons and Lu-choice sensitivities.
- `figures/`: descriptive figures and compact report AUROC, PNG/SVG.
- `figures/exploratory/`: 18 core forests, core and Lu-choice sensitivity figures, unchanged diagnostic figures.
- `reports/`, `reports/exploratory/`, `reports/revisions/`: Markdown/HTML reports and LaTeX source.
- `output/pdf/`: compiled three-page report and PDF build manifest.
- `results/revisions/run_manifest.json`: complete revision verification, versions, commands, hashes, tests and warnings; component manifests remain at `run_manifest.json` and `results/exploratory/run_manifest.json`.

The `exploratory-pooling` branch preserves the previous 20-model analysis. Publication does not overwrite it. The manifest's source Git SHA identifies the revision available during execution; a commit containing the manifest cannot record its own future hash.

Only sanitized aggregate data and derived outputs are published. `scripts/check_publication.py --staged` checks staged filenames and text for original private inputs, correspondence, contact information and credentials. No patient-level records are included.
