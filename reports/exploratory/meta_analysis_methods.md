# EXPLORATORY: meta-analysis methods

The supplied extraction is authoritative for this task and has not been independently verified against original papers. No new studies, external confidence intervals, author correspondence or patient-level records were consulted. Reported source values are unchanged. Original confirmatory feasibility conclusions and descriptive outputs are preserved. The numbers here are **conditional pooled calculations**, not the primary evidence-supported findings or established clinical accuracy.

## Scope, selections and provenance

Working extraction: five reports/20 models with Yu 2026 and Yu 2023 Gaussian Naive Bayes excluded. Computations read only the existing AUROC and diagnostic CSVs plus explicit configuration, retaining source record, model, cohort/dependency identifier and units in every ledger. The baseline hashes protect 67 original scientific/configuration/data files. Original execution metadata may change only on an intentional original-pipeline rerun; this extension does not rewrite it.

AUROC factorial: 2 mutually exclusive Dallas reports x 3 Kenet choices x 3 assumed missing SEs = 18 scenarios. Fixed choices are Lu PEDCA-FT and Bose **held-out** test. Default selection is Yu 2023 plus Kenet logistic regression, reported at all three SE assumptions; no single assumption is called empirical truth. Clinical independence between four conservative source groups is assumed, not established.

Diagnostic factorial: 3 Kenet choices x 3 Kenet design effects x 2 Yu inflation factors x 5 fixed T specifications = 90 scenarios. Six additional focused within-source-correlation variants (3 models x 2 correlations) give 96 total. No scenario contains multiple Kenet algorithms as separate sources.

## AUROC normal random-effects model

For source i, y_i=logit(AUC_i). The conditional model is y_i ~ N(mu, v_i+tau²). For genuinely labelled Yu 2023 CI, use the existing endpoint approximation SE_logit=[logit(0.90)-logit(0.79)]/(2*1.95996398454)=0.22252939; CI construction is still unverified. For missing uncertainty, set original-scale SE=s in {0.02,0.04,0.08} and use delta SE_logit=s/[p(1-p)]. These are explicitly **assumed**, not extracted SEs or reconstructed confidence limits.

The installed primary implementation is `statsmodels.stats.meta_analysis.combine_effects(method_re="iterated")`, **Paule–Mandel**, not REML. Its installed source documents checks against metafor; it was inspected locally and is independently tested here against equal-variance analytic and unequal-variance bracketed-root solutions using synthetic numerical examples (no new clinical data). The PM estimate solves sum[w_i(tau²)*(y_i-mu_w)²]=k-1 if Q(0)>k-1, otherwise tau²=0. We verify that equation or boundary inequality for every fit. Maximum iterations=1000, equation tolerance=1e-07.

If a library iteration fails the equation check, preserve the failure and solve the **same PM equation** by configured SciPy `brentq` bracketing. This changes the numerical solver only, not source values, estimator or assumptions. A failed fallback yields no pooled result. All attempts, including unsuccessful initial attempts, are in `fit_attempts.csv`.

Weights are 1/(v_i+tau²). Conditional pooled logit mu=sum(w_i*y_i)/sum(w_i). Modified Hartung–Knapp variance=max[1/sum(w_i), Q(tau²)/((k-1)*sum(w_i))], using t critical value with k-1=3 degrees of freedom. Transform mu and interval endpoints by expit. This scale floor prevents the H-K adjustment narrowing below the conventional variance at a zero-heterogeneity boundary. Report tau² on **logit** scale, Q, root residual, boundary status, weights, warnings and solver. No I², clinical prediction interval or p-value is used to claim validity.

EXPLORATORY — uncertainty assumptions supplied by analyst; not validated pooled clinical accuracy.

## Joint diagnostic normal-logit model with fixed heterogeneity

