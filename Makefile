DOCKER_TAG = vectorapi:latest
VOLUMES = --mount type=bind,source=$(PWD),target=/app
PORT := 8889
.DEFAULT_GOAL := help

# DOCKER DEV
.PHONY: build
build: ## Build the docker image
	docker compose build

.PHONY: up
up: build ## Run the docker compose stack
	docker compose up

.PHONY: populate-db
populate-db: env ## Populate the database with data
	poetry run python -m scripts.populate_db

# LOCAL DEV
.PHONY: env
env: ## Create the virtual environment
	poetry install

.PHONY: api
api: env ## Run the API
	poetry run uvicorn vectorapi.main:app --host 0.0.0.0 --port $(PORT) --log-level debug --reload

.PHONY: docs
docs: env ## Generate the API documentation
	mkdir -p ./docs
	poetry run python -m scripts.generate_apidoc > ./docs/index.html
	poetry run python -m scripts.generate_openapijson > ./docs/openapi.json

.PHONY: integration
integration: ## Run the integration tests with docker compose
	docker compose -p integration-tests -f docker-compose.yaml -f docker-compose.tests.yaml up --build --abort-on-container-exit
	docker compose -p integration-tests -f docker-compose.yaml -f docker-compose.tests.yaml down

# CI test commands
.PHONY: lint
lint: ## Run the linter
	ruff check -v .

.PHONY: static-analysis
static-analysis: ## Run the static analysis
	mypy .

.PHONY: test
test: ## Run the unit tests
	python -m pytest -v

.PHONY: test-integration
test-integration: ## Run the integration tests
	python -m pytest -v tests/integration --integration

.PHONY: help
help: ## Display this help screen
	@grep -E '^[a-z.A-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
