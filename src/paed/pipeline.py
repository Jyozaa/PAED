"""Orchestrate deterministic extraction-level evidence synthesis."""
import json
import platform
import subprocess
import sys
from datetime import datetime,timezone
from importlib.metadata import version
from pathlib import Path
from .analysis import feasibility,heterogeneity
from .clean import build
from .figures import create_figures
from .ingest import digest,ingest
from .reporting import write_csv,principal_tables,risk_evidence,dictionaries,render_reports,write_md


def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def git_sha(root):
    p=subprocess.run(['git','rev-parse','HEAD'],cwd=root,text=True,capture_output=True)
    return p.stdout.strip() if p.returncode==0 else None


def run(project,output_dir=None,input_dir=None,run_tests=False):
    project=Path(project).resolve();out=Path(output_dir).resolve() if output_dir else project
    started=datetime.now(timezone.utc).isoformat()
    for name in ['results','reports','figures']: (out/name).mkdir(parents=True,exist_ok=True)
    rows=ingest(input_dir,project) if input_dir else load(project/'data/curated/source_rows.json')
    config=load(project/'config/analysis.json');contexts=load(project/'config/study_context.json')
    data=build(rows,contexts,config);statuses,selection=feasibility(data,contexts,config)
    source_provenance=load(project/'data/curated/source_provenance.json')
    t1,t2=principal_tables(data,contexts)
    study_inventory=[]
    for sid,c in contexts.items():
        sr=[r for r in rows if r['study_id']==sid and r['record_type']=='populated_model']
        keep=[r for r in data['models'] if r['study_id']==sid]
        study_inventory.append({'study_id':sid,'populated_models':len(sr),'retained_models':len(keep),
            'source_rows':';'.join(str(r['source_row']) for r in sr),'setting':c['setting_class'],
            'outcome_context':sr[0].get('outcome_raw',''),'prediction_horizon':c['horizon_group'],
            'validation_methods':'; '.join(dict.fromkeys(r.get('internal_validation','') for r in sr)),
            'external_validation':c['external_validation'],'analysis_unit':c['unit'],
            'cohort_id':c['cohort_id'],'dependency_group':c['dependency_group'],'working_eligible':bool(keep),
            'doi':sr[0]['doi'],'strict_status':c['strict_status'],'strict_reason':c['strict_reason']})
    inventory=[]
    for r in rows:
        if r['record_type']!='populated_model':continue
        a=next(x for x in data['audit'] if x['source_row']==r['source_row'])
        c=contexts[r['study_id']]
        inventory.append({**a,'architecture_raw':r['architecture_raw'],'outcome':r['outcome_raw'],
            'prediction_horizon':c['horizon_group'],'validation_type':r['internal_validation'],
            'analysis_unit':c['unit'],'cohort_id':c['cohort_id'],'dependency_group':c['dependency_group'],
            **{k:r[k] for k in ['auroc_raw','sensitivity_raw','specificity_raw','tp_raw','fp_raw','fn_raw','tn_raw']}})
    summary=[{'measure':'original_study_reports','value':len({r['study_id'] for r in rows if r['record_type']=='populated_model'}),'unit':'study reports'},
             {'measure':'post_header_records','value':len(rows),'unit':'logical CSV records'},
             {'measure':'populated_model_entries','value':len(inventory),'unit':'models'},
             {'measure':'cross_reference_records','value':sum(r['record_type']=='cross_reference' for r in rows),'unit':'records'},
             {'measure':'fully_blank_records','value':sum(r['record_type']=='blank' for r in rows),'unit':'records'},
             {'measure':'retained_study_reports','value':len(t1),'unit':'reports'},
             {'measure':'retained_models','value':len(t2),'unit':'models'},
             {'measure':'potential_dependency_groups','value':len({r['dependency_group'] for r in data['models']}),'unit':'conservative groups, not proven overlap'},
             {'measure':'numeric_auroc_evaluations','value':len(data['auroc']),'unit':'evaluations; includes Bose training/test'},
             {'measure':'genuine_auroc_95ci','value':statuses['auroc']['genuine_95ci_estimates'],'unit':'estimates'},
             {'measure':'complete_candidate_2x2','value':len(data['diagnostic']),'unit':'dependent model tables'},
             {'measure':'2x2_study_sources','value':len({r['study_id'] for r in data['diagnostic']}),'unit':'study sources, not eligible independent tables'},
             {'measure':'confirmed_independent_patient_tables','value':0,'unit':'tables'},
             {'measure':'strict_demonstrated_eligible_studies','value':0,'unit':'reports'},
             {'measure':'sensitivity_reporting_models','value':sum(r['sensitivity_reported'] is not None for r in data['models']),'unit':'models'},
             {'measure':'specificity_reporting_models','value':sum(r['specificity_reported'] is not None for r in data['models']),'unit':'models'}]
    for sid in dict.fromkeys(r['study_id'] for r in data['models']):
        vals=[r['auroc'] for r in data['auroc'] if r['study_id']==sid and r['evaluation']!='training']
        summary.extend([{'measure':f'{sid}_nontraining_reported_auroc_min','value':min(vals),'unit':'descriptive AUROC'},
                        {'measure':f'{sid}_nontraining_reported_auroc_max','value':max(vals),'unit':'descriptive AUROC'}])
    change=data['changes'][:]
    for r in rows:
        change.append({'study_id':r['study_id'],'model_id':'','source_row':r['source_row'],'field':'public_source_sanitization',
                       'original':'[private narrative fields withheld]','standardised':'Aggregate whitelist plus analyst-curated evidence',
                       'action':'Exclude authors/personal details and narrative quality/notes/assumptions; Lu correspondence-derived horizon/outcome withheld'})
    tables={
        'data_audit':data['audit'],'exclusion_log':data['excluded'],'study_inventory':study_inventory,
        'model_inventory':inventory,'cleaned_models':data['models'],'auroc_estimates':data['auroc'],
        'diagnostic_2x2':data['diagnostic'],'operating_points':data['operating'],
        'data_quality_flags':data['flags'],'cleaning_change_log':change,
        'source_cell_states':load(project/'data/curated/cell_states.json'),
        'table1_study_characteristics':t1,'table2_model_performance':t2,'descriptive_summary':summary,
        'model_selection':selection,'heterogeneity_matrix':heterogeneity(contexts),
        'risk_of_bias_evidence':risk_evidence(contexts),
        'strict_protocol_eligibility':[{k:r[k] for k in ['study_id','populated_models','retained_models','setting','external_validation','strict_status','strict_reason']} for r in study_inventory],
        'analysis_feasibility':[{'analysis':key,'status':value.get('status','eligibility_assessment'),
                                 'pooled_estimate_produced':value.get('pooled_estimate_produced',False),
                                 'reason':'; '.join(value.get('gate_reasons',[]))} for key,value in statuses.items()]}
    for name,rs in tables.items():write_csv(out/'results'/f'{name}.csv',rs)
    (out/'results/analysis_status.json').write_text(json.dumps(statuses,indent=2)+'\n')
    create_figures(data,contexts,out/'figures')
    # Dictionary source is configuration; output directory may be separate in tests.
    if out!=project:
        (out/'config').mkdir(exist_ok=True)
        (out/'config/source_schema.json').write_text((project/'config/source_schema.json').read_text())
    dictionaries(out,tables)
    render_reports(out,data,contexts,statuses,selection,t1,t2)
    checks=validate(out,data)
    write_md(out/'reports/validation_report.md',f'''# Execution validation

The complete pipeline was executed from {'all three local original sources' if input_dir else 'the public curated aggregate inputs'}. Numerical/completeness checks: **{len(checks)} passed**. The checks include count reconciliation, complete-table denominators, domain coverage, genuine-CI counts, no unapproved pooling outputs and required figure files.

Source study facts were not independently re-extracted from full texts. Formal QUADAS-2/GRADE consensus remains pending. Inferential R fitting was **not invoked** because statistical eligibility failed; that is not a technical analysis failure. See the run manifest for actual software availability, executed commands and the full automated-test result. CI/uncertainty, clustering and clinical comparability blockers remain documented.

'''+ '\n'.join('- '+x for x in checks))
    test_result={'status':'not_run_in_this_invocation','command':None}
    if run_tests:
        command=[sys.executable,'-m','pytest','-q']
        proc=subprocess.run(command,cwd=project,text=True,capture_output=True)
        test_result={'status':'passed' if proc.returncode==0 else 'failed','command':'python -m pytest -q',
                     'exit_code':proc.returncode,'output':proc.stdout.strip(),'stderr':proc.stderr.strip()}
        if proc.returncode:raise RuntimeError('Tests failed:\n'+proc.stdout+'\n'+proc.stderr)
    versions={p:version(p) for p in ['numpy','pandas','scipy','matplotlib','Markdown','pytest','pypdf']}
    exclusion_counts={reason:sum(x['exclusion_reason']==reason for x in data['excluded']) for reason in dict.fromkeys(x['exclusion_reason'] for x in data['excluded'])}
    outputs={str(p.relative_to(out)):digest(p) for folder in ['results','reports','figures'] for p in sorted((out/folder).iterdir()) if p.is_file()}
    manifest={'analysis_reference_date':config['decision_date'],'started_at_utc':started,
              'completed_at_utc':datetime.now(timezone.utc).isoformat(),'input_mode':'raw_local' if input_dir else 'public_curated',
              'raw_sources_verified_this_run':bool(input_dir),'inputs':source_provenance['inputs'],
              'pdf_read_checks':source_provenance['pdf_read_checks'],
              'curated_inputs':[{'filename':str(p.relative_to(project)),'sha256':digest(p)} for p in sorted((project/'data/curated').glob('*.json'))],
              'counts':{r['measure']:r['value'] for r in summary if 'auroc_min' not in r['measure'] and 'auroc_max' not in r['measure']},
              'exclusion_reasons_and_counts':exclusion_counts,'analyses':statuses,
              'statistical_method_packages':{'executed':'Python semantic extraction, exact count arithmetic, descriptive plotting and eligibility gates',
                   'conditional_not_executed':['R metafor REML logit AUROC with modified Hartung-Knapp','R mada Reitsma bivariate REML for eligible interior independent data'],
                   'Rscript_available':bool(__import__('shutil').which('Rscript'))},
              'analysis_configuration':config,'warnings_and_unresolved_decisions':sorted({r['code'] for r in data['flags']}),
              'source_git_commit_sha':git_sha(project),'git_commit_note':'Revision present at execution; publication commit cannot contain its own future SHA',
              'software':{'python':platform.python_version(),'platform':platform.platform(),'packages':versions},
              'execution_command':'python scripts/run_pipeline.py'+(' --input-dir <local source directory>' if input_dir else '')+(' --run-tests' if run_tests else ''),
              'validation_checks':checks,'tests':test_result,'output_files':outputs}
    (out/'run_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def validate(root,data=None):
    import pandas as pd
    root=Path(root);checks=[]
    required=['data_audit','exclusion_log','study_inventory','model_inventory','cleaned_models','auroc_estimates','diagnostic_2x2',
              'data_quality_flags','cleaning_change_log','table1_study_characteristics','table2_model_performance','descriptive_summary',
              'heterogeneity_matrix','risk_of_bias_evidence','strict_protocol_eligibility','data_dictionary_source','data_dictionary_derived']
    for name in required:
        p=root/'results'/f'{name}.csv'
        if not p.exists() or p.stat().st_size<20:raise AssertionError(f'Missing output {p}')
    checks.append('All mandatory result tables exist with nonempty schemas')
    read=lambda name:pd.read_csv(root/'results'/f'{name}.csv')
    audit=read('data_audit');models=read('cleaned_models');a=read('auroc_estimates');d=read('diagnostic_2x2')
    assert len(audit)==27 and len(models)==20 and models.study_id.nunique()==5
    assert len(read('model_inventory'))==26 and len(read('study_inventory'))==6
    assert len(read('exclusion_log'))==7
    checks.append('Reconciled 27 records, 26 populated models, 6 original reports; 20 retained models / 5 reports; 6 exclusions plus 1 cross-reference')
    assert len(a)==21 and a.auroc.between(0,1).all() and a.ci_lower.notna().sum()==1
    assert (a.uncertainty_type=='unspecified_plus_minus').sum()==11
    assert a.loc[a.uncertainty_type=='unspecified_plus_minus','se_logit_approx'].isna().all()
    checks.append('21 AUROCs; 1 genuine CI; 11 unspecified variations never used as SE')
    assert len(d)==7 and d.study_id.nunique()==2
    kenet=d[d.study_id=='kenet_2023']
    assert (kenet.total_units==3059).all() and (kenet.positive_units==211).all() and (kenet.negative_units==2848).all()
    assert ((d.tp+d.fp+d.fn+d.tn)==d.total_units).all()
    for _,r in d.iterrows():
        assert abs(r.sensitivity_recalculated-r.tp/(r.tp+r.fn))<1e-12
        assert abs(r.specificity_recalculated-r.tn/(r.tn+r.fp))<1e-12
    checks.append('7 complete matrices validated; Kenet units consistently 3059 windows, 211 positive / 2848 negative')
    assert not a.pooled_eligible.any() and not d.pooled_eligible.any()
    assert len(read('risk_of_bias_evidence'))==20 and len(read('heterogeneity_matrix'))==10
    checks.append('No pooling eligibility; 20 pending QUADAS-2 domains and 10 pairwise comparability records')
    for name in ['auroc_descriptive','sensitivity_descriptive','specificity_descriptive','sroc_descriptive','heterogeneity_overview','inclusion_flow']:
        for ext in ['png','svg']:
            assert (root/'figures'/f'{name}.{ext}').stat().st_size>1000
    checks.append('All six descriptive figures exist as PNG and SVG')
    for name in ['final_analysis_report','plain_english_summary','protocol_deviations','auroc_feasibility','diagnostic_feasibility','data_audit','data_dictionary','risk_of_bias','certainty_of_evidence','figure_captions']:
        for ext in ['md','html']:assert (root/'reports'/f'{name}.{ext}').stat().st_size>500
    checks.append('Mandatory reports generated in Markdown and styled HTML')
    for forbidden in ['pooled_auroc','pooled_diagnostic','hsroc_fitted','forest_pooled']:
        assert not list((root/'figures').glob(forbidden+'*'))
    checks.append('No falsely pooled forest, HSROC or confidence-region figure present')
    return checks