For each unchanged table, z_i=(log(TP/FN), log(FP/TN))'=(logit sensitivity, logit FPR)'. Within covariance S_i has diagonal D_i*(1/TP+1/FN) and D_i*(1/FP+1/TN). Its off-diagonal is rho_within*sqrt(S11*S22), with primary rho_within=0 and focused alternatives -0.5/+0.5 for both sources. D_Kenet=1/5/20; D_Yu=1/5. Disjoint-class binomial independence motivates the naive zero correlation, but repeated patients can link both outcomes; all these covariances are assumptions. Counts are never divided, rounded or replaced by effective counts.

Let T be the **prespecified** between-source covariance, V_i=S_i+T, P_i=V_i^(-1). Then C=(sum P_i)^(-1), mu=C*sum(P_i*z_i). This is generalized least squares for z_i ~ N_2(mu,V_i), integrating Gaussian source-level random effects when T>0. T0 gives a common-logit constraint, not estimated random heterogeneity. All covariance choices are explicit:

| T ID | SD sensitivity | SD FPR | rho sensitivity/FPR | matrix [[T11,T12],[T12,T22]] |
| --- | --- | --- | --- | --- |
| T0 | 0.0 | 0.0 | 0.0 | [[0.0, 0.0], [0.0, 0.0]] |
| T05Rneg | 0.5 | 0.5 | -0.5 | [[0.25, -0.125], [-0.125, 0.25]] |
| T05R0 | 0.5 | 0.5 | 0.0 | [[0.25, 0.0], [0.0, 0.25]] |
| T05Rpos | 0.5 | 0.5 | 0.5 | [[0.25, 0.125], [0.125, 0.25]] |
| T1R0 | 1.0 | 1.0 | 0.0 | [[1.0, 0.0], [0.0, 1.0]] |


Correlations refer to sensitivity/FPR logits, not sensitivity/specificity. Matrices with nonzero correlation can change both GLS mean coordinates through cross-coordinate weighting; results need not equal separate univariate inverse-variance summaries. The complete [diagnostic input/covariance/weight ledger](../../results/exploratory/diagnostic_scenario_inputs.csv) records S_i, V_i and the 2x2 coefficient matrices C*P_i, which sum to identity.

Report sensitivity=expit(mu_1), specificity=expit(-mu_2). Marginal conditional 95% intervals transform mu_j +/- 1.95996398454*sqrt(C_jj), reversing FPR to specificity correctly. Joint regions use (u-mu)'C^(-1)(u-mu)<=chi²(2,0.95) on logit coordinates, transformed to ROC space. They are **confidence regions conditional on covariance**, not study prediction regions or fitted HSROC curves. Point/covariance solves are closed form; iterative convergence and Bayesian priors/MCMC do not apply.

Check all covariance eigenvalues, normal-equation residuals and condition numbers. Q_conditional=sum[(z_i-mu)'P_i(z_i-mu)] is a conditional residual diagnostic with 4-2=2 degrees of freedom if covariance were truly known, not an empirical T estimate. Sparse-cell and large conditional residual warnings remain in output; no adverse scenario is suppressed.

EXPLORATORY — clustered windows, unresolved analysis units and assumed statistical parameters.

## Why no unrestricted covariance fit

Two paired source observations supply four scalar logits. After two mean coordinates, the ordinary residual scatter has rank at most one; attempting to learn two random-effect variances and a correlation would be extremely unstable/boundary-prone. Parameter counting alone is not asserted as a general structural-identifiability theorem. No reliable unrestricted fit or empirical between-study correlation is claimed. Prespecifying T makes the conditional GLS problem solvable without pretending T was learned from these two sources.

## Reproduction and software

Run `make exploratory`, then `make verify-exploratory`. The separate runner records input/configuration/output hashes, source revision, versions, original-source hash references, all scenarios, attempted/accepted fits and full tests in `results/exploratory/run_manifest.json`. Computation is deterministic; no random simulation is used. Public curated reproduction requires no raw files or external evidence. Original `make all` remains a separate descriptive workflow.
