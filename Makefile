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

.PHONY: revised revised-raw verify-revised short-report
revised:
	$(PYTHON) scripts/run_revision.py --run-tests

revised-raw:
	$(PYTHON) scripts/run_revision.py --input-dir . --run-tests

verify-revised:
	$(PYTHON) scripts/verify_revision.py

short-report:
	$(PYTHON) scripts/build_short_report.py
