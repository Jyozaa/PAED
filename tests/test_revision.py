"""Scientific and complete-build regression checks for the intentional revision."""
import json
import re
from collections import Counter
from pathlib import Path
import pandas as pd
import pytest
from pypdf import PdfReader
from paed.ingest import digest
from paed.provenance import historical_checks,current_checks
from paed.revision_pipeline import run,verify

EXCLUDED={'lu_2025_xgboost','lu_2025_gmlp','lu_2025_pedca_ft'}
REASON='Research-team decision: model excluded because sensitivity and specificity were extracted graphically and considered insufficiently reliable.'


def test_reconciles_exclusions_against_unchanged_source_records(project):
    revision,_=historical_checks(project)
    rows=json.loads((project/'data/curated/source_rows.json').read_text())
    inventory=pd.read_csv(project/'results/model_inventory.csv')
    retained=pd.read_csv(project/'results/cleaned_models.csv')
    exclusions=pd.read_csv(project/'results/exclusion_log.csv')
    assert len(rows)==27 and len(inventory)==26 and inventory.study_id.nunique()==6
    assert len(retained)==17 and retained.study_id.nunique()==5
    assert (retained.study_id=='lu_2025').sum()==8
    assert EXCLUDED.issubset(set(inventory.model_id)) and EXCLUDED.isdisjoint(retained.model_id)
    selected=exclusions[exclusions.model_id.isin(EXCLUDED)]
    assert set(selected.model_id)==EXCLUDED and set(selected.exclusion_reason)=={REASON}
    assert set(selected.source_row)=={13,17,18}
    assert len(exclusions[exclusions.study_id=='yu_2026'])==5
    assert (exclusions.model_id=='yu_2023_gnb').sum()==1
    assert revision['original_source_hashes']==json.loads((project/'data/curated/source_provenance.json').read_text())['inputs']
    assert len(current_checks(project)['protected_files'])==76


def test_every_retained_lu_choice_is_crossed_with_all_18_configurations(project):
    models=pd.read_csv(project/'results/cleaned_models.csv')
    results=pd.read_csv(project/'results/exploratory/auroc_scenario_results.csv')
    inputs=pd.read_csv(project/'results/exploratory/auroc_scenario_inputs.csv')
    expected=set(models.loc[models.study_id=='lu_2025','model_id'])
    lu=inputs[inputs.study_id=='lu_2025']
    assert Counter(lu.model_id)==Counter({m:18 for m in expected})
    assert len(results)==144 and len(inputs)==144*4
    assert EXCLUDED.isdisjoint(inputs.model_id)
    for _,frame in inputs.groupby('scenario_id'):
        assert len(frame)==4 and frame.dependency_group.nunique()==4
        assert len(frame[frame.study_id=='lu_2025'])==1
        assert not {'yu_2022','yu_2023'}.issubset(frame.study_id)
        assert frame.metric_source.str.contains('Extraction CSV logical record').all()
    core=results[results.scenario_family=='core_lu_logistic']
    assert len(core)==18 and set(core.lu_estimate_id)=={'lu_2025_logistic_a1'}
    assert set(lu[lu.model_id=='lu_2025_logistic'].auroc)=={.6292}
    assert set(core.assumed_se_auroc)=={.02,.04,.08}
    assert (results.status=='success_conditional').all() and results.converged.all()


def test_excluded_models_absent_from_active_tables_and_descriptive_vector_figures(project):
    for name in ['cleaned_models','auroc_estimates','table2_model_performance','operating_points']:
        frame=pd.read_csv(project/'results'/f'{name}.csv')
        assert EXCLUDED.isdisjoint(frame.model_id)
    a=pd.read_csv(project/'results/auroc_estimates.csv')
    lu=a[a.study_id=='lu_2025']
    assert len(lu)==8 and lu.auroc.min()==pytest.approx(.5472) and lu.auroc.max()==pytest.approx(.7329)
    op=pd.read_csv(project/'results/operating_points.csv')
    assert not {'lu_2025','yu_2022'}.intersection(op.study_id)
    for name in ['auroc_descriptive','auroc_short_report','sensitivity_descriptive','specificity_descriptive','sroc_descriptive']:
        text=(project/'figures'/f'{name}.svg').read_text().lower()
        assert 'pedca' not in text and 'gmlp' not in text
        assert not re.search(r'lu 2025[^<\n]*xgboost',text)


