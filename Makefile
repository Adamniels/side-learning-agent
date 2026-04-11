SHELL := /bin/bash

.DEFAULT_GOAL := help

PYTHON ?= python3
VENV := .venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn
RUFF := $(VENV)/bin/ruff

UVICORN_APP := session_designer.api.main:app
HOST ?= 127.0.0.1
PORT ?= 8010

FIXTURE ?= examples/sample_context.json
MOCK_REVISIONS ?= 2

# Align with side-learning-backend appsettings.Development.json (SessionDesigner:SharedSecret)
SESSION_DESIGNER_SHARED_SECRET ?= dev_session_designer_secret_change_me

.PHONY: help venv install install-dev clean ruff ruff-fix run-api run-api-mock watch-api health cli-version cli-run cli-run-mock

help: ## Show all available commands
	@echo "Useful commands:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

venv: ## Create .venv (override interpreter with PYTHON=...)
	@test -d "$(VENV)" || $(PYTHON) -m venv "$(VENV)"
	@echo "Virtualenv ready at $(VENV)/ (activate: source $(VENV)/bin/activate)"

install: venv ## Install package (editable)
	$(VENV_PIP) install -U pip
	$(VENV_PIP) install -e .

install-dev: venv ## Install package with dev extras (ruff)
	$(VENV_PIP) install -U pip
	$(VENV_PIP) install -e ".[dev]"

clean: ## Remove caches and build artifacts (does not remove .venv)
	find . -path './.venv' -prune -o -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -path './.venv' -prune -o -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete 2>/dev/null || true
	rm -rf .ruff_cache build dist *.egg-info .eggs

ruff: install-dev ## Run Ruff linter
	$(RUFF) check session_designer

ruff-fix: install-dev ## Run Ruff with auto-fix
	$(RUFF) check --fix session_designer

run-api: install ## Run FastAPI session designer (set SESSION_DESIGNER_SHARED_SECRET; optional ANTHROPIC_API_KEY)
	@test -f "$(UVICORN)" || { echo "Run: make install"; exit 1; }
	SESSION_DESIGNER_SHARED_SECRET="$(SESSION_DESIGNER_SHARED_SECRET)" $(UVICORN) $(UVICORN_APP) --host $(HOST) --port $(PORT)

run-api-mock: install ## Run FastAPI with mock LLM (no Anthropic key)
	@test -f "$(UVICORN)" || { echo "Run: make install"; exit 1; }
	SESSION_DESIGNER_SHARED_SECRET="$(SESSION_DESIGNER_SHARED_SECRET)" \
	SESSION_DESIGNER_USE_MOCK=true \
	$(UVICORN) $(UVICORN_APP) --host $(HOST) --port $(PORT)

watch-api: install-dev ## Run API with uvicorn --reload (mock LLM)
	@test -f "$(UVICORN)" || { echo "Run: make install-dev"; exit 1; }
	SESSION_DESIGNER_SHARED_SECRET="$(SESSION_DESIGNER_SHARED_SECRET)" \
	SESSION_DESIGNER_USE_MOCK=true \
	$(UVICORN) $(UVICORN_APP) --host $(HOST) --port $(PORT) --reload

health: ## GET /health on local designer (PORT)
	curl -sS -w "\nHTTP %{http_code}\n" "http://$(HOST):$(PORT)/health"

cli-version: install ## Print CLI version
	$(VENV_PY) -m session_designer.cli.main version

cli-run: install ## Run CLI against FIXTURE (needs ANTHROPIC_API_KEY or use cli-run-mock)
	$(VENV_PY) -m session_designer.cli.main run --fixture $(FIXTURE)

cli-run-mock: install ## Run CLI with mock provider (FIXTURE, MOCK_REVISIONS)
	$(VENV_PY) -m session_designer.cli.main run --fixture $(FIXTURE) --mock --max-revisions $(MOCK_REVISIONS)
