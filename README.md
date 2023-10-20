# VectorAPI

VectorAPI is a service for managing vector collections and performing vector similarity queries using a PostgreSQL vector database with the `pgvector` extension. Utilizes `fastapi` for the HTTP API, `pgvector` and SQLAlchemy for the vector database side and relies on `pytorch` for computing embeddings.

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

## Making requests

See [API docs](https://grafana.github.io/vectorapi/) for more details.

### Embedding text

```sh
curl -X POST "http://localhost:8889/v1/embeddings" \
    -H "Content-Type: application/json" \
    -d '{"input":"I enjoy taking long walks along the beach.", "model":"BAAI/bge-small-en-v1.5"}'
```

### Adding a vector to a collection

1. Create a collection

```sh
curl -X POST "http://localhost:8889/v1/collections/create" \
    -H "Content-Type: application/json" \
    -d '{"collection_name":"my_collection", "dimension":384}'
```

2. Add a vector to the collection

```sh
curl -X POST "http://localhost:8889/v1/collections/my_collection/upsert" \
    -H "Content-Type: application/json" \
    -d '{"id":"abc1", "metadata":{"key":"value"}, "input":"I enjoy taking long walks along the beach."}'
```

### Vector search

```sh
curl -X POST "http://localhost:8889/v1/collections/my_collection/search" \
    -H "Content-Type: application/json" \
    -d '{"input":"beach walks"}'
```
