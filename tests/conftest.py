import json
from pathlib import Path
import pytest
from paed.clean import build
ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='session')
def project():return ROOT

@pytest.fixture(scope='session')
def evidence():
    return build(json.loads((ROOT/'data/curated/source_rows.json').read_text()),
                 json.loads((ROOT/'config/study_context.json').read_text()),
                 json.loads((ROOT/'config/analysis.json').read_text()))
