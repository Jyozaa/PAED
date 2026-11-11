"""Independent analytical checks plus complete scenario/output preservation tests."""
import copy
import json
from pathlib import Path
import numpy as np
import pytest
from scipy.optimize import brentq
from scipy.special import expit,logit
from scipy.stats import t,chi2,norm
from paed.exploratory import (CLASS,auroc_scenarios,diagnostic_scenarios,select_auroc,fit_auroc,
    fit_diagnostic,table_covariance,covariance,safe_fit,execute)
from paed.exploratory_pipeline import read,baseline_checks,run,verify
from paed.exploratory_figures import joint_ellipse


@pytest.fixture(scope='module')
def config():
    return json.loads((Path(__file__).resolve().parents[1]/'config/exploratory_scenarios.json').read_text())

@pytest.fixture(scope='module')
def source():
    root=Path(__file__).resolve().parents[1]
    return read(root/'results/auroc_estimates.csv'),read(root/'results/diagnostic_2x2.csv')

@pytest.fixture(scope='module')
def scenarios(source,config):return execute(*source,config)


def test_all_scenarios_and_labels_present(scenarios,config):
    assert len(list(auroc_scenarios(config)))==18
    assert len(list(diagnostic_scenarios(config)))==96
    for key in ['auroc_results','diagnostic_results']:
        rows=scenarios[key]
        assert len({r['scenario_id'] for r in rows})==len(rows)
        assert all(r['analysis_class']==CLASS and r['status']=='success_conditional' and r['figure_warning'].startswith('EXPLORATORY —') for r in rows)


def test_one_model_per_dependency_group_no_training_or_overlap(scenarios):
    for scenario in scenarios['auroc_results']:
        rows=[r for r in scenarios['auroc_inputs'] if r['scenario_id']==scenario['scenario_id']]
        assert len(rows)==4 and len({r['dependency_group'] for r in rows})==4
        assert not {'yu_2022','yu_2023'}.issubset({r['study_id'] for r in rows})
        assert sum(r['study_id']=='kenet_2023' for r in rows)==1
        assert not any(r['evaluation']=='training' for r in rows)
    for scenario in scenarios['diagnostic_results']:
        rows=[r for r in scenarios['diagnostic_inputs'] if r['scenario_id']==scenario['scenario_id']]
        assert len(rows)==2 and sum(r['study_id']=='kenet_2023' for r in rows)==1


def test_attempt_to_double_count_dallas_is_rejected(source,config):
    scenario=next(auroc_scenarios(config));scenario['estimate_ids'][-1]='yu_2022_logistic_a1'
    with pytest.raises(ValueError,match='Non-independent'):select_auroc(source[0],scenario,config)


def test_assumed_se_tags_genuine_ci_preserved_no_lu_plusminus(scenarios,source):
    original={r['estimate_id']:r for r in source[0]}
    for r in scenarios['auroc_inputs']:
        if r['study_id']=='yu_2023':
            assert r['uncertainty_origin']=='genuine_ci_endpoint_approximation'
            assert r['se_logit_used']==original[r['estimate_id']]['se_logit_approx']
            assert r['assumed_se_auroc'] is None
            assert r['conditional_plot_lower']==.79 and r['conditional_plot_upper']==.90
        else:
            assert r['uncertainty_origin']=='assumed_not_study_estimated'
            assert r['se_logit_used']==pytest.approx(r['assumed_se_auroc']/(r['auroc']*(1-r['auroc'])))
        assert not r['original_plus_minus_used_as_se']
        if r['study_id']=='lu_2025':assert r['se_auroc_used']!=r['reported_variation']


def synthetic(y,v):
    return [{'dependency_group':str(i),'model_id':'synthetic_'+str(i),'logit_auroc':float(yi),
             'se_logit_used':float(np.sqrt(vi)),'uncertainty_origin':'assumed_not_study_estimated'} for i,(yi,vi) in enumerate(zip(y,v))]


def test_paule_mandel_equal_variance_analytic_solution(config):
    y=np.array([1.,2.,3.,4.]);v=np.repeat(.1,4)
    r=fit_auroc(synthetic(y,v),config)
    assert r['pooled_logit']==pytest.approx(y.mean())
    assert r['tau2_logit_estimated']==pytest.approx(y.var(ddof=1)-.1,abs=1e-9)
    expected=y.var(ddof=1)/len(y)
    assert r['conditional_variance_logit']==pytest.approx(expected)
    assert r['conditional_95_lower']==pytest.approx(expit(y.mean()-t.ppf(.975,3)*np.sqrt(expected)))


def test_paule_mandel_unequal_variance_independent_root(config):
    y=np.array([1.,1.4,2.8,3.1]);v=np.array([.02,.04,.1,.3])
    def eq(tau):
        w=1/(v+tau);mu=np.dot(w,y)/w.sum();return np.dot(w,(y-mu)**2)-3
    expected=brentq(eq,0,10,xtol=1e-13)
    r=fit_auroc(synthetic(y,v),config)
    assert r['tau2_logit_estimated']==pytest.approx(expected,abs=1e-8)
    assert abs(r['pm_equation_residual'])<1e-7


