.PHONY: setup test evolve arena dashboard lint clean help

help:  ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup:  ## Install all dependencies
	pip install -e ".[dev]"

test:  ## Run all tests
	python -m pytest tests/ -v

lint:  ## Check code style
	python -m py_compile darwinia/__main__.py
	@echo "Syntax OK"

evolve:  ## Run 50-generation evolution
	python -m darwinia evolve -g 50

evolve-quick:  ## Run quick 10-generation demo
	python -m darwinia evolve -g 10

evolve-json:  ## Run evolution with JSON output
	python -m darwinia evolve -g 50 --json

arena:  ## Test champion in adversarial arena
	python -m darwinia arena

arena-json:  ## Arena test with JSON output
	python -m darwinia arena --json

dashboard:  ## Launch Streamlit dashboard
	streamlit run dashboard/app.py

info:  ## Show project info
	python -m darwinia info

clean:  ## Remove output files
	rm -rf output/*
