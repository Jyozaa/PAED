import math
import pytest
from paed.clean import proportion,count,rates,parse_auroc,parse_operating_point
from paed.ingest import missing_state

@pytest.mark.parametrize('raw,expected',[('73.29%',.7329),('0.7329',.7329),('73.29',.7329),('0',0),('0%',0),('100%',1),('NR',None),('',None),('N/A',None)])
def test_proportion_conversion(raw,expected):
    if expected is None:assert proportion(raw) is None
    else:assert proportion(raw)==pytest.approx(expected,abs=1e-12)

@pytest.mark.parametrize('raw',['101%','-1%','0.8; 0.9','about 90%'])
def test_reject_ambiguous_or_invalid_percent(raw):
    with pytest.raises(ValueError):proportion(raw)

@pytest.mark.parametrize('raw,state',[('', 'missing'),('NR','not_reported'),('NR - pending','not_reported'),('N/A','not_applicable'),('ambiguous','ambiguous'),('0','observed_zero'),('0.5','observed')])
def test_missing_states(raw,state):assert missing_state(raw)==state


def test_unspecified_variation_not_se():
    x=parse_auroc('73.29 ± 2.47')[0]
    assert x['auroc']==pytest.approx(.7329)
    assert x['reported_variation']==pytest.approx(.0247)
    assert x['uncertainty_type']=='unspecified_plus_minus' and x['se_logit_approx'] is None


def test_real_ci_and_logit_variance():
    x=parse_auroc('0.85 [95% CI 0.79, 0.90] at 1 hour prior to CA (peak performance)')[0]
    assert x['ci_lower']==.79 and x['ci_upper']==.9
    expected=(math.log(.9/.1)-math.log(.79/.21))/(2*1.959963984540054)
    assert x['se_logit_approx']==pytest.approx(expected)
    assert x['horizon']=='1h'


def test_all_named_horizons_parsed():
    x=parse_auroc('0.989 (8hr); 0.979 (4hr); 0.979 (2hr); 0.980 (1hr)')
    assert [v['horizon'] for v in x]==['8h','4h','2h','1h']
    assert [v['auroc'] for v in x]==[.989,.979,.979,.98]


def test_training_and_test_not_silently_collapsed():
    x=parse_auroc('0.91 (training set); 0.75 (test set)')
    assert len(x)==2 and x[0]['evaluation']=='training' and x[1]['auroc']==.75
    assert len(parse_operating_point('74.1% (test set); 80.2% (entire dataset)'))==2


def test_complex_unknown_auroc_requires_review():
    with pytest.raises(ValueError):parse_auroc('0.80 or 0.90 with a 2-hour event window')
    with pytest.raises(ValueError):parse_auroc('0.85 [95% CI 0.90, 0.79] at 1 hour prior to CA')


def test_2x2_correct_formulas_and_zero_denominators():
    x=rates(36,63,4,115)
    assert x['sensitivity_recalculated']==.9
    assert x['specificity_recalculated']==pytest.approx(115/178)
    assert x['ppv_recalculated']==pytest.approx(36/99)
    assert x['npv_recalculated']==pytest.approx(115/119)
    assert x['total_units']==218
    assert rates(0,0,0,0)['sensitivity_recalculated'] is None
    assert count('0')==0 and count('NR') is None
    for invalid in [(-1,0,1,1),(1.5,1,2,3),(None,1,2,3)]:
        with pytest.raises(ValueError):rates(*invalid)
    with pytest.raises(ValueError):count('3.2')


def test_agreed_exclusions_and_cross_reference(evidence):
    assert len(evidence['audit'])==27 and len(evidence['models'])==17
    assert len({r['study_id'] for r in evidence['models']})==5
    assert not any(r['study_id']=='yu_2026' or r['model_id'] in {'yu_2023_gnb','lu_2025_xgboost','lu_2025_gmlp','lu_2025_pedca_ft'} for r in evidence['models'])
    assert sum(x['study_id']=='yu_2026' for x in evidence['excluded'])==5
    assert next(x for x in evidence['excluded'] if x['source_row']==21)['record_type']=='cross_reference'
    assert any(r['study_id']=='kenet_2023' for r in evidence['models'])


def test_cohort_overlap_and_windows(evidence):
    dallas={r['dependency_group'] for r in evidence['models'] if r['study_id'] in ['yu_2022','yu_2023']}
    assert len(dallas)==1
    k=[r for r in evidence['diagnostic'] if r['study_id']=='kenet_2023']
    assert len(k)==6 and all(r['total_units']==3059 and r['positive_units']==211 for r in k)
    assert all(r['analysis_unit']=='repeated_5_minute_window' for r in k)
    assert all(r['ci_status'].startswith('withheld') for r in k)
    assert any(r['code']=='WINDOW_EVENT_COUNT_RECONCILIATION' for r in evidence['flags'])


def test_rounding_and_actual_discrepancy(evidence):
    flags=[r for r in evidence['flags'] if r['code']=='REPORTED_RECALCULATED_DISCREPANCY']
    assert len(flags)==1 and flags[0]['model_id']=='kenet_2023_random_forest' and flags[0]['metric']=='specificity'
    yu=next(r for r in evidence['diagnostic'] if r['study_id']=='yu_2023')
    assert yu['specificity_within_tolerance'] and yu['ppv_within_tolerance'] and yu['npv_within_tolerance']
    assert not yu['pairing_with_auroc_verified'] and yu['table_model_attribution']=='assumed_by_extractor'


def test_all_estimates_traceable_no_imputed_variance(evidence):
    for family in ['auroc','diagnostic','operating']:
        for r in evidence[family]:
            for field in ['study_id','model_id','source_row','metric_source','prediction_horizon','validation_type','cohort_id','dependency_group','analysis_unit']:
                assert r[field] is not None and r[field]!=''
    a=evidence['auroc']
    assert len(a)==18 and sum(r['ci_lower'] is not None for r in a)==1
    assert sum(r['uncertainty_type']=='unspecified_plus_minus' for r in a)==8
    assert all(r['se_logit_approx'] is None for r in a if r['ci_lower'] is None)
