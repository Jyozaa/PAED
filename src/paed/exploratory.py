"""Explicitly hypothetical pooling; the evidence-supported gates are unchanged.

AUROC: established statsmodels Paule-Mandel implementation with an independently
checked estimating equation and modified Hartung-Knapp t interval.
Diagnostic: closed-form GLS of paired sensitivity/FPR logits with known-assumed
within-source covariance and prespecified between-source covariance.
"""
from itertools import product
import json
import math
import warnings
import numpy as np
from scipy.special import expit,logit
from scipy.optimize import brentq
from scipy.stats import norm,t,chi2
from statsmodels.stats.meta_analysis import combine_effects
from .analysis import assert_independent

CLASS='exploratory_conditional'
LIMIT_A='Hypothetical missing SEs; four source groups assumed independent; heterogeneous tools, horizons, units and internal validation; not validated clinical accuracy.'
LIMIT_D='Two source summaries; Kenet clustered windows and mixed-age sample; Yu attribution/unit/threshold/horizon unresolved; all covariance assumptions conditional; not validated patient-level accuracy.'


def auroc_scenarios(config):
    c=config['auroc'];core=c['core_lu_estimate_id']
    other_fixed=[x for x in c['fixed_estimate_ids'] if x!=core]
    if len(other_fixed)!=1:raise ValueError('One fixed Bose estimate must accompany the selected Lu estimate')
    for lu in [core,*c['additional_lu_alternatives']]:
        family='core_lu_logistic' if lu==core else 'alternative_lu_model'
        prefix='' if lu==core else 'LU_'+lu.removeprefix('lu_2025_').removesuffix('_a1')+'_'
        for dallas,kenet,se in product(c['dallas_alternatives'],c['kenet_alternatives'],c['assumed_auroc_scale_ses']):
            yield {'scenario_id':f'A_{prefix}{dallas.split("_")[1]}_{kenet.removeprefix("kenet_2023_").removesuffix("_a1")}_SE{round(se*100):02d}',
                   'scenario_family':family,'lu_estimate_id':lu,
                   'estimate_ids':[lu,*other_fixed,dallas,kenet],
                   'dallas_estimate_id':dallas,'kenet_estimate_id':kenet,'assumed_se_auroc':se,
                   'initial_selection':lu==core and dallas==c['initial_dallas'] and kenet==c['initial_kenet']}


def diagnostic_scenarios(config):
    c=config['diagnostic']
    for model,de,yu,tau in product(c['kenet_models'],c['kenet_design_effects'],c['yu_variance_inflations'],c['between_source_covariances']):
        yield {'scenario_id':f'D_{model.removeprefix("kenet_2023_")}_K{de}_Y{yu}_{tau["id"]}_W0',
               'kenet_model_id':model,'yu_model_id':c['yu_model'],'kenet_design_effect':de,
               'yu_variance_inflation':yu,'between_covariance_id':tau['id'],
               'sd_sensitivity_assumed':tau['sd_sensitivity'],'sd_fpr_assumed':tau['sd_fpr'],
               'rho_between_assumed':tau['correlation'],'rho_within_assumed':c['primary_within_correlation'],
               'scenario_family':'primary_covariance_grid'}
    extra=c['within_correlation_sensitivity']
    tau=next(x for x in c['between_source_covariances'] if x['id']==extra['between_covariance_id'])
    for model,rho in product(c['kenet_models'],extra['alternative_correlations']):
        yield {'scenario_id':f'D_{model.removeprefix("kenet_2023_")}_K{extra["kenet_design_effect"]}_Y{extra["yu_variance_inflation"]}_{tau["id"]}_W{rho:+.1f}',
               'kenet_model_id':model,'yu_model_id':c['yu_model'],'kenet_design_effect':extra['kenet_design_effect'],
               'yu_variance_inflation':extra['yu_variance_inflation'],'between_covariance_id':tau['id'],
               'sd_sensitivity_assumed':tau['sd_sensitivity'],'sd_fpr_assumed':tau['sd_fpr'],
               'rho_between_assumed':tau['correlation'],'rho_within_assumed':rho,
               'scenario_family':'focused_within_correlation_sensitivity'}


