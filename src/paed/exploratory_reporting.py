"""All scenarios are reported, including errors and assumption ledgers."""
import json
from itertools import combinations
from pathlib import Path
import numpy as np
from .reporting import write_md,md_table
from .exploratory import CLASS,LIMIT_A,LIMIT_D


def contrasts(results):
    A=[r for r in results['auroc_results'] if r['status']=='success_conditional']
    D=[r for r in results['diagnostic_results'] if r['status']=='success_conditional']
    out=[]
    def pair(analysis,factor,a,b):
        row={'analysis_class':CLASS,'analysis':analysis,'factor':factor,'scenario_from':a['scenario_id'],'scenario_to':b['scenario_id'],
             'limitations':LIMIT_A if analysis=='auroc' else LIMIT_D}
        if analysis=='auroc':row['delta_auroc']=b['pooled_auroc']-a['pooled_auroc']
        else:
            row['delta_sensitivity']=b['summary_sensitivity']-a['summary_sensitivity']
            row['delta_specificity']=b['summary_specificity']-a['summary_specificity']
            row['delta_variance_logit_sensitivity']=b['summary_cov_11']-a['summary_cov_11']
            row['delta_variance_logit_fpr']=b['summary_cov_22']-a['summary_cov_22']
        out.append(row)
    for a,b in combinations(A,2):
        dif=[k for k in ['kenet_estimate_id','dallas_estimate_id','assumed_se_auroc'] if a[k]!=b[k]]
        if len(dif)==1:pair('auroc',{'kenet_estimate_id':'Kenet model','dallas_estimate_id':'Dallas substitution','assumed_se_auroc':'Assumed AUROC SE'}[dif[0]],a,b)
    for a,b in combinations(D,2):
        dif=[k for k in ['kenet_model_id','kenet_design_effect','yu_variance_inflation','between_covariance_id','rho_within_assumed'] if a[k]!=b[k]]
        if len(dif)==1:
            names={'kenet_model_id':'Kenet model','kenet_design_effect':'Kenet design effect','yu_variance_inflation':'Yu variance inflation','between_covariance_id':'Between-source covariance','rho_within_assumed':'Within-source correlation'}
            pair('diagnostic',names[dif[0]],a,b)
    return out


def contrast_summary(rows):
    summary=[]
    for analysis in ['auroc','diagnostic']:
        for factor in dict.fromkeys(x['factor'] for x in rows if x['analysis']==analysis):
            rs=[r for r in rows if r['analysis']==analysis and r['factor']==factor]
            row={'analysis_class':CLASS,'analysis':analysis,'factor':factor,'matched_pairs':len(rs),
                 'interpretation':'Absolute differences across matched configured scenarios; not sampling uncertainty, effect tests or clinical validation'}
            for key in ['delta_auroc','delta_sensitivity','delta_specificity']:
                if key in rs[0]:
                    largest=max(rs,key=lambda x:abs(x[key]));row['max_abs_'+key]=abs(largest[key]);row[key+'_example']=largest['scenario_from']+' -> '+largest['scenario_to']
            summary.append(row)
    return summary


def auroc_display(rows):
    out=[]
    for r in rows:
        out.append({'scenario':r['scenario_id'],'Kenet':r['kenet_estimate_id'].removeprefix('kenet_2023_').removesuffix('_a1'),
            'Dallas':r['dallas_estimate_id'].split('_')[1],'assumed SE':r['assumed_se_auroc'],
            'conditional pooled AUROC [95%]':f'{r["pooled_auroc"]:.4f} [{r["conditional_95_lower"]:.4f}, {r["conditional_95_upper"]:.4f}]' if r['status']=='success_conditional' else 'NOT POOLED: '+r['error_message'],
            'estimated logit tau²':f'{r["tau2_logit_estimated"]:.6f}' if r['status']=='success_conditional' else '',
            'status / diagnostics':('boundary; ' if r.get('tau2_boundary') else '')+('validated fallback; ' if r.get('fallback_used') else '')+r['status']})
    return out