def test_diagnostic_rerun_is_numerically_and_byte_identical_to_saved_parent(project):
    old=project/'data/history/analysis_20_models'
    for name in ['diagnostic_scenario_results','diagnostic_scenario_inputs']:
        assert digest(project/'results/exploratory'/f'{name}.csv')==digest(old/f'{name}.csv')
    assert digest(project/'results/diagnostic_2x2.csv')==digest(old/'diagnostic_2x2.csv')
    comparison=pd.read_csv(project/'results/exploratory/diagnostic_reproduction_comparison.csv')
    assert len(comparison)==96 and comparison.all_numerical_columns_identical.all()
    assert (comparison.maximum_absolute_numerical_difference==0).all()
    files=pd.read_csv(project/'results/exploratory/diagnostic_file_comparison.csv')
    assert len(files)==7 and files.byte_identical.all()
    inputs=pd.read_csv(project/'results/exploratory/diagnostic_scenario_inputs.csv')
    assert set(inputs.study_id)=={'yu_2023','kenet_2023'}


def test_short_report_presentation_and_all_contributors(project):
    source=(project/'reports/short_report.tex').read_text()
    reader=PdfReader(project/'output/pdf/short_report.pdf')
    text='\n'.join(p.extract_text() or '' for p in reader.pages)
    assert len(reader.pages)==3 and len(re.findall(r'\\section\*\{',source))==8
    for forbidden in ['Codex','\u2014','Figure 1','Table 1','\\date','\\section*{Aim}']:
        assert forbidden not in source and forbidden not in text
    assert source.count('\\includegraphics')==1 and '../figures/auroc_short_report.png' in source
    assert '\\hyphenpenalty=10000' in source and '\\exhyphenpenalty=10000' in source
    pooled=text.split('Revised exploratory pooled AUROC',1)[1].split('Sensitivity, specificity and PPV',1)[0]
    for token in ['Lu 2025','Bose 2019','Yu 2023 RDN','Yu 2022 LR','Kenet 2023','0.6292','0.7500','0.8500','0.8300']:
        assert token in pooled
    meta=json.loads((project/'output/pdf/build_manifest.json').read_text())
    assert not meta['layout_warnings'] and not meta['sensitivity_specificity_graph_included']
    assert meta['pdf_sha256']==digest(project/'output/pdf/short_report.pdf')


def test_complete_revision_is_deterministic_in_fresh_output_directories(project,tmp_path):
    first=run(project,tmp_path/'first');second=run(project,tmp_path/'second')
    # Execution timestamps/source metadata vary; every scientific artifact and
    # the LaTeX-derived PDF must be identical, including the PDF build manifest.
    excluded={'run_manifest.json','results/exploratory/run_manifest.json'}
    one={k:v for k,v in first['output_files'].items() if k not in excluded}
    two={k:v for k,v in second['output_files'].items() if k not in excluded}
    assert one==two
    assert first['pdf']['pdf_sha256']==second['pdf']['pdf_sha256']
    assert len(verify(project,tmp_path/'first'))==11
    assert first['counts']['retained_models']==17 and first['diagnostic_numerically_identical_to_previous']
    assert first['maximum_diagnostic_difference']==0
    from html.parser import HTMLParser
    from urllib.parse import unquote,urlparse
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.paths=[]
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            if tag=='a' and 'href' in attrs:self.paths.append(attrs['href'])
            if tag=='img':self.paths.append(attrs['src'])
    for path in (tmp_path/'first/reports').rglob('*.html'):
        parser=Links();parser.feed(path.read_text())
        for target in parser.paths:
            uri=urlparse(target)
            if not uri.scheme and uri.path:assert (path.parent/unquote(uri.path)).is_file(),(path,target)
