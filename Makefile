DOCKER_TAG = vectorapi:latest
VOLUMES = --mount type=bind,source=$(PWD),target=/app
PORT := 8889

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
	poetry run uvicorn vectorapi.main:app --host 0.0.0.0 --port $(PORT) --log-level debug --reload
.PHONY: api

docs: env
	mkdir -p ./docs
	poetry run python -m scripts.generate_apidoc > ./docs/apidocs.html
	poetry run python -m scripts.generate_openapijson > ./docs/openapi.json
.PHONY: docs
