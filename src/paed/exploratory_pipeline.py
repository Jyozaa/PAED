"""Run and verify the separate assumption-dependent scenario layer."""
import json
from pathlib import Path
import platform
import subprocess
import sys
from datetime import datetime,timezone
from importlib.metadata import version
import numpy as np
import pandas as pd
from .ingest import digest
from .pipeline import git_sha
from .reporting import write_csv
from .exploratory import execute,CLASS,auroc_scenarios,diagnostic_scenarios
from .exploratory_figures import create
from .exploratory_reporting import render,contrasts,contrast_summary


def read(path):
    return pd.read_csv(path).astype(object).where(lambda x:x.notna(),None).to_dict('records')


def baseline_checks(project):
    from .provenance import current_checks
    return current_checks(project)


def check_calculations(results,config,project):
    baseline=baseline_checks(project);messages=[]
    assert {r['scenario_id'] for r in results['auroc_results']}=={r['scenario_id'] for r in auroc_scenarios(config)}
    assert {r['scenario_id'] for r in results['diagnostic_results']}=={r['scenario_id'] for r in diagnostic_scenarios(config)}
    messages.append('All configured scenarios present, with unique exploratory IDs and explicit success/error status')
    source_a={r['estimate_id']:r for r in read(Path(project)/'results/auroc_estimates.csv')}
    source_d={r['model_id']:r for r in read(Path(project)/'results/diagnostic_2x2.csv')}
    eligible={r['model_id'] for r in read(Path(project)/'results/cleaned_models.csv')}
    for a in results['auroc_results']:
        inputs=[r for r in results['auroc_inputs'] if r['scenario_id']==a['scenario_id']]
        assert a['analysis_class']==CLASS
        if a['status']!='success_conditional':
            assert not any(a.get(x) is not None for x in ['pooled_auroc','conditional_95_lower','conditional_95_upper']);continue
        assert len(inputs)==4 and len({r['dependency_group'] for r in inputs})==4
        studies={r['study_id'] for r in inputs}
        assert not {'yu_2022','yu_2023'}.issubset(studies)
        assert sum(r['study_id']=='kenet_2023' for r in inputs)==1
        assert a['conditional_95_lower']<a['pooled_auroc']<a['conditional_95_upper']
        assert a['tau2_logit_estimated']>=0 and a['converged']
        assert abs(sum(r['random_effects_weight'] for r in inputs)-1)<1e-10
        for r in inputs:
            assert r['model_id'] in eligible
            assert r['auroc']==source_a[r['estimate_id']]['auroc']
            assert r['original_plus_minus_used_as_se'] is False
            if r['uncertainty_origin'].startswith('genuine'):
                assert r['se_logit_used']==source_a[r['estimate_id']]['se_logit_approx'] and r['assumed_se_auroc'] is None
            else:assert r['uncertainty_origin']=='assumed_not_study_estimated' and r['assumed_se_auroc'] in config['auroc']['assumed_auroc_scale_ses']
    messages.append('Four source groups per AUROC scenario; no Dallas double counting, training performance, favourable-only selection or untagged imputed uncertainty')
    messages.append('Source AUROCs and genuine CI-derived variance unchanged; normalized weights, PM root/boundary and conditional intervals validated')
    for d in results['diagnostic_results']:
        inputs=[r for r in results['diagnostic_inputs'] if r['scenario_id']==d['scenario_id']]
        assert d['analysis_class']==CLASS
        if d['status']!='success_conditional':
            assert d.get('summary_sensitivity') is None and d.get('summary_specificity') is None;continue
        assert len(inputs)==2 and len({r['dependency_group'] for r in inputs})==2
        assert sum(r['study_id']=='kenet_2023' for r in inputs)==1
        assert not d['heterogeneity_estimated'] and d['normal_equation_residual']<=config['diagnostic']['normal_equation_tolerance']
        for key in ['sensitivity','specificity']:
            assert 0<d[f'{key}_conditional_95_lower']<d[f'summary_{key}']<d[f'{key}_conditional_95_upper']<1
        for inp in inputs:
            assert all(inp[k]==source_d[inp['model_id']][k] for k in ['tp','fp','fn','tn'])
            assert not inp['source_counts_altered']
            factor=inp['variance_inflation_assumed']
            assert np.isclose(inp['sampling_var_logit_sensitivity_assumed'],factor*(1/inp['tp']+1/inp['fn']))
            assert np.isclose(inp['sampling_var_logit_fpr_assumed'],factor*(1/inp['fp']+1/inp['tn']))
        assert np.allclose(np.array([[sum(x[f'GLS_weight_matrix_{i+1}{j+1}'] for x in inputs) for j in range(2)] for i in range(2)]),np.eye(2))
    messages.append('Two source summaries per diagnostic scenario; unchanged integer counts; correctly inflated covariance and GLS weight matrices summing to identity')
    messages.append('All accepted joint solutions have positive covariance and consistent marginal conditional intervals; fixed heterogeneity is never called estimated')
    messages.append(f'{len(baseline["protected_files"])} current-revision scientific/configuration/source files match their protected hashes; historical 20-model baseline independently verified against Git')
    return messages