def test_zero_tau_boundary_has_valid_modified_hk_floor(config):
    r=fit_auroc(synthetic([1.,1.,1.,1.],[.1]*4),config)
    assert r['tau2_logit_estimated']==0 and r['tau2_boundary']
    assert r['hk_variance_logit']==0 and r['conditional_variance_logit']==pytest.approx(.1/4)
    assert r['hk_scale_floor_applied'] and r['df']==3


def test_library_failure_not_silently_accepted(scenarios):
    r=next(r for r in scenarios['auroc_results'] if r['scenario_id']=='A_2022_soft_voting_SE02')
    assert r['status']=='success_conditional'
    # The installed statsmodels iteration can round across the PM root then
    # report tau2=0. Accept either a checked primary root or a documented fallback
    # if a future compatible implementation fixes that numerical path.
    if r['fallback_used']:
        assert 'residual check failed' in r['primary_solver_error']
        assert r['solver']=='scipy_brentq_same_PM_equation' and r['fallback_iterations']>0
    assert r['tau2_logit_estimated']>0 and abs(r['Q_at_tau2']-3)<1e-7


@pytest.mark.parametrize('D',[1,5,20])
def test_design_effect_multiplies_covariance_not_counts(source,D):
    row=next(r for r in source[1] if r['model_id']=='kenet_2023_logistic');before=copy.deepcopy(row)
    base=table_covariance(row,1,.5);inflated=table_covariance(row,D,.5)
    assert np.allclose(inflated,D*base) and row==before


@pytest.mark.parametrize('rho',[-.5,0,.5])
def test_covariance_correlation_orientation(rho):
    S=covariance(.5,1,rho)
    assert S[0,1]==rho*.5 and np.linalg.eigvalsh(S).min()>0
    with pytest.raises(ValueError):covariance(1,1,1)


def test_source_counts_unchanged_and_no_effective_counts(scenarios,source):
    lookup={r['model_id']:r for r in source[1]}
    for r in scenarios['diagnostic_inputs']:
        assert not r['source_counts_altered']
        assert all(r[k]==lookup[r['model_id']][k] for k in ['tp','fp','fn','tn'])
        assert r['analysis_unit']==lookup[r['model_id']]['analysis_unit']


def test_diagonal_gls_matches_two_univariate_known_variance_means(source,config):
    scenario=next(diagnostic_scenarios(config));lookup={r['model_id']:r for r in source[1]}
    rows=[lookup[scenario['yu_model_id']],lookup[scenario['kenet_model_id']]]
    result,_=fit_diagnostic(rows,scenario,config)
    y=np.array([[np.log(r['tp']/r['fn']),np.log(r['fp']/r['tn'])] for r in rows])
    v=np.array([[1/r['tp']+1/r['fn'],1/r['fp']+1/r['tn']] for r in rows])
    w=1/v;mu=(w*y).sum(axis=0)/w.sum(axis=0)
    assert result['mu_logit_sensitivity']==pytest.approx(mu[0])
    assert result['mu_logit_fpr']==pytest.approx(mu[1])
    assert result['summary_cov_11']==pytest.approx(1/w[:,0].sum())
    assert result['summary_cov_22']==pytest.approx(1/w[:,1].sum())


def test_correlated_gls_matches_stacked_linear_model(source,config):
    scenario=next(s for s in diagnostic_scenarios(config) if s['rho_within_assumed']==.5)
    lookup={r['model_id']:r for r in source[1]};rows=[lookup[scenario['yu_model_id']],lookup[scenario['kenet_model_id']]]
    result,inputs=fit_diagnostic(rows,scenario,config)
    V=np.zeros((4,4));y=[]
    for j,r in enumerate(inputs):
        V[2*j:2*j+2,2*j:2*j+2]=[[r['total_var_logit_sensitivity'],r['total_cov_logits']],[r['total_cov_logits'],r['total_var_logit_fpr']]]
        y.extend([r['logit_sensitivity'],r['logit_fpr']])
    X=np.vstack([np.eye(2),np.eye(2)]);P=np.linalg.inv(V);C=np.linalg.inv(X.T@P@X);mu=C@X.T@P@np.array(y)
    assert result['mu_logit_sensitivity']==pytest.approx(mu[0]) and result['mu_logit_fpr']==pytest.approx(mu[1])
    assert np.allclose(C,[[result['summary_cov_11'],result['summary_cov_12']],[result['summary_cov_12'],result['summary_cov_22']]])


def test_more_variance_inflation_cannot_reduce_gls_covariance_at_fixed_T(scenarios):
    rows=scenarios['diagnostic_results']
    for r in rows:
        if r['kenet_design_effect']!=1 or r['scenario_family']!='primary_covariance_grid':continue
        other=next(q for q in rows if q['kenet_model_id']==r['kenet_model_id'] and q['kenet_design_effect']==20 and q['yu_variance_inflation']==r['yu_variance_inflation'] and q['between_covariance_id']==r['between_covariance_id'] and q['rho_within_assumed']==r['rho_within_assumed'])
        matrix=lambda a:np.array([[a['summary_cov_11'],a['summary_cov_12']],[a['summary_cov_12'],a['summary_cov_22']]])
        assert np.linalg.eigvalsh(matrix(other)-matrix(r)).min()>-1e-12


