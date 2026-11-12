"""Complete ordered revision: descriptive -> scenarios -> comparison -> LaTeX -> QA."""
from datetime import datetime,timezone
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import sys
from .pipeline import run as descriptive_run,git_sha
from .exploratory_pipeline import run as exploratory_run,verify as exploratory_verify
from .provenance import current_checks,create_revision_baseline,historical_checks
from .short_report import build as build_pdf
from .ingest import digest


def verify(project,output=None):
    project=Path(project).resolve();root=Path(output).resolve() if output else project
    info=json.loads((root/'results/revisions/run_manifest.json').read_text())
    current_checks(project)
    for name,sha in info['output_files'].items():assert digest(root/name)==sha,f'Revised output changed since run: {name}'
    for name,sha in info['source_code_hashes'].items():assert digest(project/name)==sha,f'Revision implementation changed: {name}'
    checks=exploratory_verify(project,root)
    assert info['counts']['retained_models']==17 and info['counts']['retained_study_reports']==5
    assert info['auroc']['core_scenarios']==18 and info['auroc']['alternative_lu_scenarios']==126
    assert info['diagnostic_numerically_identical_to_previous']
    assert info['pdf']['pages']>=1 and not info['pdf']['layout_warnings'] and not info['pdf']['sensitivity_specificity_graph_included']
    return checks+['Revised 5-report/17-model counts and 18+126 AUROC scenarios confirmed',
                  'All 96 diagnostic results compared with saved parent; unchanged',
                  'LaTeX source and compiled PDF exist with no detected overflow or diagnostic graph']


def run(project,output=None,input_dir=None,run_tests=False):
    project=Path(project).resolve();root=Path(output).resolve() if output else project
    started=datetime.now(timezone.utc).isoformat();revision,_=historical_checks(project)
    descriptive=descriptive_run(project,output_dir=root,input_dir=input_dir,run_tests=False)
    create_revision_baseline(project)
    exploratory,_=exploratory_run(project,output=root,run_tests=False)
    pdf=build_pdf(project,output=root)
    test={'status':'not_run_in_this_invocation'}
    if run_tests:
        proc=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=project,capture_output=True,text=True)
        test={'status':'passed' if proc.returncode==0 else 'failed','command':'python -m pytest -q','exit_code':proc.returncode,'output':proc.stdout.strip(),'stderr':proc.stderr.strip()}
    # Record the same completed test run in both component manifests. Metadata
    # is updated after every calculation and PDF build, without refitting results.
    descriptive['tests']=test
    descriptive['execution_command']='python scripts/run_revision.py'+(' --input-dir <local sources>' if input_dir else '')+(' --run-tests' if run_tests else '')
    descriptive['output_files']={str(p.relative_to(root)):digest(p) for sub in ['results','figures','reports'] for p in sorted((root/sub).iterdir()) if p.is_file()}
    (root/'run_manifest.json').write_text(json.dumps(descriptive,indent=2)+'\n')
    exploratory['tests']=test;exploratory['descriptive_run_manifest_sha256_at_execution']=digest(root/'run_manifest.json')
    exploratory['executed_command']=descriptive['execution_command']+' (exploratory stage)'
    (root/'results/exploratory/run_manifest.json').write_text(json.dumps(exploratory,indent=2)+'\n')
    import pandas as pd
    diagnostic_comparison=pd.read_csv(root/'results/exploratory/diagnostic_reproduction_comparison.csv')
    files={**descriptive['output_files'],**exploratory['output_files']}
    for folder in ['reports/revisions','output/pdf']:
        for p in sorted((root/folder).glob('*')):
            if p.is_file() and p.suffix in {'.pdf','.json','.md','.html'}:files[str(p.relative_to(root))]=digest(p)
    for p in [root/'run_manifest.json',root/'results/exploratory/run_manifest.json']:files[str(p.relative_to(root))]=digest(p)
    code=[*sorted((project/'src/paed').glob('*.py')),project/'scripts/run_revision.py',project/'scripts/verify_revision.py',project/'scripts/build_short_report.py']
    manifest={'revision_id':revision['revision_id'],'analysis_class':'revised_descriptive_and_conditional_exploratory',
        'started_at_utc':started,'completed_at_utc':datetime.now(timezone.utc).isoformat(),
        'source_git_commit_sha':git_sha(project),'parent_commit':revision['parent_commit'],
        'original_source_hashes':revision['original_source_hashes'],'source_code_hashes':{str(p.relative_to(project)):digest(p) for p in code},
        'counts':descriptive['counts'],'exclusions':descriptive['exclusion_reasons_and_counts'],
        'auroc':exploratory['auroc'],'diagnostic':exploratory['diagnostic'],
        'diagnostic_numerically_identical_to_previous':bool(diagnostic_comparison.all_numerical_columns_identical.all()),
        'maximum_diagnostic_difference':float(diagnostic_comparison.maximum_absolute_numerical_difference.max()),
        'pdf':pdf,'tests':test,'output_files':files,'executed_command':descriptive['execution_command'],
        'software':{**exploratory['software'],'latex_engine':pdf['engine'],'pdf_serializer':{'pypdf':version('pypdf')}},'provenance':'Historical 20-model records verified against Git; current 17-model scientific baseline and immutable input hashes both enforced',
        'warnings':['Conditional pooling remains assumption-dependent','No unrestricted fitted bivariate covariance or HSROC','Sparse cells, clustering, adult participants, validation and protocol concerns unresolved']}
    (root/'results/revisions').mkdir(parents=True,exist_ok=True)
    (root/'results/revisions/run_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if test['status']=='failed':raise RuntimeError('Revision tests failed; no validated completion claimed:\n'+test['output']+'\n'+test['stderr'])
    verify(project,root)
    return manifest
