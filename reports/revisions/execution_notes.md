# Published revision execution record

This records the validated original-source run for the 17-model revision. It is a historical execution note; the machine-readable manifests are regenerated on subsequent runs.

## Exact commands

```bash
.venv/bin/python scripts/version_revision_baseline.py
make revised-raw
make verify-revised
make verify
make verify-exploratory
git diff --check
.venv/bin/python scripts/check_publication.py --staged
```

`make revised-raw` expands to `.venv/bin/python scripts/run_revision.py --input-dir . --run-tests`. The runner executes the complete descriptive, AUROC, diagnostic, comparison and LaTeX/PDF stages, then `python -m pytest -q` using the same Python interpreter. Public-only reproduction uses `make revised`; the originals are not published.

## Recorded environment and results

- Python 3.14.7; numpy 2.5.4, pandas 3.1.1, scipy 1.18.1, statsmodels 0.15.0, matplotlib 3.11.2, Markdown 3.11.3, pytest 9.2.0; pypdf 7.0.1; Tectonic 0.17.0.
- All three original files verified in this invocation: True. Original SHA256 values remain in `config/revision.json` and all execution manifests.
- Original extraction: six reports, 26 populated model entries and one cross-reference. Revised inclusion: five reports, 17 models, including eight Lu models.
- AUROC: 18 core and 126 additional Lu-choice scenarios; 144 accepted final estimates, zero failed final scenarios.
- Diagnostic: 96 accepted scenarios; all numerical columns equal to the saved parent, maximum absolute difference zero. Source tables, input ledger, result CSV and both diagnostic PNG/SVG figures are byte-identical to the parent.
- Automated tests: 68 passed in 36.84s. Complete builds in isolated output directories require identical scientific tables, reports, figures and PDF bytes.
- Final verifiers: 11 revision checks, eight descriptive checks and eight exploratory checks, plus all recorded file hashes.
- PDF: three pages; all rendered pages visually inspected. No overflow/missing-character warnings, only the revised AUROC figure, and all four contributors identified in the core scenario table.

## Numerical warnings and unresolved evidence limits

Eleven library Paule–Mandel attempts failed the estimating-equation residual check. The recorded bracketed-root fallback solved the identical equation with unchanged inputs; all final estimates passed residual checks. There were 155 AUROC numerical attempts for 144 final scenarios. Both the rejected and accepted attempts remain in `results/exploratory/fit_attempts.csv`.

All 96 diagnostic scenarios carry sparse-cell normal-logit approximation warnings; eight also have large conditional residual discrepancy under the assumed covariance. No unrestricted bivariate covariance or HSROC was estimated. Missing SEs, design effects and covariance assumptions remain hypothetical. Clustering, adults in Kenet, possible Dallas overlap, unresolved Yu linkage/units, differing horizons and absent demonstrated external validation remain unresolved. Confirmatory pooling remains unsupported.

## Execution issues resolved before publication

Initial isolated-output checks identified a missing comparison-report directory and a link test that built only the descriptive stage; both were corrected while preserving complete link/schema checks. A subsequent final verifier encountered cloud-sync duplicate placeholders with filesystem read timeouts. Those untracked duplicate artifacts were preserved locally in an ignored quarantine directory; analytical artifacts were unchanged. The final complete original-source execution returned success and passed all tests and verifiers.

## Provenance

Parent analysis: `38815dec5fa9d5d67c895739fa27a0a33dc8d88d` on `exploratory-pooling`. The old 67-file integrity record is validated against historical Git; the revised 76-file scientific baseline is separately enforced. Original/curated sources remain immutable. The execution manifest refers to the Git revision present while running, which precedes the future publication commit containing that manifest.
