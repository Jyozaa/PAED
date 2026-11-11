#!/usr/bin/env python3
"""Execute only the separate assumption-dependent pooling layer."""
from pathlib import Path
import argparse
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from paed.exploratory_pipeline import run
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path);p.add_argument('--run-tests',action='store_true')
    a=p.parse_args();m,checks=run(ROOT,a.output_dir,a.run_tests)
    print('EXPLORATORY AUROC:',m['auroc']);print('EXPLORATORY diagnostic:',m['diagnostic'])
    print('Verification:',len(checks),'checks;',len(m['output_files']),'output hashes; tests',m['tests']['status'])
