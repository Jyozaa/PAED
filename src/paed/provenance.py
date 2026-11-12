"""Versioned integrity for an intentional eligibility revision, never a bypass."""
from functools import lru_cache
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
from .ingest import digest


def load(path):return json.loads(Path(path).read_text())


@lru_cache(maxsize=4)
def historical_files(project,commit):
    result=subprocess.run(['git','archive',commit],cwd=project,capture_output=True)
    if result.returncode:
        raise RuntimeError('Historical baseline unavailable; use a full clone or fetch the missing history: '+commit)
    with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
        return {m.name:archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}


def historical_checks(project):
    project=Path(project).resolve();revision=load(project/'config/revision.json')
    previous=historical_files(str(project),revision['parent_commit'])
    old=load(project/revision['historical_baseline'])
    assert old==json.loads(previous['config/exploratory_baseline_hashes.json']), 'Historical integrity record was altered'
    original=historical_files(str(project),old['baseline_commit'])
    for name,expected in old['protected_files'].items():
        assert hashlib.sha256(original[name]).hexdigest()==expected, f'Historical original file mismatch: {name}'
    for name,record in revision['saved_comparison_inputs'].items():
        assert digest(project/name)==record['sha256'],f'Saved aggregate comparison changed: {name}'
        assert hashlib.sha256(previous[record['source_path']]).hexdigest()==record['sha256'],f'Comparison does not match parent Git tree: {name}'
    for name in ['config/source_schema.json','data/curated/source_rows.json','data/curated/cell_states.json','data/curated/source_provenance.json']:
        assert digest(project/name)==old['protected_files'][name], f'Original source derivative changed: {name}'
    assert revision['original_source_hashes']==load(project/'data/curated/source_provenance.json')['inputs']
    for record in revision['original_source_hashes']:
        path=project/record['filename']
        if path.exists():assert digest(path)==record['sha256'],f'Original input changed: {record["filename"]}'
    return revision,old


def current_checks(project):
    project=Path(project);revision,_=historical_checks(project)
    info=load(project/'config/exploratory_baseline_hashes.json')
    assert info['revision_id']==revision['revision_id'], 'Current baseline not versioned for this revision'
    for name,expected in info['protected_files'].items():
        assert digest(project/name)==expected,f'Current revision scientific output/input changed: {name}'
    return info


def create_revision_baseline(project):
    """Explicit one-time versioning after all revised descriptive checks pass."""
    from .pipeline import validate
    project=Path(project);revision,old=historical_checks(project)
    checks=validate(project)
    existing=load(project/'config/exploratory_baseline_hashes.json')
    if existing.get('revision_id')==revision['revision_id']:
        current_checks(project)
        return existing
    names=[*old['protected_files'], 'config/revision.json',revision['historical_baseline'],*revision['saved_comparison_inputs']]
    info={'revision_id':revision['revision_id'],'baseline_commit':revision['parent_commit'],
          'historical_baseline':revision['historical_baseline'],
          'scope':'Intentional 17-model scientific revision; historical 20-model records are validated against Git, original/curated inputs remain immutable, execution metadata is excluded',
          'descriptive_validation_checks':checks,
          'protected_files':{name:digest(project/name) for name in names}}
    (project/'config/exploratory_baseline_hashes.json').write_text(json.dumps(info,indent=2)+'\n')
    current_checks(project)
    return info
