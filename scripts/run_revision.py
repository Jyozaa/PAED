#!/usr/bin/env python3
"""Rebuild the intentional 17-model revision, its comparisons and LaTeX/PDF."""
from pathlib import Path
import argparse
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from paed.revision_pipeline import run
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input-dir',type=Path);parser.add_argument('--output-dir',type=Path);parser.add_argument('--run-tests',action='store_true')
    a=parser.parse_args();m=run(ROOT,a.output_dir,a.input_dir,a.run_tests)
    print('Revised counts:',m['counts']);print('AUROC:',m['auroc']);print('Diagnostic identical:',m['diagnostic_numerically_identical_to_previous'])
    print('PDF:',m['pdf']['pages'],'pages; tests:',m['tests']['status'])
