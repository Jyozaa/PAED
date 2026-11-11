#!/usr/bin/env python3
"""Validate scenarios and output hashes while protecting the original analysis."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from paed.exploratory_pipeline import verify
if __name__=='__main__':
    checks=verify(ROOT)
    print('PASS:',len(checks),'exploratory numerical/completeness/preservation checks and all recorded output hashes')
