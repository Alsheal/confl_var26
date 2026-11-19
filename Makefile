PYTHON ?= python3

.PHONY: install test run

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m pytest

run:
	PYTHONPATH=src $(PYTHON) -m confl -i $(FILE)