def select_auroc(rows,scenario,config):
    selected=[]
    for ident in scenario['estimate_ids']:
        candidates=[r for r in rows if r['estimate_id']==ident]
        if len(candidates)!=1:raise ValueError(f'Expected exactly one AUROC evaluation: {ident}')
        r=dict(candidates[0]);p=float(r['auroc'])
        if not 0<p<1 or r['evaluation']=='training':raise ValueError('Interior nontraining AUROC required')
        genuine=r['uncertainty_type']=='95%_confidence_interval' and r.get('se_logit_approx') is not None
        if genuine:
            se=float(r['se_logit_approx']);source='genuine_ci_endpoint_approximation';assumed=None
            lower=float(r['ci_lower']);upper=float(r['ci_upper']);raw_se=float(r['se_raw_approx'])
        else:
            raw_se=float(scenario['assumed_se_auroc'])
            if raw_se<=0 or not np.isfinite(raw_se):raise ValueError('Positive finite hypothetical SE required')
            se=raw_se/(p*(1-p));source='assumed_not_study_estimated';assumed=raw_se
            z=norm.ppf(1-config['alpha']/2);lower=float(expit(logit(p)-z*se));upper=float(expit(logit(p)+z*se))
        if not np.isfinite(se) or se<=0:raise ValueError('Invalid transformed SE')
        r.update(analysis_class=CLASS,scenario_id=scenario['scenario_id'],logit_auroc=float(logit(p)),
                 se_logit_used=se,se_auroc_used=raw_se,uncertainty_origin=source,assumed_se_auroc=assumed,
                 conditional_plot_lower=lower,conditional_plot_upper=upper,
                 original_plus_minus_used_as_se=False,source_group_independence='assumed',limitations=LIMIT_A)
        selected.append(r)
    assert_independent(selected)
    if len(selected)!=4:raise ValueError('Each configured AUROC scenario must contain four source groups')
    return selected


def fit_auroc(selected,config):
    assert_independent(selected)
    c=config['auroc'];k=len(selected)
    if c['method']!='Paule-Mandel':raise ValueError('Unsupported configured AUROC estimator')
    if k<3:raise ValueError('At least three independent source groups required in AUROC scenarios')
    y=np.array([r['logit_auroc'] for r in selected]);v=np.array([r['se_logit_used']**2 for r in selected])
    if not np.all(np.isfinite(y)) or not np.all(np.isfinite(v)) or np.any(v<=0):raise ValueError('Invalid effect/variance')
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        fit=combine_effects(y,v,method_re='iterated',use_t=True,tau2_start=c['tau2_start'],atol=c['tau2_atol'],maxiter=c['tau2_maxiter'])
    tau=float(fit.tau2);mu=float(fit.mean_effect_re);w=1/(v+tau)
    q=float(np.dot(w,(y-mu)**2));boundary=tau<=c['boundary_tolerance']
    valid=(tau>=0 and np.isfinite(tau) and ((boundary and q<=k-1+c['equation_check_tolerance']) or abs(q-(k-1))<=c['equation_check_tolerance']))
    primary_error='';fallback_used=False;fallback_iterations=None
    if not valid:
        primary_error=f'Library PM residual check failed: tau2={tau}, Q_tau={q}'
        fallback_used=True
        def equation(value):
            wi=1/(v+value);mean=float(np.dot(wi,y)/wi.sum())
            return float(np.dot(wi,(y-mean)**2)-(k-1))
        upper=c['fallback_initial_upper']
        for _ in range(c['fallback_max_expansions']):
            if equation(upper)<0:break
            upper*=2
        else:raise ArithmeticError(primary_error+'; fallback could not bracket root')
        tau,details=brentq(equation,0,upper,xtol=c['fallback_xtol'],rtol=c['fallback_rtol'],maxiter=c['tau2_maxiter'],full_output=True)
        w=1/(v+tau);mu=float(np.dot(w,y)/w.sum());q=float(np.dot(w,(y-mu)**2));boundary=tau<=c['boundary_tolerance']
        fallback_iterations=int(details.iterations)
        if not details.converged or abs(q-(k-1))>c['equation_check_tolerance']:
            raise ArithmeticError(primary_error+'; fallback failed residual check')
    base_var=float(1/w.sum());hk_var=float(q/((k-1)*w.sum()));conditional_var=max(base_var,hk_var)
    z=float(t.ppf(1-config['alpha']/2,k-1));se=math.sqrt(conditional_var)
    low=mu-z*se;high=mu+z*se
    result={'analysis_class':CLASS,'status':'success_conditional','converged':True,'fit_method':'Paule-Mandel (statsmodels)',
            'k_source_groups_assumed_independent':k,'fallback_used':fallback_used,
            'primary_solver_error':primary_error,'fallback_iterations':fallback_iterations,
            'solver':'statsmodels_iterated_PM' if not fallback_used else 'scipy_brentq_same_PM_equation','model_ids':';'.join(r['model_id'] for r in selected),
            'dependency_groups':';'.join(r['dependency_group'] for r in selected),
            'genuine_variance_count':sum(r['uncertainty_origin'].startswith('genuine') for r in selected),
            'assumed_variance_count':sum(r['uncertainty_origin'].startswith('assumed') for r in selected),
            'pooled_auroc':float(expit(mu)),'conditional_95_lower':float(expit(low)),
            'conditional_95_upper':float(expit(high)),'pooled_logit':mu,'conditional_variance_logit':conditional_var,
            'conditional_se_logit':se,'df':k-1,'interval_method':'modified Hartung-Knapp t',
            'tau2_logit_estimated':tau,'tau_logit_estimated':math.sqrt(tau),
            'tau2_boundary':boundary,'Q_fixed_variance':float(fit.q),'Q_at_tau2':q,
            'pm_equation_residual':q-(k-1),'conventional_variance_logit':base_var,'hk_variance_logit':hk_var,
            'hk_scale_floor_applied':hk_var<base_var,'critical_value':z,
            'numerical_warnings':'; '.join(str(x.message) for x in captured),
            'diagnostic_note':'valid boundary at tau2=0' if boundary else 'positive PM root verified',
            'limitations':LIMIT_A,'figure_warning':c['warning']}
    for r,wi in zip(selected,w/w.sum()):r['random_effects_weight']=float(wi)
    return result


