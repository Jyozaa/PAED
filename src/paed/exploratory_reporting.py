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
        dif=[k for k in ['lu_estimate_id','kenet_estimate_id','dallas_estimate_id','assumed_se_auroc'] if a[k]!=b[k]]
        if len(dif)==1:pair('auroc',{'lu_estimate_id':'Lu representative','kenet_estimate_id':'Kenet model','dallas_estimate_id':'Dallas substitution','assumed_se_auroc':'Assumed AUROC SE'}[dif[0]],a,b)
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


def auroc_display(rows,inputs):
    out=[]
    for r in rows:
        selected=[x for x in inputs if x['scenario_id']==r['scenario_id']]
        bystudy={x['study_id']:x for x in selected}
        row={'scenario':r['scenario_id'],'family':r['scenario_family']}
        for label,study in [('Lu 2025','lu_2025'),('Bose 2019','bose_2019'),('Dallas','yu_2023' if '2023' in r['dallas_estimate_id'] else 'yu_2022'),('Kenet 2023','kenet_2023')]:
            item=bystudy.get(study)
            row[label]=f'{item["model_name"]} ({item["auroc"]:.4f})'+(' held-out' if study=='bose_2019' else '')+(' '+study.replace('_',' ') if label=='Dallas' else '') if item else 'NOT POOLED'
        row.update({'assumed SE':r['assumed_se_auroc'],
            'conditional pooled AUROC [95%]':f'{r["pooled_auroc"]:.4f} [{r["conditional_95_lower"]:.4f}, {r["conditional_95_upper"]:.4f}]' if r['status']=='success_conditional' else 'NOT POOLED: '+r['error_message'],
            'estimated logit tau2':f'{r["tau2_logit_estimated"]:.6f}' if r['status']=='success_conditional' else '',
            'status':('boundary; ' if r.get('tau2_boundary') else '')+('checked fallback; ' if r.get('fallback_used') else '')+r['status']})
        out.append(row)
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



