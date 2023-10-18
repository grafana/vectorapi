# VectorAPI

VectorAPI is a service for managing vector collections and performing vector similarity queries using a PostgreSQL vector database with the `pgvector` extension. Utilizes `fastapi` for the HTTP API, `pgvector` and SQLAlchemy for the vector database side and relies on `pytorch` for computing embeddings.

## Getting started

To get started with the VectorAPI, run:

```sh
make up
```

To populate the local DB instance with test data from huggingface run:

```sh
make populate-db
```

[Grafana public datasets](https://huggingface.co/grafanalabs)

[API docs](./API.md)
