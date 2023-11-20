PORT := 8889
.DEFAULT_GOAL := help

# DOCKER DEV
.PHONY: build
build: ## Build the docker image
	docker compose build

.PHONY: up
up: build ## Run the docker compose stack
	docker compose up

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
	mypy vectorapi

.PHONY: test
test: ## Run the unit tests
	python -m pytest -v

.PHONY: test-integration
test-integration: ## Run the integration tests
	python -m pytest -v tests/integration --integration

.PHONY: drone
drone: ## Regenerate and sign drone.yml
	drone jsonnet --stream --format --source .drone/drone.jsonnet --target .drone/drone.yml
	drone lint .drone/drone.yml --trusted
	@drone sign --save grafana/vectorapi .drone/drone.yml || echo "You must set DRONE_SERVER and DRONE_TOKEN. These values can be found on your [drone account](http://drone.grafana.net/account) page."

.PHONY: create-collection
create-collection: ## Create grafana.promql.templates collection
	echo "Creating the collection..."
	curl -X POST "http://localhost:8889/v1/collections/create" \
		-H "Content-Type: application/json" \
		-d '{"collection_name":"grafana.promql.templates", "dimension":384}'

.PHONY: populate-db
populate-db: create-collection ## Populate the database with test data
	echo "Populating database with test data...";
	json=$$(curl -s -L https://huggingface.co/datasets/grafanalabs/promql-test-data/resolve/main/promql-test-data.json); counter=0;\
    echo "Loading..."; \
    echo "$$json" | jq -c '.[]' | while IFS= read -r line; do counter=$$((counter + 1)); \
        if [ $$((counter % 100)) -eq 0 ]; then \
            echo "Still loading... $$counter / $$(echo "$$json" | jq 'length')"; \
        fi; curl -s -X POST -H "Content-Type: application/json" -d "$$line" http://localhost:8889/v1/collections/grafana.promql.templates/upsert > /dev/null; \
    done; echo "Done!"

.PHONY: help
help: ## Display this help screen
	@grep -E '^[a-z.A-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