def diagnostic_display(rows):
    out=[]
    for r in rows:
        success=r['status']=='success_conditional'
        out.append({'scenario':r['scenario_id'],'Kenet':r['kenet_model_id'].removeprefix('kenet_2023_'),
            'Kenet D':r['kenet_design_effect'],'Yu D':r['yu_variance_inflation'],'T':r['between_covariance_id'],'within rho':r['rho_within_assumed'],
            'conditional sensitivity [95%]':f'{r["summary_sensitivity"]:.4f} [{r["sensitivity_conditional_95_lower"]:.4f}, {r["sensitivity_conditional_95_upper"]:.4f}]' if success else 'NOT POOLED',
            'conditional specificity [95%]':f'{r["summary_specificity"]:.4f} [{r["specificity_conditional_95_lower"]:.4f}, {r["specificity_conditional_95_upper"]:.4f}]' if success else 'NOT POOLED',
            'status':r['status']})
    return out


def render(root,results,config,summary,attempts,checks):
    root=Path(root);reports=root/'reports/exploratory'
    A=results['auroc_results'];D=results['diagnostic_results'];gooda=[r for r in A if r['status']=='success_conditional'];goodd=[r for r in D if r['status']=='success_conditional']
    at=md_table(auroc_display(A),list(auroc_display(A)[0]));dt=md_table(diagnostic_display(D),list(diagnostic_display(D)[0]))
    wa=config['auroc']['warning'];wd=config['diagnostic']['warning']
    countsa=len(gooda);countsd=len(goodd)
    amin=min(r['pooled_auroc'] for r in gooda);amax=max(r['pooled_auroc'] for r in gooda)
    smin=min(r['summary_sensitivity'] for r in goodd);smax=max(r['summary_sensitivity'] for r in goodd)
    pmin=min(r['summary_specificity'] for r in goodd);pmax=max(r['summary_specificity'] for r in goodd)
    tau_table=[]
    for q in config['diagnostic']['between_source_covariances']:
        tau_table.append({'T ID':q['id'],'SD sensitivity':q['sd_sensitivity'],'SD FPR':q['sd_fpr'],'rho sensitivity/FPR':q['correlation'],
                          'matrix [[T11,T12],[T12,T22]]':str([[q['sd_sensitivity']**2,q['correlation']*q['sd_sensitivity']*q['sd_fpr']],[q['correlation']*q['sd_sensitivity']*q['sd_fpr'],q['sd_fpr']**2]])})
    tt=md_table(tau_table,list(tau_table[0]))
    seen={r['estimate_id']:r for r in results['auroc_inputs']}
    selected_table=md_table([{'estimate':r['estimate_id'],'source row':r['source_row'],'AUROC':r['auroc'],
        'uncertainty provenance':f'genuine 95% CI {r["ci_lower"]}-{r["ci_upper"]}' if r['uncertainty_origin'].startswith('genuine') else 'No genuine SE; hypothetical 0.02/0.04/0.08'} for r in seen.values()],['estimate','source row','AUROC','uncertainty provenance'])
    seen_d={r['model_id']:r for r in results['diagnostic_inputs']}
    counts_table=md_table([{k:r[k] for k in ['model_id','source_row','tp','fp','fn','tn','analysis_unit']} for r in seen_d.values()],['model_id','source_row','tp','fp','fn','tn','analysis_unit'])
    input_link='[AUROC input/weight ledger](../../results/exploratory/auroc_scenario_inputs.csv)'
    diag_link='[diagnostic input/covariance/weight ledger](../../results/exploratory/diagnostic_scenario_inputs.csv)'
    common='''The supplied extraction is authoritative for this task and has not been independently verified against original papers. No new studies, external confidence intervals, author correspondence or patient-level records were consulted. Reported source values are unchanged. Original confirmatory feasibility conclusions and descriptive outputs are preserved. The numbers here are **conditional pooled calculations**, not the primary evidence-supported findings or established clinical accuracy.'''
    limits=f'''# EXPLORATORY: assumptions and limitations

{common}

## Assumptions introduced for AUROC

{wa}

Select exactly four source groups: named Lu PEDCA-FT, Bose held-out GLM, one Dallas report and one Kenet algorithm. Kenet logistic regression is an analyst-selected conventional baseline, not a claim it was the original study's primary model. XGBoost and soft voting are separately assessed; all alternatives are reported. Yu 2022 replaces Yu 2023, never accompanies it. Selection is not optimized for a favourable pooled result. First-hour Yu peaks, varying warning times and other forecast contexts are not equivalent endpoints.

Only Yu 2023 provides a labelled AUROC 95% CI. All other missing SEs are hypothetical 0.02/0.04/0.08 on original AUROC scale. These ranges are illustrative, not empirically calibrated or exhaustive bounds. Lu's +/- value is never used as sampling SE. Its meaning remains unknown. Delta transformation can magnify a fixed original-scale SE near AUROC=1; this is mathematically expected and makes model weights assumption-dependent. The normal-logit approximation is not validated by these files. Conditional intervals do not include uncertainty about the chosen SE assumptions, cohort independence or selection.

## Assumptions introduced for diagnostic summaries

{wd}

Exactly two source summaries are used per scenario: one Kenet model and the Yu 2023 table. They are assumed mutually independent for calculation. Within-source sampling covariance is based on normal-logit delta approximations and explicit design-effect/correlation assumptions; the counts are not converted to observed effective patient samples. Kenet design effects 1/5/20 and Yu multipliers 1/5 are analyst assumptions, not measured ICCs or corrections known to be adequate. Scaling Yu variance probes sensitivity to uncertainty but cannot identify its counted unit, model, fold, horizon or threshold. Classification thresholds differ or are unknown.

The between-source covariance T is fixed at the configured values, not estimated. The joint normal GLS mean and its conditional covariance can be computed with two sources under that constraint. This is **not** an unrestricted fitted bivariate random-effects model or fitted HSROC. Normal-logit variances are particularly uncertain with sparse cells: Yu has FN=4, Kenet XGBoost FN=1. Known-assumed-covariance normal intervals and joint confidence ellipses exclude uncertainty about covariance parameters, source-data validity and the original selection process. No distribution of future clinical accuracy is inferred.

## Inherent source restrictions

Kenet matrices count repeated five-minute windows (3,059 per table, 211 positive), not independent patients/arrests. The test cohort contains 229 patients with five CA patients. Positive windows exceed 180 under an unstated one-arrest-per-patient assumption and three-hour/five-minute labeling rule; event multiplicity/labeling remain unresolved. Its whole cohort includes 38 adults; no paediatric-only accuracy is available. General PICU is team-agreed but broader than registered CICU eligibility. None of the retained reports demonstrates all strict protocol criteria, including external validation. Formal eligibility amendments, QUADAS-2 and adapted GRADE decisions are not supplied or presumed.

Yu 2022/2023 probably overlap by institution, period and 160 CA/711 controls, and are never independent contributors to the same scenario. Missing AUROC uncertainty, internal-only or unreported validation, selected controls/negative windows and heterogeneous inputs/outcomes remain. No original-paper verification is possible in this task. Private source narratives remain withheld. The original five-report/20-model inventory and exclusions remain intact.

## Interpretation boundaries

Pooled AUROC is the back-transformed mean of selected AUROC logits under assumed variances and random effects. It is not one tool's discrimination, a newly measured study AUROC, or sensitivity. Diagnostic summaries are back-transformed GLS mean logits for mixed-unit, different-threshold source summaries; they do not measure a common clinically validated operating point. A transformed mean logit is not generally the arithmetic mean probability over a random-effects distribution.

Differences across scenarios quantify **assumption sensitivity**, not sampling CIs, effectiveness comparisons or validation. Stable digits cannot resolve bias, indirectness, wrong units, unmeasured clustering or absent external validation. No clinical deployment or safety recommendation follows. Actual false alarms per patient-day, missed children, calibration, net benefit and improved outcomes cannot be inferred.
'''
    write_md(reports/'assumptions_and_limitations.md',limits)
    methods=f'''# EXPLORATORY: meta-analysis methods

{common}

## Scope, selections and provenance

Working extraction: five reports/20 models with Yu 2026 and Yu 2023 Gaussian Naive Bayes excluded. Computations read only the existing AUROC and diagnostic CSVs plus explicit configuration, retaining source record, model, cohort/dependency identifier and units in every ledger. The baseline hashes protect 67 original scientific/configuration/data files. Original execution metadata may change only on an intentional original-pipeline rerun; this extension does not rewrite it.

AUROC factorial: 2 mutually exclusive Dallas reports x 3 Kenet choices x 3 assumed missing SEs = {len(A)} scenarios. Fixed choices are Lu PEDCA-FT and Bose **held-out** test. Default selection is Yu 2023 plus Kenet logistic regression, reported at all three SE assumptions; no single assumption is called empirical truth. Clinical independence between four conservative source groups is assumed, not established.

Diagnostic factorial: 3 Kenet choices x 3 Kenet design effects x 2 Yu inflation factors x 5 fixed T specifications = 90 scenarios. Six additional focused within-source-correlation variants (3 models x 2 correlations) give {len(D)} total. No scenario contains multiple Kenet algorithms as separate sources.

## AUROC normal random-effects model

For source i, y_i=logit(AUC_i). The conditional model is y_i ~ N(mu, v_i+tau²). For genuinely labelled Yu 2023 CI, use the existing endpoint approximation SE_logit=[logit(0.90)-logit(0.79)]/(2*1.95996398454)=0.22252939; CI construction is still unverified. For missing uncertainty, set original-scale SE=s in {{0.02,0.04,0.08}} and use delta SE_logit=s/[p(1-p)]. These are explicitly **assumed**, not extracted SEs or reconstructed confidence limits.

The installed primary implementation is `statsmodels.stats.meta_analysis.combine_effects(method_re="iterated")`, **Paule–Mandel**, not REML. Its installed source documents checks against metafor; it was inspected locally and is independently tested here against equal-variance analytic and unequal-variance bracketed-root solutions using synthetic numerical examples (no new clinical data). The PM estimate solves sum[w_i(tau²)*(y_i-mu_w)²]=k-1 if Q(0)>k-1, otherwise tau²=0. We verify that equation or boundary inequality for every fit. Maximum iterations={config['auroc']['tau2_maxiter']}, equation tolerance={config['auroc']['equation_check_tolerance']}.

If a library iteration fails the equation check, preserve the failure and solve the **same PM equation** by configured SciPy `brentq` bracketing. This changes the numerical solver only, not source values, estimator or assumptions. A failed fallback yields no pooled result. All attempts, including unsuccessful initial attempts, are in `fit_attempts.csv`.

Weights are 1/(v_i+tau²). Conditional pooled logit mu=sum(w_i*y_i)/sum(w_i). Modified Hartung–Knapp variance=max[1/sum(w_i), Q(tau²)/((k-1)*sum(w_i))], using t critical value with k-1=3 degrees of freedom. Transform mu and interval endpoints by expit. This scale floor prevents the H-K adjustment narrowing below the conventional variance at a zero-heterogeneity boundary. Report tau² on **logit** scale, Q, root residual, boundary status, weights, warnings and solver. No I², clinical prediction interval or p-value is used to claim validity.

{wa}

## Joint diagnostic normal-logit model with fixed heterogeneity

For each unchanged table, z_i=(log(TP/FN), log(FP/TN))'=(logit sensitivity, logit FPR)'. Within covariance S_i has diagonal D_i*(1/TP+1/FN) and D_i*(1/FP+1/TN). Its off-diagonal is rho_within*sqrt(S11*S22), with primary rho_within=0 and focused alternatives -0.5/+0.5 for both sources. D_Kenet=1/5/20; D_Yu=1/5. Disjoint-class binomial independence motivates the naive zero correlation, but repeated patients can link both outcomes; all these covariances are assumptions. Counts are never divided, rounded or replaced by effective counts.

Let T be the **prespecified** between-source covariance, V_i=S_i+T, P_i=V_i^(-1). Then C=(sum P_i)^(-1), mu=C*sum(P_i*z_i). This is generalized least squares for z_i ~ N_2(mu,V_i), integrating Gaussian source-level random effects when T>0. T0 gives a common-logit constraint, not estimated random heterogeneity. All covariance choices are explicit:

{tt}

Correlations refer to sensitivity/FPR logits, not sensitivity/specificity. Matrices with nonzero correlation can change both GLS mean coordinates through cross-coordinate weighting; results need not equal separate univariate inverse-variance summaries. The complete {diag_link} records S_i, V_i and the 2x2 coefficient matrices C*P_i, which sum to identity.

Report sensitivity=expit(mu_1), specificity=expit(-mu_2). Marginal conditional 95% intervals transform mu_j +/- 1.95996398454*sqrt(C_jj), reversing FPR to specificity correctly. Joint regions use (u-mu)'C^(-1)(u-mu)<=chi²(2,0.95) on logit coordinates, transformed to ROC space. They are **confidence regions conditional on covariance**, not study prediction regions or fitted HSROC curves. Point/covariance solves are closed form; iterative convergence and Bayesian priors/MCMC do not apply.

Check all covariance eigenvalues, normal-equation residuals and condition numbers. Q_conditional=sum[(z_i-mu)'P_i(z_i-mu)] is a conditional residual diagnostic with 4-2=2 degrees of freedom if covariance were truly known, not an empirical T estimate. Sparse-cell and large conditional residual warnings remain in output; no adverse scenario is suppressed.

{wd}

## Why no unrestricted covariance fit

Two paired source observations supply four scalar logits. After two mean coordinates, the ordinary residual scatter has rank at most one; attempting to learn two random-effect variances and a correlation would be extremely unstable/boundary-prone. Parameter counting alone is not asserted as a general structural-identifiability theorem. No reliable unrestricted fit or empirical between-study correlation is claimed. Prespecifying T makes the conditional GLS problem solvable without pretending T was learned from these two sources.

## Reproduction and software

Run `make exploratory`, then `make verify-exploratory`. The separate runner records input/configuration/output hashes, source revision, versions, original-source hash references, all scenarios, attempted/accepted fits and full tests in `results/exploratory/run_manifest.json`. Computation is deterministic; no random simulation is used. Public curated reproduction requires no raw files or external evidence. Original `make all` remains a separate descriptive workflow.
'''
    write_md(reports/'meta_analysis_methods.md',methods)
    af=f'''# EXPLORATORY: AUROC meta-analysis results

{common}

**{countsa}/{len(A)} configured scenarios produced conditional pooled results.** Each has four potentially independent source groups, assumed independent for fitting; the existing source inventory remains five reports/20 models. Conditional summaries range **{amin:.6f}-{amax:.6f}** across configurations. This range is scenario spread, not a confidence interval.

{wa}

{LIMIT_A} Yu 2023's genuine CI is preserved; all other missing variances are hypothetical. Yu 2022 substitution means all four variances are assumed. No numerical result is a confirmatory estimate, and none resolves validation, horizon or protocol discrepancies.

## Selected extracted AUROCs

{selected_table}

Each scenario includes four rows from this seven-evaluation set, as configured; never both Dallas reports.

## Every configured scenario

{at}

Each bracketed interval is the modified H-K conditional 95% interval, df=3. Estimated tau² refers to the assumed-variance logit model, not verified clinical heterogeneity. Full precision, source/model selections, assumptions, convergence and numerical diagnostics are in [auroc_scenario_results.csv](../../results/exploratory/auroc_scenario_results.csv); {input_link} gives all 72 selected rows, individual points, genuine versus hypothetical SEs, plot limits and weights.

## Preserved numerical attempts

{md_table([r for r in attempts if r['analysis']=='auroc' and r.get('status')!='success_conditional'],['scenario_id','solver','status','message']) if any(r['analysis']=='auroc' and r.get('status')!='success_conditional' for r in attempts) else 'No failed numerical attempts.'}

All final accepted fits pass the PM equation/boundary check. A numerical fallback is disclosed, not a suppressed or data-modified fit. Zero tau² at some high-SE scenarios is a conditional boundary estimate; it does not show the studies are clinically homogeneous.

## Forest plots and assumption sensitivity

![AUROC sensitivity](../../figures/exploratory/auroc_sensitivity.png)

Shading is conditional 95% uncertainty under each scenario; it excludes uncertainty about the assumptions. Genuine study intervals are used only for Yu 2023; other forest error bars arise from analyst-assumed SEs. Different algorithms/horizons/units are summarized under a hypothetical random-effects model. All successful scenarios have individual forest plots:

'''+ '\n'.join(f'- [{r["scenario_id"]}](../../figures/exploratory/forest_{r["scenario_id"]}.png) ([SVG](../../figures/exploratory/forest_{r["scenario_id"]}.svg)): {r["pooled_auroc"]:.4f} [{r["conditional_95_lower"]:.4f}, {r["conditional_95_upper"]:.4f}]; **{wa}** {LIMIT_A}' for r in gooda)
    write_md(reports/'auroc_meta_analysis.md',af)
    dr=f'''# EXPLORATORY: diagnostic joint pooling results

{common}

**{countsd}/{len(D)} configured conditional GLS scenarios solved successfully.** Each contains one Kenet model and the Yu 2023 representative-fold table: two assumed independent source summaries, not seven independent studies or two verified patient datasets. Across all configurations, summary sensitivity ranges **{smin:.6f}-{smax:.6f}** and specificity **{pmin:.6f}-{pmax:.6f}**. These separate scenario extrema need not occur in the same scenario and are not confidence intervals.

{wd}

{LIMIT_D} All heterogeneity parameters are fixed assumptions, not empirical estimates. The original counts remain unchanged; all 192 source-scenario rows, analysis units, linkage caveats, sampling/total covariances and GLS weight matrices are in the {diag_link}.

## Assumed between-source covariance matrices

{tt}

D means variance inflation: Kenet 1/5/20; Yu 1/5. Primary within-source rho=0. The six focused within-rho variants use Kenet D=5, Yu D=1, T05R0 and rho=-0.5/+0.5. Intervals condition on these choices, assume approximate normal logits, and do not include uncertainty in covariance parameters or extraction validity. All tables include a small-cell approximation warning because Yu has FN=4; XGBoost additionally has FN=1.

## Unchanged observed count tables used

{counts_table}

Only one Kenet row accompanies Yu in each scenario.

## Every configured scenario

{dt}

Every bracket is a **conditional marginal** 95% interval, not a reported study CI or validated patient-level interval. Full precision and diagnostics are in [diagnostic_scenario_results.csv](../../results/exploratory/diagnostic_scenario_results.csv). No unrestricted covariance/HSROC fit was claimed. Closed-form solutions are checked by positive-definite covariance, normal equations and condition numbers; large conditional residual diagnostics remain visible.

## Numerical diagnostics

Maximum normal-equation residual: {max(r['normal_equation_residual'] for r in goodd):.3g}; maximum covariance/precision condition number: {max(r['max_condition_number'] for r in goodd):.3f}. There are {sum('Large conditional residual' in r['numerical_warnings'] for r in goodd)} scenarios with large conditional residual discrepancy warnings, retained in the table/ledger. This signals tension under the specified covariance model, not an estimated heterogeneity parameter. All {len(goodd)} scenarios have sparse-cell approximation warnings. No warnings are used to select favourable scenarios.

## Conditional joint regions

![Joint summaries](../../figures/exploratory/diagnostic_joint_summaries.png)

Caption: one panel per Kenet model; fixed T05R0 (SDs=0.5, rho=0), Yu D=1, within rho=0; Kenet D=1/5/20 varies. Lines are transformed **joint confidence ellipses** under supplied covariance, not fitted SROC curves or prediction regions. {wd} {LIMIT_D}

![Diagnostic sensitivity](../../figures/exploratory/diagnostic_sensitivity.png)

Caption: all five T choices across Kenet D=1/5/20, per model, holding Yu D=1 and within rho=0. Lines connect assumption scenarios and omit error bars for legibility; all conditional intervals and additional variants are tabulated. {wd} {LIMIT_D}
'''
    write_md(reports/'diagnostic_meta_analysis.md',dr)
    # Narrow readable summary, with percentage-point differences explicitly stated.
    short=[]
    for r in summary:
        short.append({'analysis':r['analysis'],'assumption changed':r['factor'],'matched pairs':r['matched_pairs'],
                      'max absolute delta AUROC':f'{r["max_abs_delta_auroc"]:.6f}' if 'max_abs_delta_auroc' in r else '',
                      'max absolute delta sensitivity (pp)':f'{100*r["max_abs_delta_sensitivity"]:.3f}' if 'max_abs_delta_sensitivity' in r else '',
                      'max absolute delta specificity (pp)':f'{100*r["max_abs_delta_specificity"]:.3f}' if 'max_abs_delta_specificity' in r else ''})
    shortt=md_table(short,list(short[0]))
    sens=f'''# EXPLORATORY: sensitivity analysis

{common}

The following are matched-scenario contrasts, changing one configured factor at a time. They are not causal model comparisons or hypothesis tests. All paired scenarios and numerical deltas are in [sensitivity_contrasts.csv](../../results/exploratory/sensitivity_contrasts.csv). The table reports maximum absolute changes over the configured grid only; larger changes under unexamined assumptions remain possible.

{shortt}

## 1. Assumed AUROC SE

Increasing assumed original-scale uncertainty changes transformed variances, study weights and estimated tau². The pooled result need not move monotonically or its interval widen monotonically, because relative weights and estimated random heterogeneity change together. The genuine Yu 2023 CI is retained while other SEs vary. Across all 18 configurations, pooled AUROC spans {amin:.4f}-{amax:.4f}; this is not an uncertainty interval over a probability model of assumptions.

## 2. Representative Kenet model

All logistic, soft-voting and XGBoost choices are reported; no observed maximum is selected as the preferred conclusion. A constant original-scale SE corresponds to a larger logit SE near AUROC=1, so high reported AUROC does not guarantee high inverse-variance weight. The full weight ledger makes this visible. Model-selection sensitivity does not establish an architecture winner.

## 3. Substitute Yu 2022

Yu 2022 replaces, never accompanies, Yu 2023. This changes both the source estimate (0.83 versus 0.85) and uncertainty provenance: Yu 2023 has a labelled CI, while Yu 2022's variance is assumed. The matched contrast is a joint substitution, not an isolated estimate of a publication-year or algorithm effect.

## 4. Kenet clustering assumptions

D=1 is the naive independence scenario, not an endorsed analysis of windows. D=5/20 inflate source covariance while preserving counts and logit points. Relative source influence changes and conditional logit-mean variances increase when only a source covariance is inflated at fixed T/rho. Summary point estimates can shift toward Yu, with the direction depending on the selected Kenet model. The illustrative D values do not identify real ICCs or validate an effective patient count.

## 5. Between-source and within-source covariance

T0 assumes no between-source heterogeneity; T05 assumes SDs=0.5 with three correlations; T1 assumes SDs=1 with zero correlation. All are fixed, not estimated. Yu inflation and within-rho checks are separate sensitivity axes. These assumptions change the joint weights, means and intervals; correlation is in sensitivity/FPR coordinates. The transformed conditional summaries span sensitivity {smin:.4f}-{smax:.4f}, specificity {pmin:.4f}-{pmax:.4f}. Separate extremes are not one simultaneous operating point. Known-assumed-covariance intervals omit uncertainty about T, D and rho.

## 6. Relatively stable conclusions

Within this grid AUROC summaries remain above 0.5, but that numerical pattern is conditional on selected reported points, assumed uncertainty and model form. The source-data facts remain stable: genuine AUROC uncertainty is scarce; Kenet observations are repeated windows; Yu linkage remains unresolved; no confirmed external validation or universal threshold is added. Numerical stability does not validate clinical accuracy.

## 7. Results too assumption-dependent for clinical interpretation

There is no unique pooled AUROC or diagnostic operating point that can be selected as the evidence-supported answer. The apparently precise T0/D1 result assumes independence and zero heterogeneity that the extraction does not establish. Wider scenarios are not automatically adequate either. These summaries cannot determine patient-level missed arrests, alert burden, deployment safety or prospective benefit.

{wa}

{wd}
'''
    write_md(reports/'sensitivity_analysis.md',sens)
    summarydoc=f'''# EXPLORATORY: conditional results summary

{common}

The team requested numerical exploration despite the prior confirmatory feasibility blockers. This continuation executes explicit additional assumptions without changing the original findings.

- AUROC: **{countsa}/{len(A)} final scenarios fitted**, four assumed independent groups each; conditional pooled results span **{amin:.4f}-{amax:.4f}**.
- Diagnostic: **{countsd}/{len(D)} constrained joint scenarios solved**, two assumed independent source summaries each; conditional sensitivity spans **{smin:.4f}-{smax:.4f}**, specificity **{pmin:.4f}-{pmax:.4f}**. Extrema are separate scenario values, not a joint interval.
- Original five reports/20 models and all evidence-supported descriptive/feasibility conclusions are preserved. Confirmatory pooling remains unsupported.
- Every result includes the uncertainty provenance, assumptions, diagnostics and limitations. All scenarios are listed below and in machine-readable CSVs.

## Reading the conditional numbers

We asked what the calculations would produce **if** missing uncertainty, clustering and differences between sources had the specified values. The source numbers stay fixed while these extra assumptions change.

- **Assumed SE** describes hypothetical precision of an AUROC. It is not a number recovered from the paper. Lu's +/- variation remains unspecified.
- **Design effect D** inflates uncertainty for repeated observations; it does not turn windows into a known number of independent children.
- **T** specifies assumed differences between source logits. Its entries were supplied by the analyst, not learned from two sources.
- A **conditional 95% interval** describes uncertainty only if the selected statistical model and its parameter assumptions hold. It does not cover extraction errors, bias, uncertain clinical units or uncertainty about the assumptions themselves.
- AUROC describes ranking. Sensitivity/specificity concern a threshold and a counted unit. None of the summaries establishes the percentage of children whose arrests would be anticipated in practice.

## AUROC scenarios

{selected_table}

{wa}

Missing SEs are hypothetical; only Yu 2023 CI is genuine. Each interval below is conditional on assumed independence and sampling uncertainty, with k=4 and modified H-K df=3. {LIMIT_A}

{at}

## Diagnostic scenarios

{counts_table}

Prespecified between-source covariance matrices (never estimated):

{tt}

{wd}

Exactly one Kenet table and Yu 2023 per scenario. Fixed T and inflated S are assumptions; no unrestricted covariance is estimated. Each interval below is a conditional marginal normal-logit interval. {LIMIT_D}

{dt}

## Sensitivity to assumptions

{shortt}

See [sensitivity analysis](sensitivity_analysis.md) for the seven requested questions and every matched contrast in the CSV. Scenario spread is not a confidence interval. No favourable scenario is selected as the answer.

## Clinical interpretation

An AUROC ranks observations across thresholds; it is not arrest-detection sensitivity. The joint results summarize two mixed-unit, different-threshold sources under assumed covariance; they are not estimates of the proportion of children whose arrests would be anticipated in practice. Window false positives cannot be converted to alarms per patient-day. Conditional precision and apparent stability do not establish validity, clinical usefulness or safety. No deployment recommendation is made.

## Limits and differences from the original analysis

The descriptive analysis uses only supplied observed metrics and retains its **not statistically defensible** confirmatory pooling conclusion. This separate layer adds hypothetical variances and fixed covariance parameters, explicitly authorized for sensitivity calculations. It does not change missing source uncertainty into measured uncertainty or make windows independent. Yu model/horizon linkage, potential Dallas reuse, adult inclusion, general-PICU scope, absent demonstrated external validation and reviewer assessments remain unresolved. See [full limitations](assumptions_and_limitations.md).

## Figures and complete methods

![AUROC assumption sensitivity](../../figures/exploratory/auroc_sensitivity.png)

{wa} Conditional shading depends on assumed SEs; source horizons/units differ.

![Joint diagnostic summaries](../../figures/exploratory/diagnostic_joint_summaries.png)

{wd} Fixed T05R0, Yu D=1 and within rho=0 shown, with Kenet D=1/5/20; ellipses are conditional confidence regions, not HSROC curves or prediction regions.

![Diagnostic assumption sensitivity](../../figures/exploratory/diagnostic_sensitivity.png)

{wd} Five T choices, Yu D=1 and within rho=0 shown; source counts and units remain unchanged.

See [methods](meta_analysis_methods.md), [all AUROC results and forests](auroc_meta_analysis.md), [all diagnostic results](diagnostic_meta_analysis.md), and [assumption configuration](../../config/exploratory_scenarios.json).

## Execution and verification

The independent exploratory command is `make exploratory`; verify with `make verify-exploratory`. The run manifest records actual versions, commands, tests, preserved baseline hashes, every fit attempt and output hash. This is deterministic arithmetic; no new clinical data or simulated patient data were used. Full original and new tests are run. Numerical/completeness checks: {len(checks)} passed. Source Git SHA is the revision available at execution, not the future commit containing the manifest.
'''
    write_md(reports/'exploratory_results_summary.md',summarydoc)
    write_md(reports/'consolidated_exploratory_report.md',summarydoc)
