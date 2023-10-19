# VectorAPI

VectorAPI is a service for managing vector collections and performing vector similarity queries using a PostgreSQL vector database with the `pgvector` extension. Utilizes `fastapi` for the HTTP API, `pgvector` and SQLAlchemy for the vector database side and relies on `pytorch` for computing embeddings.

### [API docs](./API.md)

## Getting started

### Existing database

To get started with the VectorAPI, run:

```sh
docker run -p 8889:8889 -e DB_URL=postgresql+asyncpg://<user>:<password>@<host>:<port>/<dbname> grafana/vectorapi
```

### New database

You can bring up a postgres database (`ankane/pgvector`) and vectorapi instance using docker compose:

```sh
docker compose up --build
```

To populate the local DB instance with test data from HuggingFace (see [Grafana public datasets](https://huggingface.co/grafanalabs)) run:

```sh
make populate-db
```
