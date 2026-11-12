#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from paed.revision_pipeline import verify
if __name__=='__main__':print('PASS:',len(verify(ROOT)),'revised provenance, numerical, output-hash and PDF checks')
