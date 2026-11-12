#!/usr/bin/env python3
"""Create the documented current baseline once, validating historical provenance."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from paed.provenance import create_revision_baseline
if __name__=='__main__':
    b=create_revision_baseline(ROOT)
    print('Validated versioned baseline:',b['revision_id'],len(b['protected_files']),'protected files')
