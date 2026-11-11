#!/usr/bin/env python3
"""Inspect staged/committed content without printing possible secret values."""
import argparse
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
RAW_NAMES={'PROSPERO.pdf','List of Variables.pdf','Data extraction paeds cardiac arrest SR progress 5.xlsx - Sheet1.csv'}


def check(staged=False):
    command=['git','diff','--cached','--name-only','--diff-filter=ACMR','-z'] if staged else ['git','ls-files','-z']
    paths=subprocess.check_output(command,cwd=ROOT).decode().split('\0')
    files=[p for p in paths if p]
    problems=[]
    for relative in files:
        path=ROOT/relative
        if path.name in RAW_NAMES or relative.startswith(('data/local/','data/raw/','.venv/','tmp/')):
            problems.append((relative,'original/private/runtime file must not be published'));continue
        if path.suffix.lower() in {'.png','.pdf','.rds'}:continue
        try:
            content=(subprocess.check_output(['git','show',':'+relative],cwd=ROOT).decode() if staged else path.read_text())
        except (UnicodeError,OSError):continue
        if re.search(r'gh[opusr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----',content):
            problems.append((relative,'possible credential/private key'))
        if relative.startswith(('data/curated/','results/','reports/')) or relative=='config/study_context.json':
            if re.search(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}',content,re.I):
                problems.append((relative,'personal contact information'))
            if 'per author correspondence' in content.lower() or 'emailed to ask' in content.lower():
                problems.append((relative,'correspondence-derived narrative'))
    if problems:
        raise SystemExit('\n'.join(f'{path}: {reason}' for path,reason in problems))
    print(f'PASS: {len(files)} '+('staged' if staged else 'tracked')+' files checked; no supplied raw files, contact details, correspondence narrative or credential patterns')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--staged',action='store_true')
    check(parser.parse_args().staged)
