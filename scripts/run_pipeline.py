#!/usr/bin/env python3
"""One-command entry point; public curated mode needs no original files."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from paed.pipeline import run

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path,help='Discover all three originals recursively and refresh curated aggregate records')
    parser.add_argument('--output-dir',type=Path,help='Alternative destination for generated results, figures, reports and manifest')
    parser.add_argument('--run-tests',action='store_true',help='Run complete automated test suite after output validation')
    args=parser.parse_args()
    manifest=run(ROOT,args.output_dir,args.input_dir,args.run_tests)
    print('Completed extraction-level synthesis:',manifest['counts'])
    print('AUROC:',manifest['analyses']['auroc']['status'])
    print('Diagnostic:',manifest['analyses']['diagnostic']['status'])
    print('Tests:',manifest['tests']['status'])
