import json
import pytest
from paed.analysis import assert_independent,gate_auroc,gate_diagnostic,feasibility


def test_pooling_dependent_rows_forbidden(evidence):
    with pytest.raises(ValueError,match='Non-independent'):assert_independent(evidence['auroc'])
    with pytest.raises(ValueError,match='Non-independent'):assert_independent(evidence['diagnostic'])
    dallas=[next(r for r in evidence['auroc'] if r['study_id']==sid) for sid in ['yu_2022','yu_2023']]
    with pytest.raises(ValueError):assert_independent(dallas)
    with pytest.raises(ValueError):assert_independent([{'dependency_group':''}])


def test_missing_variance_cannot_pass_with_many_models():
    rows=[{'dependency_group':str(i),'se_logit_approx':None,'selection_confirmed':True,'comparability_confirmed':True} for i in range(20)]
    assert 'Missing valid sampling variance' in gate_auroc(rows)
    for r in rows:r.update(se_logit_approx=.1,uncertainty_type='unspecified_plus_minus')
    assert 'Genuine uncertainty type not established' in gate_auroc(rows)


def test_explicit_selection_and_comparability_required():
    rows=[{'dependency_group':str(i),'se_logit_approx':.1,'uncertainty_type':'95%_confidence_interval'} for i in range(3)]
    assert 'Representative model/horizon selection unresolved' in gate_auroc(rows)
    for r in rows:r.update(selection_confirmed=True,comparability_confirmed=True,evaluation='internal_held_out_test')
    assert gate_auroc(rows)==[]
    rows[0]['evaluation']='training'
    assert 'Training performance cannot represent independent validation' in gate_auroc(rows)


def test_windows_never_treated_as_independent_patients():
    rows=[{'dependency_group':str(i),'analysis_unit':'repeated_5_minute_window','selection_confirmed':True,
           'comparability_confirmed':True,'model_threshold_unit_linkage_verified':True,'tp':10,'fp':10,'fn':1,'tn':100} for i in range(6)]
    assert 'Independent binomial analysis unit not established' in gate_diagnostic(rows)
    for r in rows:r['analysis_unit']='patient'
    assert gate_diagnostic(rows)==[]
    rows[0]['model_threshold_unit_linkage_verified']=False
    assert 'Model/threshold/horizon linkage unresolved' in gate_diagnostic(rows)


def test_real_evidence_correctly_gated(evidence,project):
    c=json.loads((project/'config/study_context.json').read_text());config=json.loads((project/'config/analysis.json').read_text())
    status,_=feasibility(evidence,c,config)
    assert status['auroc']['variance_bearing_independent_cohorts']==1
    assert status['diagnostic']['source_cohort_groups']==2
    assert status['diagnostic']['eligible_datasets']==0
    assert status['strict_protocol']['demonstrated_eligible_studies']==0
    assert status['strict_protocol']['with_setting_requirement_only_models']==14
    assert not status['auroc']['pooled_estimate_produced'] and not status['diagnostic']['pooled_estimate_produced']
