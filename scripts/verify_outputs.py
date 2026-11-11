#!/usr/bin/env python3
"""Independently check output schemas, arithmetic and recorded file hashes."""
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from paed.pipeline import validate
from paed.ingest import digest

if __name__=='__main__':
    checks=validate(ROOT)
    m=json.loads((ROOT/'run_manifest.json').read_text())
    for file,expected in m['output_files'].items():
        assert digest(ROOT/file)==expected, f'Output changed since recorded run: {file}'
    assert not m['analyses']['auroc']['pooled_estimate_produced']
    assert not m['analyses']['diagnostic']['pooled_estimate_produced']
    print(f'PASS: {len(checks)} numerical/completeness checks; {len(m["output_files"])} output hashes verified')
