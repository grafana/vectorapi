DOCKER_TAG = vectorapi:latest
VOLUMES = --mount type=bind,source=$(PWD),target=/app
PORT := 8889
VECTORAPI_STORE_CLIENT := memory

# DOCKER DEV
build: 
	docker compose build
.PHONY: build

up: build
	docker compose up
.PHONY: up

# LOCAL DEV
env:
	poetry install
.PHONY: env

api: env
	VECTORAPI_STORE_CLIENT=$(VECTORAPI_STORE_CLIENT) poetry run uvicorn vectorapi.main:app --host 0.0.0.0 --port $(PORT) --log-level debug --reload
.PHONY: api

docs: env
	mkdir -p ./docs
	poetry run python -m scripts.generate_apidoc > ./docs/apidocs.html
	poetry run python -m scripts.generate_openapijson > ./docs/openapi.json
.PHONY: docs

integration: 
	docker compose -p integration-tests -f docker-compose.yaml -f docker-compose.tests.yaml up --build --abort-on-container-exit
	docker compose -p integration-tests -f docker-compose.yaml -f docker-compose.tests.yaml down
.PHONY: integration

unit_tests:
	poetry run pytest -v
.PHONY: unit_tests