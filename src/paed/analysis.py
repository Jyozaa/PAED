"""Feasibility is an analysis outcome, not an optimization error."""
from itertools import combinations
import math


def assert_independent(records):
    groups=[r['dependency_group'] for r in records]
    if any(not x for x in groups):
        raise ValueError('Missing dependency group; independence cannot be established')
    if len(set(groups))!=len(groups):
        raise ValueError('Non-independent model rows or overlapping cohorts: one per dependency group required')


def gate_auroc(records, minimum=3):
    reasons=[]
    if len(records)<minimum:reasons.append(f'Fewer than {minimum} eligible independent estimates')
    assert_independent(records)
    for r in records:
        if r.get('se_logit_approx') is None or not math.isfinite(r['se_logit_approx']) or r['se_logit_approx']<=0:
            reasons.append('Missing valid sampling variance')
        if r.get('uncertainty_type') not in {'95%_confidence_interval','standard_error'}:reasons.append('Genuine uncertainty type not established')
        if r.get('evaluation')=='training':reasons.append('Training performance cannot represent independent validation')
        if not r.get('selection_confirmed',False):reasons.append('Representative model/horizon selection unresolved')
        if not r.get('comparability_confirmed',False):reasons.append('Clinical/validation/horizon comparability not established')
    return sorted(set(reasons))


def gate_diagnostic(records, minimum=5):
    reasons=[]
    if len(records)<minimum:reasons.append(f'Fewer than {minimum} eligible independent datasets')
    assert_independent(records)
    for r in records:
        if r.get('analysis_unit') not in {'patient','admission_independent','event_independent'}:
            reasons.append('Independent binomial analysis unit not established')
        if not r.get('model_threshold_unit_linkage_verified',False):reasons.append('Model/threshold/horizon linkage unresolved')
        if not r.get('comparability_confirmed',False):reasons.append('Clinical comparability not established')
        if not r.get('selection_confirmed',False):reasons.append('Representative operating-point selection unresolved')
        counts=[r.get(k) for k in ['tp','fp','fn','tn']]
        if any(x is None or not isinstance(x,int) or x<0 for x in counts):reasons.append('Complete nonnegative integer counts required')
    return sorted(set(reasons))


def feasibility(data, contexts, config):
    a=data['auroc'];d=data['diagnostic'];m=data['models']
    selection=[]
    for sid in dict.fromkeys(r['study_id'] for r in m):
        c=contexts[sid]; candidates=[r for r in a if r['study_id']==sid]
        usable=[r for r in candidates if r['sampling_variance_available']]
        selected=[r for r in candidates if r['model_id']==c['representative_model'] and r['evaluation']!='training']
        selection.append({'study_id':sid,'dependency_group':c['dependency_group'],
                          'representative_model':c['representative_model'],'selection_reason':c['selection_reason'],
                          'selected_candidate_estimate_ids':';'.join(x['estimate_id'] for x in selected),
                          'genuine_variance_estimates':len(usable),'pooled_eligible':False,
                          'reason':'Only one variance-bearing cohort in entire dataset' if usable else 'No usable genuine AUROC variance'})
    statuses={
      'auroc':{'status':'not_statistically_defensible','pooled_estimate_produced':False,'pooled_estimate':None,
               'retained_studies':len({r['study_id'] for r in m}),'retained_models':len(m),
               'point_estimates':len(a),'model_estimates_with_numerical_auroc':len({r['model_id'] for r in a}),
               'genuine_95ci_estimates':sum(r['uncertainty_type']=='95%_confidence_interval' for r in a),
               'variance_bearing_independent_cohorts':len({r['dependency_group'] for r in a if r['sampling_variance_available']}),
               'potential_dependency_groups':len({r['dependency_group'] for r in a}),
               'contributing_independent_studies':0,'contributing_model_estimates':0,
               'analysis_unit':'heterogeneous admission, minute-score, hourly and repeated-window evaluations',
               'gate_reasons':gate_auroc([],config['minimum_auroc_independent_cohorts'])+
                 [f'Only Yu 2023 has a supplied genuine CI; {sum(r["study_id"]=="lu_2025" and r["uncertainty_type"]=="unspecified_plus_minus" for r in a)} retained Lu +/- values have unspecified meaning',
                  'Yu 2022/2023 may reuse patients; no covariance supplied',
                  'Different horizons/units/validation types; Kenet representative-model selection unresolved'],
               'estimator_if_eligible':'R metafor::rma.uni REML on logit AUROC, modified Hartung-Knapp t CI',
               'fitting_attempt':'Feasibility gate executed; inferential optimizer intentionally not invoked'},
      'diagnostic':{'status':'not_statistically_defensible','pooled_estimate_produced':False,'pooled_estimate':None,
                    'candidate_complete_tables':len(d),'source_studies':len({r['study_id'] for r in d}),
                    'source_cohort_groups':len({r['dependency_group'] for r in d}),
                    'independent_patient_level_tables_confirmed':0,'eligible_datasets':0,
                    'contributing_independent_studies':0,'contributing_model_estimates':0,
                    'analysis_unit':'six repeated five-minute-window tables; one representative-fold table with unresolved unit',
                    'gate_reasons':gate_diagnostic([],config['minimum_bivariate_independent_cohorts'])+
                      ['Six Kenet models share the same 3059 windows from 229 test patients (5 CA); no clustering adjustment',
                       'Yu 2023 representative fold has 218 units; model attribution, threshold and horizon unresolved',
                       'Even optimistic study-source independence gives only two sources for five bivariate location/covariance parameters'],
                    'estimator_if_eligible':'R mada::reitsma REML bivariate model for interior independent proportions; binomial HSROC required for sparse boundary data',
                    'fitting_attempt':'Feasibility gate executed; no convergence result claimed'},
      'strict_protocol':{'demonstrated_eligible_studies':0,'demonstrated_eligible_models':0,
                         'interpretation':'No retained study demonstrates all strict criteria in supplied extraction; NR is not proof external validation never occurred',
                         'with_setting_requirement_only_studies':sum(c['setting_class']=='CICU' for c in contexts.values() if c['working_eligible']),
                         'with_setting_requirement_only_models':sum(contexts[r['study_id']]['setting_class']=='CICU' for r in m)}
    }
    return statuses,selection


def heterogeneity(contexts):
    studies=[sid for sid,c in contexts.items() if c['working_eligible']]
    rows=[]
    for left,right in combinations(studies,2):
        a,b=contexts[left],contexts[right]
        same=a['dependency_group']==b['dependency_group']
        rows.append({'study_1':left,'study_2':right,'setting_comparable':a['setting_class']==b['setting_class'],
                     'analysis_unit_comparable':a['unit']==b['unit'],'horizon_comparable':left.startswith('yu_') and right.startswith('yu_'),
                     'same_dependency_group':same,'independence':'potential_overlap' if same else 'no_overlap_identified_not_proven',
                     'pooling_supported':False,'reason':'Probable patient overlap; covariance unknown' if same else 'Different units/horizons, incomplete variance and/or unverified thresholds',
                     'comparison':'Contextual descriptive comparison only'})
    return rows
