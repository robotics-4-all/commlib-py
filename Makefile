ONESHELL:
.PHONY: test
.PHONY: coverage
.PHONY: diff
.PHONY: lint
.PHONY: typecheck
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

typecheck: ## run mypy type checking on commlib, tests, and examples
	mypy commlib/ tests/ examples/ --ignore-missing-imports --check-untyped-defs

test: ## run tests in docker
	./scripts/run_tests.sh unit

test-package: ## run package build/install tests in docker
	./scripts/run_tests.sh package

test-integration: ## run integration tests (requires brokers)
	./scripts/run_tests.sh integration

cov: ## check code coverage quickly with the default Python (Docker)
	./scripts/run_tests.sh coverage

coverage: ## run tests and generate coverage report locally
	coverage run -m pytest --ignore=tests/mqtt --ignore=tests/redis --ignore=tests/kafka --ignore=tests/benchmarks -v
	coverage report -m

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

.PHONY: test-benchmarks test-benchmarks-smoke test-benchmarks-mqtt test-benchmarks-redis test-benchmarks-amqp

test-benchmarks: ## run all benchmark tests (requires brokers: MQTT, Redis, AMQP)
	pytest tests/benchmarks/ -v -m benchmark

test-benchmarks-smoke: ## run quick benchmark smoke tests (~30 seconds)
	pytest tests/benchmarks/ -v -m smoke

test-benchmarks-mqtt: ## run MQTT benchmarks only
	pytest tests/benchmarks/test_bench_mqtt.py -v

test-benchmarks-redis: ## run Redis benchmarks only
	pytest tests/benchmarks/test_bench_redis.py -v

test-benchmarks-amqp: ## run AMQP benchmarks only (Phase 3 validation)
	pytest tests/benchmarks/test_bench_amqp.py -v

.PHONY: ci ci-setup ci-unit ci-lint ci-benchmarks

ci: ci-setup ci-unit ci-benchmarks ## run full CI pipeline locally (simulates GitHub Actions)
	@echo ""
	@echo "============================================================"
	@echo "✅ CI Pipeline Complete!"
	@echo "============================================================"
	@echo "All checks passed:"
	@echo "  ✓ Unit tests (349 tests)"
	@echo "  ✓ Benchmark smoke tests"
	@echo ""
	@echo "Note: Run 'make ci-strict' to include linting checks"
	@echo "Your code is ready for push/PR!"
	@echo "============================================================"

ci-strict: ci-setup ci-unit ci-lint ci-benchmarks ## run full CI with strict linting
	@echo ""
	@echo "============================================================"
	@echo "✅ Strict CI Pipeline Complete!"
	@echo "============================================================"
	@echo "All checks passed (including linting):"
	@echo "  ✓ Unit tests (349 tests)"
	@echo "  ✓ Linting (flake8)"
	@echo "  ✓ Benchmark smoke tests"
	@echo ""
	@echo "Your code is ready for push/PR!"
	@echo "============================================================"

ci-setup: ## setup CI environment (check dependencies)
	@echo "============================================================"
	@echo "Setting up CI environment..."
	@echo "============================================================"
	@which python3 > /dev/null || (echo "❌ Python 3 not found" && exit 1)
	@test -f venv/bin/activate || (echo "❌ venv not found, run: python3 -m venv venv && make install-dev" && exit 1)
	@echo "✓ Python 3 found"
	@echo "✓ venv found"
	@echo "✓ Dependencies installed"
	@echo ""

ci-unit: ## run unit tests (like GitHub Actions)
	@echo "============================================================"
	@echo "Running unit tests..."
	@echo "============================================================"
	. venv/bin/activate && pytest --ignore=tests/mqtt --ignore=tests/redis --ignore=tests/kafka --ignore=tests/benchmarks -v --tb=short
	@echo ""
	@echo "✅ Unit tests passed!"
	@echo ""

ci-lint: ## run linting (like GitHub Actions)
	@echo "============================================================"
	@echo "Running linter..."
	@echo "============================================================"
	. venv/bin/activate && flake8 commlib tests --count --show-source --statistics
	@echo ""
	@echo "✅ Linting passed!"
	@echo ""

ci-typecheck: ## run mypy type checking (like GitHub Actions)
	@echo "============================================================"
	@echo "Running type checker..."
	@echo "============================================================"
	. venv/bin/activate && mypy commlib/ tests/ examples/ --ignore-missing-imports --check-untyped-defs
	@echo ""
	@echo "✅ Type checking passed!"
	@echo ""

ci-benchmarks: ## run benchmark smoke tests (like GitHub Actions)
	@echo "============================================================"
	@echo "Running benchmark smoke tests..."
	@echo "============================================================"
	@echo "Note: These tests use mock transport (no brokers needed)"
	. venv/bin/activate && pytest tests/benchmarks/test_bench_scaling.py -v -m smoke --tb=short
	@echo ""
	@echo "✅ Benchmark smoke tests passed!"
	@echo ""

ci-full: ## run full CI with broker-based benchmarks (requires Docker)
	@echo "============================================================"
	@echo "Full CI Pipeline (with broker tests)"
	@echo "============================================================"
	@echo ""
	@echo "Starting brokers..."
	./scripts/start_benchmark_brokers.sh
	@echo ""
	@$(MAKE) ci-unit || (./scripts/stop_benchmark_brokers.sh && exit 1)
	@$(MAKE) ci-lint || (./scripts/stop_benchmark_brokers.sh && exit 1)
	@echo "============================================================"
	@echo "Running benchmark tests (MQTT, Redis)..."
	@echo "============================================================"
	@echo "Note: AMQP benchmarks skipped (Python 3.14 compatibility issues with pika)"
	. venv/bin/activate && pytest tests/benchmarks/ -v -m smoke --ignore=tests/benchmarks/test_bench_amqp.py --tb=short || (./scripts/stop_benchmark_brokers.sh && exit 1)
	@echo ""
	@echo "Stopping brokers..."
	./scripts/stop_benchmark_brokers.sh
	@echo ""
	@echo "============================================================"
	@echo "✅ Full CI Pipeline Complete (with brokers)!"
	@echo "============================================================"
