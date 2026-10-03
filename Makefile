# AI Phone Receptionist — common commands.
# Run from the repo root. Requires Docker Compose, uv (for Python), and make.

SHELL := /usr/bin/env bash
COMPOSE := docker compose
API_SERVICE := api
AGENT_SERVICE := agent

.PHONY: help up down restart logs logs-api logs-agent ps build pull \
        migrate migrate-new seed shell-api shell-agent shell-db \
        test eval eval-baseline lint format clean reset-data

help:  ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---------- Stack lifecycle ----------
up:  ## Start the full stack.
	$(COMPOSE) up -d

down:  ## Stop the stack.
	$(COMPOSE) down

restart:  ## Restart all services.
	$(COMPOSE) restart

logs:  ## Tail logs for all services.
	$(COMPOSE) logs -f --tail=200

logs-api:  ## Tail api logs.
	$(COMPOSE) logs -f --tail=200 $(API_SERVICE)

logs-agent:  ## Tail agent logs.
	$(COMPOSE) logs -f --tail=200 $(AGENT_SERVICE)

ps:  ## List running services.
	$(COMPOSE) ps

build:  ## Build all images.
	$(COMPOSE) build

pull:  ## Pull base images.
	$(COMPOSE) pull

# ---------- Database ----------
migrate:  ## Run Alembic migrations.
	$(COMPOSE) exec $(API_SERVICE) alembic upgrade head

migrate-new:  ## Create a new Alembic migration. Usage: make migrate-new m="add foo"
	$(COMPOSE) exec $(API_SERVICE) alembic revision --autogenerate -m "$(m)"

seed:  ## Seed the first business + admin user.
	$(COMPOSE) exec $(API_SERVICE) python -m api.scripts.seed

shell-db:  ## Open psql against Postgres.
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-receptionist} $${POSTGRES_DB:-receptionist}

# ---------- Shells ----------
shell-api:  ## Open a shell in the api container.
	$(COMPOSE) exec $(API_SERVICE) bash

shell-agent:  ## Open a shell in the agent container.
	$(COMPOSE) exec $(AGENT_SERVICE) bash

# ---------- Testing ----------
test:  ## Run unit tests (api + agent).
	$(COMPOSE) exec $(API_SERVICE) pytest -q

eval:  ## Run the scenario eval suite (text mode, no audio).
	$(COMPOSE) exec $(AGENT_SERVICE) python -m eval.run_eval --suite eval/scenarios

eval-baseline:  ## Save current eval results as the baseline.
	$(COMPOSE) exec $(AGENT_SERVICE) python -m eval.run_eval --suite eval/scenarios --save-baseline

# ---------- Code quality ----------
lint:  ## Run ruff on Python code.
	ruff check api agent eval

format:  ## Format Python code.
	ruff format .

# ---------- Maintenance ----------
clean:  ## Remove caches and build artifacts.
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache

reset-data:  ## Delete Postgres and Redis volumes. DESTRUCTIVE.
	$(COMPOSE) down -v