def test_intervals_and_joint_region_are_mathematically_consistent(scenarios):
    for r in scenarios['diagnostic_results']:
        z=norm.ppf(.975)
        assert r['sensitivity_conditional_95_lower']==pytest.approx(expit(r['mu_logit_sensitivity']-z*np.sqrt(r['summary_cov_11'])))
        assert r['specificity_conditional_95_lower']==pytest.approx(expit(-r['mu_logit_fpr']-z*np.sqrt(r['summary_cov_22'])))
        assert r['specificity_conditional_95_upper']==pytest.approx(expit(-r['mu_logit_fpr']+z*np.sqrt(r['summary_cov_22'])))
        xy=joint_ellipse(r);latent=np.column_stack([logit(xy[:,1]),logit(xy[:,0])])
        residual=latent-[r['mu_logit_sensitivity'],r['mu_logit_fpr']]
        C=np.array([[r['summary_cov_11'],r['summary_cov_12']],[r['summary_cov_12'],r['summary_cov_22']]])
        distances=np.einsum('ij,jk,ik->i',residual,np.linalg.inv(C),residual)
        assert np.allclose(distances,chi2.ppf(.95,2),atol=1e-9)
        assert not r['heterogeneity_estimated']


def test_failed_fit_has_no_successful_estimate(config,source):
    scenario=next(diagnostic_scenarios(config));row=dict(source[1][0]);row['fn']=0
    result,inputs=safe_fit('diagnostic',scenario,lambda:fit_diagnostic([row,row],scenario,config))
    assert result['status']=='failed_not_pooled' and not result['converged'] and inputs==[]
    assert 'summary_sensitivity' not in result and 'summary_specificity' not in result
    scenario=next(auroc_scenarios(config));scenario['assumed_se_auroc']=-1
    result,_=safe_fit('auroc',scenario,lambda:(fit_auroc(select_auroc(source[0],scenario,config),config),[]))
    assert result['status']=='failed_not_pooled' and 'pooled_auroc' not in result


def test_original_descriptive_findings_remain_unchanged(project):
    baseline=baseline_checks(project);assert len(baseline['protected_files'])==67
    status=json.loads((project/'results/analysis_status.json').read_text())
    assert status['auroc']['status']=='not_statistically_defensible'
    assert status['diagnostic']['status']=='not_statistically_defensible'


def test_exploratory_end_to_end_is_deterministic_and_reports_every_scenario(project,tmp_path):
    first,checks=run(project,tmp_path/'one');second,_=run(project,tmp_path/'two')
    assert first['output_files']==second['output_files']
    assert first['auroc']['successful_final_scenarios']==18
    assert first['diagnostic']['successful_final_scenarios']==96
    assert not first['diagnostic']['unrestricted_covariance_estimated'] and not first['diagnostic']['hsroc_curve_fitted']
    assert len(verify(project,tmp_path/'one'))==8
    for sub in ['auroc_meta_analysis','diagnostic_meta_analysis','consolidated_exploratory_report']:
        text=(tmp_path/'one/reports/exploratory'/f'{sub}.md').read_text()
        assert 'EXPLORATORY' in text and 'conditional' in text
    text=(tmp_path/'one/reports/exploratory/consolidated_exploratory_report.md').read_text()
    for row in read(tmp_path/'one/results/exploratory/auroc_scenario_results.csv')+read(tmp_path/'one/results/exploratory/diagnostic_scenario_results.csv'):
        assert row['scenario_id'] in text
    from html.parser import HTMLParser
    from urllib.parse import urlparse,unquote
    class Parser(HTMLParser):
        def __init__(self):super().__init__();self.links=[];self.images=[];self.count=0;self.row_widths=[];self.tables=[]
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            if tag=='a' and 'href' in attrs:self.links.append(attrs['href'])
            if tag=='img':self.images.append(attrs['src'])
            if tag=='table':self.row_widths=[]
            if tag=='tr':self.count=0
            if tag in {'td','th'}:self.count+=1
        def handle_endtag(self,tag):
            if tag=='tr':self.row_widths.append(self.count)
            if tag=='table':self.tables.append(self.row_widths[:])
    for path in (tmp_path/'one/reports/exploratory').glob('*.html'):
        parser=Parser();parser.feed(path.read_text())
        for link in parser.links+parser.images:
            uri=urlparse(link)
            if not uri.scheme and uri.path:assert (path.parent/unquote(uri.path)).exists(),link
        assert all(len(set(widths))==1 and widths[0]>=4 for widths in parser.tables)
        if path.name in {'consolidated_exploratory_report.html','exploratory_results_summary.html'}:
            assert len(parser.tables)==6 and any(len(widths)==97 for widths in parser.tables)
    for path in (tmp_path/'one/figures/exploratory').glob('*.svg'):

        assert 'EXPLORATORY' in path.read_text()
