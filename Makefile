ONESHELL:
.PHONY: test
.PHONY: coverage
.PHONY: diff
.PHONY: lint
.PHONY: clean clean-test clean-pyc clean-build
.PHONY: help
.PHONY: docs
.PHONY: dist
.PHONY: release
.PHONY: install
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -fr .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint: ## check style with flake8
	flake8 commlib tests

test: ## run tests in docker
	./run_tests.sh unit

test-package: ## run integration tests in docker (requires MQTT and Redis brokers)
	./run_tests.sh package

cov: test ## check code coverage quickly with the default Python
	coverage report -m
	coverage xml

cov_html: test
	html

diff: ## Calculate diff
	coverage xml
	diff-cover --compare-branch=origin/devel coverage.xml

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/commlib.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ commlib
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

build: clean ## build source and wheel distributions
	python -m build
	ls -lh dist/

dist: build ## alias for build

install: ## install the package to the active Python's site-packages
	pip install .

install-dev: ## install the package with development dependencies
	pip install -e ".[dev]"

bump-patch: ## bump patch version (v0.12.0 → v0.12.1)
	bump2version patch

bump-minor: ## bump minor version (v0.12.0 → v0.13.0)
	bump2version minor

bump-major: ## bump major version (v0.12.0 → v1.0.0)
	bump2version major

check-dist: build ## check distribution integrity
	twine check dist/*

test-release: check-dist ## upload package to TestPyPI
	twine upload --repository testpypi dist/*

release: bump-patch build check-dist ## bump patch, build, and upload to PyPI
	@echo "Uploading to PyPI..."
	twine upload dist/*
	@echo "Release complete!"
	@echo "Version bumped and tagged automatically by bump2version"