def render(root,results,config,summary,attempts,checks,comparison):
    root=Path(root);reports=root/'reports/exploratory';A=results['auroc_results'];D=results['diagnostic_results']
    core=[r for r in A if r['scenario_family']=='core_lu_logistic'];alt=[r for r in A if r['scenario_family']=='alternative_lu_model']
    good=[r for r in A if r['status']=='success_conditional'];goodcore=[r for r in core if r['status']=='success_conditional']
    goodd=[r for r in D if r['status']=='success_conditional'];wa=config['auroc']['warning'];wd=config['diagnostic']['warning']
    def atable(rows):
        display=auroc_display(rows,results['auroc_inputs']);return md_table(display,list(display[0]))
    ct=atable(core);alternative_table=atable(alt);dt=md_table(diagnostic_display(D),list(diagnostic_display(D)[0]))
    rangea=lambda rows:f'{min(r["pooled_auroc"] for r in rows):.6f}-{max(r["pooled_auroc"] for r in rows):.6f}'
    beforeafter=md_table(comparison['comparison'],['measure','previous','revised'])
    lu_table=md_table(comparison['lu_sensitivity'],['lu_model_id','individual_auroc','scenario_count','pooled_min','pooled_max','max_absolute_change_from_matched_lu_logistic'])
    tau=[]
    for r in config['diagnostic']['between_source_covariances']:
        a,b,p=r['sd_sensitivity'],r['sd_fpr'],r['correlation'];tau.append({'T':r['id'],'SD sensitivity':a,'SD FPR':b,'rho sensitivity/FPR':p,'fixed covariance matrix':str([[a*a,p*a*b],[p*a*b,b*b]])})
    tt=md_table(tau,list(tau[0]));seen={r['estimate_id']:r for r in results['auroc_inputs']}
    selected=md_table([{'estimate':r['estimate_id'],'source row':r['source_row'],'individual AUROC':r['auroc'],
        'uncertainty':f'genuine 95% CI {r["ci_lower"]}-{r["ci_upper"]}' if r['uncertainty_origin'].startswith('genuine') else 'hypothetical original-scale SE 0.02/0.04/0.08'} for r in seen.values()],['estimate','source row','individual AUROC','uncertainty'])
    counts={r['model_id']:r for r in results['diagnostic_inputs']}
    counts_table=md_table([{k:r[k] for k in ['model_id','source_row','tp','fp','fn','tn','analysis_unit']} for r in counts.values()],['model_id','source_row','tp','fp','fn','tn','analysis_unit'])
    short=[]
    for r in summary:
        short.append({'analysis':r['analysis'],'factor':r['factor'],'matched pairs':r['matched_pairs'],
                      'max absolute delta AUROC':f'{r["max_abs_delta_auroc"]:.6f}' if 'max_abs_delta_auroc' in r else '',
                      'max absolute sensitivity change (pp)':f'{100*r["max_abs_delta_sensitivity"]:.3f}' if 'max_abs_delta_sensitivity' in r else '',
                      'max absolute specificity change (pp)':f'{100*r["max_abs_delta_specificity"]:.3f}' if 'max_abs_delta_specificity' in r else ''})
    st=md_table(short,list(short[0]));reproduced=all(r['all_numerical_columns_identical'] for r in comparison['diagnostic_comparison'])
    common='''This eligibility revision wholly excludes Lu 2025 XGBoost, gMLP and PEDCA-FT because their sensitivity/specificity was graphically extracted and considered insufficiently reliable. Their AUROCs are excluded with the entries; this does not assert that those AUROCs were graphical. The revised extraction retains five reports and 17 models, including eight Lu models. Other Lu models remain eligible despite missing operating points. Only the supplied sources and existing derivatives are used. Original source hashes are unchanged and no new papers, clinical data or correspondence were obtained. Confirmatory pooling remains unsupported; every pooled number here is explicitly conditional on analyst assumptions.'''
    methods=f'''# Revised exploratory meta-analysis methods

{common}

## Versioned eligibility and provenance

The parent `exploratory-pooling` branch preserves the previous 20-model results. Immutable aggregate snapshots supply the before/after comparisons and are checked against their parent Git commit. The original integrity record is retained in `config/baselines/analysis_20_model_integrity.json` and validated against its historical Git tree. A separate 17-model baseline protects current scientific outputs/configuration/data, following descriptive validation. Original raw and curated source data are never rewritten to accommodate exclusions. The revision explicitly replaces outdated expectations rather than disabling them.

## AUROC selections and scenario families

Core scenarios use Lu logistic regression **0.6292**, Bose held-out GLM **0.7500**, Yu 2023 RDN Boost **0.8500** or Yu 2022 logistic **0.8300**, and one Kenet model (logistic **0.8670**, XGBoost **0.9710**, soft voting **0.9570**). Lu logistic is an analyst-selected conventional baseline after exclusion of the named index, not an original verified primary designation. All {len(core)} core scenarios cross 2 mutually exclusive Dallas choices, 3 Kenet choices and 3 missing-SE assumptions.

Every other retained Lu numerical AUROC is substituted in source-record order, with the same full cross. This produces {len(alt)} additional scenarios, {len(A)} total, one Lu model per scenario. No model is selected to maximize the pooled result, and the potentially overlapping Dallas reports never contribute together. Four source groups are assumed independent for calculation, not proven independent clinical cohorts.

{selected}

## Random-effects estimator and intervals

For source i, y_i=logit(AUC_i), v_i=SE_logit²; y_i follows a conditional normal random-effects model with mean mu and variance v_i+tau². Genuine Yu 2023 CI-derived logit SE remains 0.22252939, with unverified CI construction. For every missing SE, s=0.02/0.04/0.08 is **assumed on the AUROC scale**, and delta SE_logit=s/[p(1-p)]. None of Lu's unspecified +/- quantities is used as an SE.

The estimator remains **Paule-Mandel**, implemented in `statsmodels.stats.meta_analysis.combine_effects(method_re="iterated")`, not REML. It solves Q(tau²)=k-1 for a positive root or uses a valid zero boundary if Q(0)<=k-1. Every accepted root/boundary is checked. If the library iteration fails that check, the failure is preserved and the same equation is solved using configured SciPy `brentq`, with no input or estimator changes. Unsuccessful final fits have no numerical pooled estimate or forest.

Weights are 1/(v_i+tau²); mu=sum(w_i*y_i)/sum(w_i). Modified Hartung-Knapp variance is max[1/sum(w_i),Q(tau²)/((k-1)*sum(w_i))], using t(3) for four source groups. Pooled point/conditional 95% endpoints are back-transformed by expit. Tau² is estimated on logit scale conditional on hypothetical sampling variances. Zero tau² does not establish clinical homogeneity. No clinical prediction interval, I² or p-value is used to establish validity.

{wa}

## Diagnostic constrained joint model

All {len(D)} prior diagnostic configurations are **rerun unchanged**: one Kenet table plus the Yu representative-fold table. Kenet variance inflation D=1/5/20; Yu inflation=1/5; five fixed between-source covariance choices give 90 scenarios. Six focused within-correlation alternatives (-0.5/+0.5 for both sources, Kenet D=5, Yu D=1, T05R0) give 96 total. Counts remain observed integers in their window/unresolved units, never invented effective patient samples.

For each table z_i=(log(TP/FN),log(FP/TN))', the sensitivity/FPR logits. S_i has diagonal D*(1/TP+1/FN) and D*(1/FP+1/TN), and covariance rho_within*sqrt(S11*S22). Primary within rho is zero. Between-source covariance T is **fixed, not estimated**:

{tt}

With V_i=S_i+T and P_i=V_i^(-1), GLS gives C=(sum P_i)^(-1), mu=C*sum(P_i*z_i). Sensitivity=expit(mu_1), specificity=expit(-mu_2). Marginal conditional 95% intervals transform normal limits using C; specificity reverses the FPR sign correctly. Joint confidence regions use chi-square(2,0.95) ellipses in logit coordinates, transformed to ROC space. They are not fitted HSROC curves or study prediction regions.

Positive covariance, normal-equation residuals and condition numbers are checked. The conditional residual quadratic has two residual degrees of freedom under known-assumed covariance; it does not empirically estimate T. With two paired sources, unrestricted covariance estimation remains unstable; the residual scatter has rank at most one. Parameter counting alone is not asserted as a structural-identifiability theorem. Sparse cells and large conditional residuals are recorded, not suppressed.

{wd}

## Reproduction

`make revised` rebuilds descriptive outputs, all 144 AUROC/96 diagnostic scenarios, comparisons and the LaTeX PDF, then runs the full tests and verifies hashes. `make exploratory` runs the scenario layer against already revised descriptive data; `make verify-exploratory` checks its provenance and outputs. Core forests are provided for 18 scenarios; all 126 alternatives are fully tabulated and plotted in a dedicated comparison. Runtime, versions, commands, failures and assumptions appear in execution manifests.
'''
    write_md(reports/'meta_analysis_methods.md',methods)
    limitations=f'''# Revised exploratory assumptions and limitations

{common}

{wa}

Missing sampling uncertainty is hypothetical. Lu's eight retained +/- quantities have unknown meaning. Only Yu 2023 provides a genuine labelled AUROC CI. Delta transformation magnifies original-scale uncertainty near AUROC=1; weights and estimated tau² depend on the assumed SEs. Conditional intervals omit uncertainty about those assumptions, source selection, extraction validity and clinical independence. Lu logistic is a conservative analyst-selected baseline; all seven other eligible choices are reported. Scenario stability is not clinical validation.

{wd}

Kenet matrices count repeated five-minute windows: 3,059 per test table, including 211 positive windows, from 229 test patients with five CA patients. Neither 3,059 nor 211 is an independent patient/arrest count. The positive-window total requires reconciliation with event multiplicity and labeling; a one-arrest-per-patient assumption is not imposed. Variance multipliers 1/5/20 are illustrative, not measured ICCs or proven adequate cluster corrections. The whole cohort includes 38 adults without paediatric-only accuracy.

Yu 2023 table attribution was assumed by the extractor; fold, threshold, horizon and unit remain unresolved. Inflating variance by 5 probes uncertainty but cannot correct an unknown estimand or bias. FN=4 in Yu and FN=1 in Kenet XGBoost challenge normal-logit approximations. Fixed T/rho and within-source covariances are assumptions; known-covariance GLS intervals/ellipses do not include uncertainty in them. No unrestricted fitted covariance or HSROC curve is claimed.

Potential Dallas cohort reuse, selected case/control and negative-window sampling, different horizons/definitions/inputs, internal-only or unreported validation, absent demonstrated external validation, and PROSPERO setting/age discrepancies remain. No register amendment, external-validation waiver, dual-reviewer risk-of-bias or formal certainty grade is claimed. Full papers and teammates are unavailable; no new evidence was sought. Raw/private material remains local.

Conditional pooled logits describe the selected mixed-source statistical inputs, not one clinical AI tool, a common validated threshold, independently measured patient sensitivity, alert burden, calibration, prospective benefit, safety or deployment readiness. A transformed mean logit is not generally an arithmetic mean probability. Missing results are not zero. The historical previous analysis is explicitly separated from revised current results.
'''
    write_md(reports/'assumptions_and_limitations.md',limitations)
    af=f'''# Revised exploratory AUROC meta-analysis

{common}

**{len(goodcore)}/{len(core)} core scenarios** and **{len(good)-len(goodcore)}/{len(alt)} additional Lu-choice scenarios** produced accepted conditional estimates. Core pooled range: **{rangea(goodcore)}**. Across all retained Lu choices: **{rangea(good)}**. Ranges are scenario spread, not confidence intervals.

{wa}

{LIMIT_A} No excluded Lu model contributes an AUROC or uncertainty value. The following tables identify all four source reports/models and their individual points. The source/SE/weight ledger contains {len(results['auroc_inputs'])} rows with provenance, genuine versus assumed SEs and conditional limits.

## Core scenarios: Lu logistic regression

{ct}

## All other retained Lu representatives

{lu_table}

The range for each Lu choice covers its 18 configurations, not the uncertainty interval of a single fit. Differences relative to matched logistic scenarios change only the Lu representative.

{alternative_table}

## Numerical diagnostics

There are {sum(r.get('tau2_boundary',False) for r in good)} accepted zero-tau² boundaries and {sum(r.get('fallback_used',False) for r in good)} cases using the checked same-equation fallback. All initial rejected attempts remain in [fit_attempts.csv](../../results/exploratory/fit_attempts.csv). Every final accepted fit passes the PM root/boundary check. No favourable scenario is selected as the answer.

## Figures

![Core SE/model sensitivity](../../figures/exploratory/auroc_sensitivity.png)

{wa} This figure shows the 18 core scenarios only, with conditional interval shading, mixed horizons/units and four assumed independent groups.

![All retained Lu choices](../../figures/exploratory/lu_model_sensitivity.png)

{wa} One Lu representative per point, with all seven alternatives. Lines connect categorical scenario choices, not clinical trends. Full conditional intervals are tabulated above.

All core forests:

'''+ '\n'.join(f'- [{r["scenario_id"]}](../../figures/exploratory/forest_{r["scenario_id"]}.png) ([SVG](../../figures/exploratory/forest_{r["scenario_id"]}.svg)); {wa} {LIMIT_A}' for r in goodcore)
    write_md(reports/'auroc_meta_analysis.md',af)
    write_md(reports/'lu_model_sensitivity.md',f'''# All retained Lu representatives

{common}

{wa}

Core logistic regression and all seven remaining retained alternatives are crossed with the same other source selections and SE assumptions. No model is selected because its observed AUROC is highest. All {len(A)} four-source scenarios use exactly one Lu model.

{lu_table}

![Lu choice sensitivity](../../figures/exploratory/lu_model_sensitivity.png)

Ranges are conditional point-estimate spreads across 18 configurations, not study/model confidence intervals. Full per-scenario inputs, weights, intervals and diagnostics are in `auroc_scenario_results.csv` and `auroc_scenario_inputs.csv`.
''')
    dr=f'''# Revised exploratory diagnostic joint calculations

{common}

**{len(goodd)}/{len(D)} scenarios** solved under the same covariance assumptions as before. All previous numeric columns are identical: **{reproduced}**. Maximum absolute numerical difference: **{max(r['maximum_absolute_numerical_difference'] for r in comparison['diagnostic_comparison']):.1f}**. The calculations were executed again; previous pooled numbers were not substituted as new results.

{wd}

{LIMIT_D} Lu never contributed a complete count table to these scenarios. All source counts and settings remain unchanged. Summary sensitivity range is {min(r['summary_sensitivity'] for r in goodd):.6f}-{max(r['summary_sensitivity'] for r in goodd):.6f}; specificity range is {min(r['summary_specificity'] for r in goodd):.6f}-{max(r['summary_specificity'] for r in goodd):.6f}. Separate extrema are not a joint operating point or uncertainty interval.

{counts_table}

{tt}

## Every scenario and its conditional marginal intervals

{dt}

Maximum linear-equation residual: {max(r['normal_equation_residual'] for r in goodd):.3g}. Large conditional residual warnings: {sum('Large conditional residual' in r['numerical_warnings'] for r in goodd)} scenarios. Sparse-cell approximation warnings remain for all scenarios. T is fixed, not estimated; the solve is closed form, not iterative convergence. No HSROC is fitted.

![Conditional joint regions](../../figures/exploratory/diagnostic_joint_summaries.png)

{wd} T05R0, Yu inflation=1, within rho=0, Kenet D=1/5/20; transformed confidence ellipses are conditional on covariance, not prediction regions or fitted ROC curves.

![Diagnostic sensitivity](../../figures/exploratory/diagnostic_sensitivity.png)

{wd} Five fixed T choices, Yu inflation=1, within rho=0 shown; all additional Yu/correlation variants are tabulated. These graphs remain separate exploratory artifacts and are not included in the short LaTeX report.
'''
    write_md(reports/'diagnostic_meta_analysis.md',dr)
    sensitivity=f'''# Revised scenario sensitivity and before/after comparison

{common}

{beforeafter}

{st}

Matched contrasts change one configured factor at a time; they are not superiority tests or sampling confidence intervals. The expanded Lu-choice grid is distinguished from the 18 revised core scenarios. Saved predecessor results and all paired changes are independently checked against the parent Git commit.

1. Changing assumed AUROC SE changes logit precision, weights and estimated tau². Changes need not be monotonic, and conditional intervals need not widen monotonically as the estimated random variance also changes.
2. Changing Kenet model is always a separate scenario, not extra independent data. No architecture winner is inferred.
3. Substituting Yu 2022 changes both its point and uncertainty provenance, since all four variances then become hypothetical. Dallas reports never appear together.
4. Inflating Kenet covariance changes its influence and conditional logit-mean covariance while preserving all counts; the design effects are unmeasured assumptions.
5. T, Yu inflation and correlation choices remain hypothetical. The diagnostic grid is numerically unchanged by the Lu exclusions, not newly validated by numerical reproduction.
6. All original source-data limitations persist across assumptions. Stable numbers do not establish clinical validity.
7. No unique pooled clinical accuracy is supported. Wider or apparently precise scenarios are not automatically adequate corrections for bias, clustering, thresholds or unverified units.

## Additional Lu selection sensitivity

{lu_table}

{wa}

{wd}

See [full before/after comparison](../revisions/exclusion_comparison.md), all source/weight/covariance ledgers, and the complete scenario tables. No missing source information was invented.
'''
    write_md(reports/'sensitivity_analysis.md',sensitivity)
    document=f'''# Revised exploratory results summary

{common}

## Before and after the exclusion decision

{beforeafter}

## How to read these calculations

An assumed SE describes hypothetical precision, not recovered study uncertainty. A design effect inflates variance without turning windows into measured independent children. T supplies between-source logit covariance rather than estimating it from two sources. A conditional 95% interval assumes the stated statistical model and parameters; it excludes uncertainty about those assumptions, bias, extraction errors and unresolved clinical units.

## Selected individual AUROCs

{selected}

## The 18 revised core AUROC scenarios

{wa}

All four contributors and selected models are identified in the table below. Lu logistic is an analyst-selected baseline, not a verified original primary model. Genuine Yu 2023 CI-derived variance is retained; all missing SEs are hypothetical. Core range is **{rangea(goodcore)}**.

{ct}

## All seven other eligible Lu choices

One Lu model contributes per scenario. All **{len(alt)}** alternatives are reported. The combined {len(A)}-scenario range is **{rangea(good)}**, not an uncertainty interval.

{lu_table}

{alternative_table}

## Rerun diagnostic scenarios

{wd}

Exactly one Kenet model and the Yu table contribute. All 96 numeric result rows are unchanged: **{reproduced}**. Fixed covariance matrices are assumptions, not empirically estimated heterogeneity. Counts and units remain unchanged.

{counts_table}

{tt}

{dt}

## Sensitivity to assumptions

{st}

## Figures

![Core AUROC scenarios](../../figures/exploratory/auroc_sensitivity.png)

{wa} Revised core uses Lu logistic, four assumed independent source groups, heterogeneous horizons/units and conditional interval shading.

![Other retained Lu choices](../../figures/exploratory/lu_model_sensitivity.png)

{wa} Categorical model choices, one Lu per four-source fit; no clinical ranking is implied.

![Diagnostic joint regions](../../figures/exploratory/diagnostic_joint_summaries.png)

{wd} T05R0, Yu inflation=1, within rho=0; Kenet D=1/5/20; confidence ellipses are conditional, not HSROC or prediction curves.

![Diagnostic covariance/design-effect sensitivity](../../figures/exploratory/diagnostic_sensitivity.png)

{wd} Diagnostic graph data are compared with the saved prior run. These figures are not included in the short LaTeX report.

## Limitations and conclusion

{LIMIT_A} {LIMIT_D} Possible Dallas overlap, Kenet adults, missing external validation and protocol discrepancies remain. No new sources or independently reviewed evidence were added. Replacing the excluded Lu index with logistic regression changes the core AUROC calculations; the diagnostic results remain unchanged because Lu did not contribute count tables. The additional Lu grid measures selection sensitivity without multiplying independent cohorts. Numerical stability, conditional precision or a high AUROC does not establish clinical accuracy, missed-patient rates, alarm burden or deployment safety.

## Methods and reproducibility

See [methods](meta_analysis_methods.md), [all AUROC results](auroc_meta_analysis.md), [all diagnostic results](diagnostic_meta_analysis.md), [Lu model sensitivity](lu_model_sensitivity.md), [limitations](assumptions_and_limitations.md), and [before/after comparison](../revisions/exclusion_comparison.md). The configuration, input ledgers and manifests retain every assumption and source record. Run `make revised` for the full validated workflow. Statistical checks completed: {len(checks)}; actual full test results and versions are in execution manifests. Historical and current integrity records are both enforced.
'''
    write_md(reports/'exploratory_results_summary.md',document)
    write_md(reports/'consolidated_exploratory_report.md',document)
