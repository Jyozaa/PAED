"""Read all supplied sources locally; export only whitelisted aggregate fields."""
import csv
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

CSV_NAME = 'Data extraction paeds cardiac arrest SR progress 5.xlsx - Sheet1.csv'
PDF_NAMES = ('List of Variables.pdf', 'PROSPERO.pdf')
FIELDS = ['title','full_text_url','doi','study_label','authors','year','country','study_aim',
          'design','setting','recruitment','age','age_groups','sex','sample_size','ca_prevalence',
          'conditions','architecture_raw','modality_raw','feature_selection','predictors','time_series',
          'internal_validation','external_validation_raw','split_sizes','lead_time_raw','outcome_raw',
          'frequency_raw','tp_raw','fp_raw','fn_raw','tn_raw','sensitivity_raw','specificity_raw',
          'auroc_raw','feature_themes_raw','comparator_raw','raw_risk_of_bias','raw_meta_regression',
          'raw_limitations','additional_notes','assumptions']
# The raw quality/narrative fields may mix correspondence and unpublished comments.
# Public evidence summaries are separately curated with column-level provenance.
PUBLIC_COLUMNS = list(range(0,4)) + list(range(5,25)) + list(range(27,35))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def missing_state(value):
    if value is None or str(value).strip() == '':
        return 'missing'
    text = str(value).strip().lower()
    if text in {'n/a','na','not applicable'}:
        return 'not_applicable'
    if text == '0' or text == '0%' or text == '0.0':
        return 'observed_zero'
    if text in {'nr','not reported','not_reported'} or text.startswith('nr ') or text.startswith('not reported ('):
        return 'not_reported'
    if text in {'unclear','ambiguous','unknown'}:
        return 'ambiguous'
    return 'observed'


def discover(input_dir):
    root = Path(input_dir).resolve()
    paths = {}
    for name in (CSV_NAME, *PDF_NAMES):
        hits = [p for p in root.rglob(name) if not any(x in p.parts for x in ('.git','.venv','tmp'))]
        if len(hits) != 1:
            raise ValueError(f'Expected exactly one {name}, found {len(hits)} under input directory')
        paths[name] = hits[0]
    return paths


def study_id(label):
    import re
    match = re.search(r'(Yu|Lu|Bose|Kenet)\s*,\s*(\d{4})', label)
    if not match:
        raise ValueError(f'Unrecognized study label: {label}')
    return f'{match[1].lower()}_{match[2]}'


def ingest(input_dir, project):
    project = Path(project)
    paths = discover(input_dir)
    schema = []
    source_rows = []
    cells = []
    group = ''
    previous_line = 0
    with paths[CSV_NAME].open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream)
        groups = next(reader)
        labels = next(reader)
        previous_line = reader.line_num
        if len(groups) != 42 or len(labels) != 42:
            raise ValueError('Unexpected two-row source schema')
        for i, (g, label, field) in enumerate(zip(groups, labels, FIELDS)):
            group = g.strip() or group
            schema.append({'source_column_index':i, 'group_header_raw':g,
                           'section':group, 'original_column_name':label, 'analysis_field':field,
                           'publication_policy':'whitelisted aggregate' if i in PUBLIC_COLUMNS else 'withheld or separately curated'})
        for number, row in enumerate(reader, 3):
            start = previous_line + 1
            previous_line = reader.line_num
            if len(row) != 42:
                raise ValueError(f'Record {number} has {len(row)} columns')
            for i, cell in enumerate(row):
                cells.append({'source_row':number,'source_column_index':i,'analysis_field':FIELDS[i],
                              'missing_state':missing_state(cell)})
            populated = bool(row[3].strip() and row[17].strip())
            sid = study_id(row[3]) if populated else ('yu_2023' if 'Logistic Regression' in row[0] else '')
            record = {'source_row':number, 'source_line_start':start, 'source_line_end':reader.line_num,
                      'study_id':sid,'source_nonempty_cells':sum(bool(x.strip()) for x in row),'record_type':'populated_model' if populated else ('cross_reference' if any(row) else 'blank')}
            for i in PUBLIC_COLUMNS:
                record[FIELDS[i]] = 'NR' if 'emailed' in row[i].lower() else row[i].strip()
            # Never republish correspondence-derived details, directly or by paraphrase.
            record['lead_time_raw'] = row[25].strip() if sid != 'lu_2025' else '[withheld: verify in public source]'
            record['outcome_raw'] = row[26].strip() if sid != 'lu_2025' else '[withheld: verify in public source]'
            record['comparator_raw'] = row[36].strip() if sid in {'yu_2023','kenet_2023'} and populated else ''
            source_rows.append(record)
    local = project/'data/local'
    local.mkdir(parents=True,exist_ok=True)
    pdf_metadata=[]
    for name in PDF_NAMES:
        pdf=PdfReader(paths[name])
        pages=[page.extract_text() or '' for page in pdf.pages]
        (local/(Path(name).stem+'.txt')).write_text('\n\n'.join(f'PAGE {i+1}\n{t}' for i,t in enumerate(pages)),encoding='utf-8')
        if any(not text.strip() for text in pages):
            raise ValueError(f'{name} has pages without extracted text; manual OCR required')
        pdf_metadata.append({'name':name,'pages':len(pages),'text_characters':sum(map(len,pages))})
    manifest={'inputs':[{'filename':name,'sha256':digest(path)} for name,path in paths.items()],
              'pdf_read_checks':pdf_metadata, 'source_records':len(source_rows),
              'header_rows':2,'source_numbering':'1-based logical CSV record, including both header records; physical multiline spans also supplied'}
    curated=project/'data/curated'
    for name, data in [('source_rows.json',source_rows),('cell_states.json',cells),('source_provenance.json',manifest)]:
        (curated/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (project/'config/source_schema.json').write_text(json.dumps(schema,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return source_rows