def verify(project,output=None):
    project=Path(project);root=Path(output) if output else project
    manifest=json.loads((root/'results/exploratory/run_manifest.json').read_text())
    for name,sha in manifest['output_files'].items():assert digest(root/name)==sha,f'Exploratory output changed since run: {name}'
    for name,sha in manifest['input_files'].items():assert digest(project/name)==sha,f'Exploratory source/configuration changed: {name}'
    for name,sha in manifest['source_code_hashes'].items():assert digest(project/name)==sha,f'Exploratory implementation changed: {name}'
    config=json.loads((project/'config/exploratory_scenarios.json').read_text())
    results={k:read(root/'results/exploratory'/f'{name}.csv') for k,name in [
        ('auroc_results','auroc_scenario_results'),('auroc_inputs','auroc_scenario_inputs'),
        ('diagnostic_results','diagnostic_scenario_results'),('diagnostic_inputs','diagnostic_scenario_inputs')]}
    checks=check_calculations(results,config,project)
    for family in ['auroc_results','diagnostic_results']:
        for row in results[family]:
            if row['status']=='success_conditional':assert row['figure_warning'].startswith('EXPLORATORY')
    for r in results['auroc_results']:
        for ext in ['png','svg']:
            p=root/'figures/exploratory'/f'forest_{r["scenario_id"]}.{ext}'
            assert p.exists()==(r['status']=='success_conditional' and r['scenario_family']=='core_lu_logistic')
    checks.append('Each successful core AUROC scenario has PNG/SVG forests; alternative Lu scenarios are fully tabulated and compared in a dedicated figure; no failed scenario has a forest')
    for p in (root/'figures/exploratory').glob('*.svg'):
        assert 'EXPLORATORY' in p.read_text()
    checks.append('Every vector figure contains a visible exploratory warning')
    return checks


