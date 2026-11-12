import csv
import json
import re
from pathlib import Path
from paed.pipeline import run,validate
from paed.ingest import digest


def test_public_curated_has_no_correspondence_or_contact_details(project):
    rows=json.loads((project/'data/curated/source_rows.json').read_text())
    assert len(rows)==27
    for r in rows:
        assert not {'authors','raw_risk_of_bias','raw_meta_regression','raw_limitations','additional_notes','assumptions'} & r.keys()
        for value in r.values():
            if isinstance(value,str):
                assert not re.search(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}',value,re.I)
                assert 'per author correspondence' not in value.lower()
                assert 'emailed' not in value.lower()
        if r['study_id']=='lu_2025':
            assert r['lead_time_raw']=='[withheld: verify in public source]'
            assert r['outcome_raw']=='[withheld: verify in public source]'


def test_source_headers_and_multiline_numbering(project):
    schema=json.loads((project/'config/source_schema.json').read_text())
    assert len(schema)==42 and schema[0]['original_column_name']=='Title '
    assert schema[3]['section']=='Basic information'
    rows=json.loads((project/'data/curated/source_rows.json').read_text())
    assert [r['source_row'] for r in rows]==list(range(3,30))
    assert all(r['source_line_end']>=r['source_line_start'] for r in rows)
    assert rows[1]['source_line_start']==rows[0]['source_line_end']+1
    assert any(r['source_line_end']>r['source_line_start'] for r in rows)
    states=json.loads((project/'data/curated/cell_states.json').read_text())
    assert len(states)==27*42


def test_pipeline_end_to_end_reproduces_same_outputs_without_raw_files(project,tmp_path):
    first=run(project,tmp_path/'first')
    second=run(project,tmp_path/'second')
    assert first['counts']['retained_models']==17
    assert first['input_mode']=='public_curated' and not first['raw_sources_verified_this_run']
    assert first['output_files']==second['output_files']
    assert len(validate(tmp_path/'first'))==8
    for relative,expected in first['output_files'].items():
        assert digest(tmp_path/'first'/relative)==expected
    assert first['analyses']['auroc']['pooled_estimate'] is None
    assert first['analyses']['diagnostic']['pooled_estimate'] is None


def test_worksheet_and_all_data_dictionary_columns_exist(project,evidence,tmp_path):
    run(project,tmp_path/'output')
    folder=tmp_path/'output'/'results'
    with (folder/'data_dictionary_derived.csv').open() as f:
        catalog={(r['table'],r['field']) for r in csv.DictReader(f)}
    for p in folder.glob('*.csv'):
        if p.name.startswith('data_dictionary'):continue
        with p.open() as f:fields=next(csv.reader(f))
        assert all((p.name,c) in catalog for c in fields)
    with (folder/'risk_of_bias_evidence.csv').open() as f:rob=list(csv.DictReader(f))
    assert len(rob)==20 and all(r['risk_of_bias_rating']=='not_assigned_pending_review' for r in rob)


def test_html_report_structure_and_local_figure_links(project,tmp_path):
    # The final report links both analysis stages and the revision comparison.
    # Build that complete report graph before checking every local target.
    from paed.revision_pipeline import run as complete_run
    from html.parser import HTMLParser
    from urllib.parse import urlparse,unquote
    output=tmp_path/'html-check'
    complete_run(project,output)
    class Parser(HTMLParser):
        def __init__(self):super().__init__();self.images=[];self.links=[];self.h2=[];self.heading=False
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            if tag=='img':self.images.append(attrs['src'])
            if tag=='a' and 'href' in attrs:self.links.append(attrs['href'])
            if tag=='h2':self.heading=True
        def handle_endtag(self,tag):
            if tag=='h2':self.heading=False
        def handle_data(self,data):
            if self.heading:self.h2.append(data)
    file=output/'reports/final_analysis_report.html';parser=Parser();parser.feed(file.read_text())
    assert len(parser.images)==6
    for source in parser.images:assert (file.parent/source).is_file()
    for link in parser.links:
        uri=urlparse(link)
        if not uri.scheme and uri.path:assert (file.parent/unquote(uri.path)).is_file(),link
    for i in range(1,16):assert any(x.startswith(f'{i}. ') for x in parser.h2)
    assert '<style>' in file.read_text() and 'overflow-x:auto' in file.read_text()
