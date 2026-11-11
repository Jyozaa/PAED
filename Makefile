PYTHON ?= .venv/bin/python

.PHONY: all test raw verify
all:
	$(PYTHON) scripts/run_pipeline.py --run-tests

test:
	$(PYTHON) -m pytest -q

raw:
	$(PYTHON) scripts/run_pipeline.py --input-dir . --run-tests

verify:
	$(PYTHON) scripts/verify_outputs.py

.PHONY: exploratory verify-exploratory
exploratory:
	$(PYTHON) scripts/run_exploratory.py --run-tests

verify-exploratory:
	$(PYTHON) scripts/verify_exploratory.py