def covariance(sd1,sd2,rho):
    if not all(np.isfinite(x) for x in [sd1,sd2,rho]) or sd1<0 or sd2<0 or abs(rho)>=1:
        raise ValueError('Nonnegative SDs and absolute correlation <1 required')
    return np.array([[sd1*sd1,rho*sd1*sd2],[rho*sd1*sd2,sd2*sd2]],dtype=float)


def table_covariance(row,inflation,rho):
    values=[row[k] for k in ['tp','fp','fn','tn']]
    if any(isinstance(x,bool) or not np.isfinite(x) or x<=0 or int(x)!=x for x in values):
        raise ValueError('Positive integer source counts required; no count alteration or continuity correction')
    if not np.isfinite(inflation) or inflation<1:raise ValueError('Variance inflation must be at least one')
    tp,fp,fn,tn=values
    v1=inflation*(1/tp+1/fn);v2=inflation*(1/fp+1/tn)
    return covariance(math.sqrt(v1),math.sqrt(v2),rho)


def fit_diagnostic(rows,scenario,config):
    if len(rows)!=2:raise ValueError('Exactly one Kenet and one Yu source table required')
    assert_independent(rows)
    if {r['model_id'] for r in rows}!={scenario['kenet_model_id'],scenario['yu_model_id']}:
        raise ValueError('Configured source models do not match selected tables')
    d=config['diagnostic'];T=covariance(scenario['sd_sensitivity_assumed'],scenario['sd_fpr_assumed'],scenario['rho_between_assumed'])
    precisions=[];effects=[];inputs=[];min_eigen=[];condition=[]
    for r in rows:
        factor=scenario['kenet_design_effect'] if r['study_id']=='kenet_2023' else scenario['yu_variance_inflation']
        S=table_covariance(r,factor,scenario['rho_within_assumed']);V=S+T
        eig=np.linalg.eigvalsh(V)
        if np.min(eig)<=0:raise ArithmeticError('Non-positive definite total source covariance')
        P=np.linalg.inv(V);z=np.array([math.log(r['tp']/r['fn']),math.log(r['fp']/r['tn'])])
        precisions.append(P);effects.append(z);min_eigen.append(float(min(eig)));condition.append(float(np.linalg.cond(V)))
        inp={k:r[k] for k in ['study_id','model_id','source_row','dependency_group','analysis_unit','threshold','table_horizon','table_model_attribution','tp','fp','fn','tn']}
        inp.update(analysis_class=CLASS,scenario_id=scenario['scenario_id'],variance_inflation_assumed=factor,
                   rho_within_assumed=scenario['rho_within_assumed'],logit_sensitivity=float(z[0]),logit_fpr=float(z[1]),
                   source_counts_altered=False,sampling_var_logit_sensitivity_assumed=float(S[0,0]),
                   sampling_cov_logits_assumed=float(S[0,1]),sampling_var_logit_fpr_assumed=float(S[1,1]),
                   total_var_logit_sensitivity=float(V[0,0]),total_cov_logits=float(V[0,1]),total_var_logit_fpr=float(V[1,1]),
                   limitations=LIMIT_D)
        inputs.append(inp)
    precision=sum(precisions);C=np.linalg.inv(precision);rhs=sum(P@z for P,z in zip(precisions,effects));mu=np.linalg.solve(precision,rhs)
    residual=float(np.linalg.norm(precision@mu-rhs));condition.append(float(np.linalg.cond(precision)))
    if residual>d['normal_equation_tolerance'] or not np.all(np.isfinite(mu)) or np.min(np.linalg.eigvalsh(C))<=0:
        raise ArithmeticError('GLS solution failed numerical validation')
    critical=float(norm.ppf(1-config['alpha']/2));ses=np.sqrt(np.diag(C))
    sens=float(expit(mu[0]));spec=float(expit(-mu[1]))
    q=float(sum((z-mu)@P@(z-mu) for P,z in zip(precisions,effects)))
    warning=[]
    if min(min(r[k] for k in ['tp','fp','fn','tn']) for r in rows)<d['minimum_cell_warning']:
        warning.append('Small cell count (<5): normal-logit sampling approximation may be poor')
    if max(condition)>d['condition_number_warning']:warning.append('Ill-conditioned covariance/precision')
    if q>chi2.ppf(1-config['alpha'],2):warning.append('Large conditional residual discrepancy under supplied covariance assumptions')
    result={**scenario,'analysis_class':CLASS,'status':'success_conditional','converged':True,
            'method':'joint normal-logit GLS with prespecified between-source covariance',
            'numerical_method':'closed-form linear solve; no iterative convergence needed','source_studies':'kenet_2023;yu_2023',
            'k_source_groups_assumed_independent':2,'summary_sensitivity':sens,
            'sensitivity_conditional_95_lower':float(expit(mu[0]-critical*ses[0])),
            'sensitivity_conditional_95_upper':float(expit(mu[0]+critical*ses[0])),
            'summary_specificity':spec,'specificity_conditional_95_lower':float(expit(-mu[1]-critical*ses[1])),
            'specificity_conditional_95_upper':float(expit(-mu[1]+critical*ses[1])),
            'mu_logit_sensitivity':float(mu[0]),'mu_logit_fpr':float(mu[1]),
            'summary_cov_11':float(C[0,0]),'summary_cov_12':float(C[0,1]),'summary_cov_22':float(C[1,1]),
            'T11_assumed':float(T[0,0]),'T12_assumed':float(T[0,1]),'T22_assumed':float(T[1,1]),
            'heterogeneity_estimated':False,'normal_equation_residual':residual,'max_condition_number':max(condition),
            'minimum_total_covariance_eigenvalue':min(min_eigen),'Q_conditional':q,
            'residual_df_under_known_covariance':2,'critical_value':critical,
            'numerical_warnings':'; '.join(warning),'limitations':LIMIT_D,'figure_warning':d['warning']}
    for inp,P in zip(inputs,precisions):
        A=C@P
        inp.update({f'GLS_weight_matrix_{i+1}{j+1}':float(A[i,j]) for i in range(2) for j in range(2)})
    return result,inputs