def run(project,output=None,run_tests=False):
    project=Path(project).resolve();root=Path(output).resolve() if output else project
    start=datetime.now(timezone.utc).isoformat();baseline=baseline_checks(project)
    config_path=project/'config/exploratory_scenarios.json';config=json.loads(config_path.read_text())
    for sub in ['results/exploratory','figures/exploratory','reports/exploratory']: (root/sub).mkdir(parents=True,exist_ok=True)
    if root!=project:
        (root/'config').mkdir(exist_ok=True)
        (root/'config/exploratory_scenarios.json').write_text(config_path.read_text())
    # Remove only owned, regenerated forests so obsolete/failed scenarios cannot
    # inherit a successful figure from an earlier invocation.
    for pattern in ['forest_A_*.png','forest_A_*.svg']:
        for p in (root/'figures/exploratory').glob(pattern):p.unlink()
    source_root=root if (root/'results/auroc_estimates.csv').exists() else project
    results=execute(read(source_root/'results/auroc_estimates.csv'),read(source_root/'results/diagnostic_2x2.csv'),config)
    checks=check_calculations(results,config,project)
    C=contrasts(results);summary=contrast_summary(C);attempts=[]
    for a in results['auroc_results']:
        fallback=a.get('fallback_used',False)
        attempts.append({'analysis_class':CLASS,'analysis':'auroc','scenario_id':a['scenario_id'],'attempt':1,
                         'solver':'statsmodels_iterated_PM','status':'failed_equation_check' if fallback else a['status'],
                         'message':a.get('primary_solver_error') or a.get('error_message') or a.get('diagnostic_note','')})
        if fallback:attempts.append({'analysis_class':CLASS,'analysis':'auroc','scenario_id':a['scenario_id'],'attempt':2,
                                    'solver':'scipy_brentq_same_PM_equation','status':a['status'],'message':'Original library failure preserved; identical estimating equation checked after bracketed root solve; no input changes'})
    attempts.extend({'analysis_class':CLASS,'analysis':'diagnostic','scenario_id':d['scenario_id'],'attempt':1,
                     'solver':'closed_form_joint_GLS','status':d['status'],'message':d.get('error_message','Positive covariance and normal equations checked; covariance not empirically estimated')} for d in results['diagnostic_results'])
    tables={'auroc_scenario_results':results['auroc_results'],'auroc_scenario_inputs':results['auroc_inputs'],
            'diagnostic_scenario_results':results['diagnostic_results'],'diagnostic_scenario_inputs':results['diagnostic_inputs'],
            'sensitivity_contrasts':C,'sensitivity_summary':summary,'fit_attempts':attempts,
            'diagnostic_identifiability':[{'analysis_class':CLASS,'source_summaries':2,'scalar_logit_observations':4,
                'mean_parameters':2,'unrestricted_covariance_components':3,'residual_scatter_rank_upper_bound':1,
                'unrestricted_covariance_estimated':False,'approach':'Prespecified covariance T and closed-form GLS',
                'caution':'Counting is not a structural-identifiability theorem; two sources cannot support reliable unrestricted heterogeneity/correlation estimation'}]}
    for name,rows in tables.items():write_csv(root/'results/exploratory'/f'{name}.csv',rows)
    (root/'results/exploratory/scenario_configuration.json').write_text(json.dumps(config,indent=2,ensure_ascii=False)+'\n')
    create(results,config,root/'figures/exploratory')
    from .revision_comparison import prepare,export
    comparison=prepare(project,root,results);export(root,comparison)
    render(root,results,config,summary,attempts,checks,comparison)
    # A compact, complete dictionary covers every result/ledger column without
    # changing the original data dictionary or tables.
    dictionary=[]
    comparison_tables={name:comparison[key] for key,name in [('comparison','before_after_comparison'),('paired_core','core_before_after'),('diagnostic_comparison','diagnostic_reproduction_comparison'),('reproduction','diagnostic_file_comparison'),('lu_sensitivity','lu_model_sensitivity')]}
    for name,rows in {**tables,**comparison_tables}.items():
        for key in dict.fromkeys(k for r in rows for k in r):
            dictionary.append({'analysis_class':CLASS,'table':name+'.csv','field':key,
                'definition':meaning(key),'missing_value':'empty cell; failed fits have no pooled estimate'})
    write_csv(root/'results/exploratory/data_dictionary.csv',dictionary)
    test={'status':'not_run_in_this_invocation'}
    if run_tests:
        p=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=project,capture_output=True,text=True)
        test={'status':'passed' if p.returncode==0 else 'failed','exit_code':p.returncode,'command':'python -m pytest -q','output':p.stdout.strip(),'stderr':p.stderr.strip()}
    outputs={str(p.relative_to(root)):digest(p) for sub in ['results/exploratory','figures/exploratory','reports/exploratory'] for p in sorted((root/sub).glob('*')) if p.is_file() and p.name!='run_manifest.json'}
    inputs=['results/auroc_estimates.csv','results/diagnostic_2x2.csv','config/exploratory_scenarios.json','config/exploratory_baseline_hashes.json']
    manifest={'analysis_class':CLASS,'status':'completed_conditional_sensitivity_analysis' if test.get('status')!='failed' else 'tests_failed',
        'started_at_utc':start,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'analysis_reference_date':config['reference_date'],
        'evidence_policy':config['evidence_policy'],'input_files':{name:digest(project/name) for name in inputs},
        'original_source_hashes':json.loads((project/'data/curated/source_provenance.json').read_text())['inputs'],
        'baseline_commit':baseline['baseline_commit'],'protected_original_files':len(baseline['protected_files']),
        'descriptive_run_manifest_sha256_at_execution':digest(project/'run_manifest.json'),
        'scientific_outputs_match_current_baseline':True,'historical_20_model_baseline_validated':True,
        'revision_id':baseline['revision_id'],
        'source_git_commit_sha':git_sha(project),'source_revision_note':'Revision available at run time; publication commit cannot include its own future hash',
        'source_code_hashes':{str(p.relative_to(project)):digest(p) for p in [*sorted((project/'src/paed').glob('exploratory*.py')),project/'scripts/run_exploratory.py',project/'scripts/verify_exploratory.py',project/'requirements.txt',project/'src/paed/provenance.py',project/'src/paed/revision_comparison.py']},
        'software':{'python':platform.python_version(),'packages':{p:version(p) for p in ['numpy','pandas','scipy','statsmodels','matplotlib','Markdown','pytest']}},
        'scenario_configuration':config,'auroc':{'attempted_scenarios':len(results['auroc_results']),
            'successful_final_scenarios':sum(r['status']=='success_conditional' for r in results['auroc_results']),
            'failed_final_scenarios':sum(r['status']!='success_conditional' for r in results['auroc_results']),
            'core_scenarios':sum(r['scenario_family']=='core_lu_logistic' for r in results['auroc_results']),
            'alternative_lu_scenarios':sum(r['scenario_family']=='alternative_lu_model' for r in results['auroc_results']),
            'library_attempts_failing_equation_check':sum(r.get('fallback_used',False) for r in results['auroc_results']),
            'total_numerical_attempts':sum(r['analysis']=='auroc' for r in attempts),'estimator':'Paule-Mandel, modified Hartung-Knapp t intervals'},
        'diagnostic':{'attempted_scenarios':len(results['diagnostic_results']),
            'successful_final_scenarios':sum(r['status']=='success_conditional' for r in results['diagnostic_results']),
            'failed_final_scenarios':sum(r['status']!='success_conditional' for r in results['diagnostic_results']),
            'method':'Joint normal-logit GLS with fixed T, inflated sampling covariances and specified correlations',
            'unrestricted_covariance_estimated':False,'hsroc_curve_fitted':False},
        'executed_command':'python scripts/run_exploratory.py'+(' --output-dir <directory>' if output else '')+(' --run-tests' if run_tests else ''),
        'numerical_checks':checks,'tests':test,'output_files':outputs,
        'warnings':['All pooled values/intervals are conditional on analyst assumptions','No new clinical evidence was obtained','Normal-logit approximation includes sparse cells','Source clustering, units, thresholds and validation remain unresolved']}
    (root/'results/exploratory/run_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if test.get('status')=='failed':raise RuntimeError('Tests failed; recorded manifest is not a verified successful run:\n'+test['output'])
    verification=verify(project,root)
    return manifest,verification


def meaning(key):
    specific={'analysis_class':'exploratory_conditional: all numerical inference depends on supplied assumptions',
        'scenario_id':'Unique model/uncertainty/covariance configuration, defined in exploratory_scenarios.json',
        'uncertainty_origin':'Genuine labelled CI endpoint approximation versus hypothetical analyst-assumed sampling SE',
        'assumed_se_auroc':'Analyst-supplied original-AUROC SE; not recovered from a study; absent for genuine-CI contribution',
        'pooled_auroc':'expit of conditional random-effects mean AUROC logit, not a specific clinical tool accuracy',
        'summary_sensitivity':'expit(mu_sensitivity) under fixed assumed GLS covariance; mixed source units',
        'summary_specificity':'expit(-mu_FPR) under fixed assumed GLS covariance; mixed source units',
        'tau2_logit_estimated':'Paule-Mandel between-source variance estimated conditional on assumed sampling variances',
        'T11_assumed':'Prespecified sensitivity-logit between-source variance; never estimated',
        'T12_assumed':'Prespecified between-source sensitivity/FPR logit covariance; never estimated',
        'T22_assumed':'Prespecified FPR-logit between-source variance; never estimated',
        'Q_conditional':'Residual quadratic form under supplied S+T; not estimated heterogeneity',
        'converged':'Numerical equation/linear solve validated; does not establish scientific validity',
        'limitations':'Adjacent interpretation restrictions, retained with every conditional result',
        'primary_solver_error':'Original rejected library attempt; retained even if same-equation fallback succeeds'}
    if key in specific:return specific[key]
    if key in ['tp','fp','fn','tn']:return 'Unchanged observed source count in original window/unverified analysis unit; never an effective patient count'
    if key.endswith('lower') or key.endswith('upper'):return 'Conditional 95% endpoint under configured assumptions; not a reported source confidence interval unless explicitly genuine in input ledger'
    if key.startswith('summary_cov_'):return 'Known-assumed-covariance GLS covariance of mean sensitivity/FPR logits'
    if key.startswith('GLS_weight_matrix_'):return 'Element of C*P_i coefficient matrix; matrices sum to identity across two sources'
    if key.startswith('delta_') or key.startswith('max_abs_delta'):return 'Matched-scenario change, not a sampling interval or hypothesis test; probability scale unless variance named'
    return key.replace('_',' ')+'; source provenance or explicitly configured/computed exploratory parameter (see methods/configuration)'