def safe_fit(kind,scenario,operation):
    """Retain every failed scenario with no successful pooled numerical fields."""
    try:return operation()
    except (ValueError,ArithmeticError,np.linalg.LinAlgError,RuntimeError) as exc:
        fail={**scenario,'analysis_class':CLASS,'status':'failed_not_pooled','converged':False,
              'error_type':type(exc).__name__,'error_message':str(exc),'limitations':LIMIT_A if kind=='auroc' else LIMIT_D}
        return (fail,[])


def execute(auroc_rows,table_rows,config):
    A=[];AI=[];D=[];DI=[]
    for scenario in auroc_scenarios(config):
        def operation():
            chosen=select_auroc(auroc_rows,scenario,config)
            return {**scenario,**fit_auroc(chosen,config)},chosen
        result,inputs=safe_fit('auroc',scenario,operation);A.append(result);AI.extend(inputs)
    for scenario in diagnostic_scenarios(config):
        def operation():
            chosen=[]
            for model in [scenario['yu_model_id'],scenario['kenet_model_id']]:
                matches=[r for r in table_rows if r['model_id']==model]
                if len(matches)!=1:raise ValueError('Exactly one extracted diagnostic table per configured model required')
                chosen.append(dict(matches[0]))
            return fit_diagnostic(chosen,scenario,config)
        result,inputs=safe_fit('diagnostic',scenario,operation);D.append(result);DI.extend(inputs)
    return {'auroc_results':A,'auroc_inputs':AI,'diagnostic_results':D,'diagnostic_inputs':DI}
