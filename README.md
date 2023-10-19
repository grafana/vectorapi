# VectorAPI

VectorAPI is a service for managing vector collections and performing vector similarity queries using a PostgreSQL vector database with the `pgvector` extension. Utilizes `fastapi` for the HTTP API, `pgvector` and SQLAlchemy for the vector database side and relies on `pytorch` for computing embeddings.

## Getting started

### Existing database

To get started with the VectorAPI, run:

```sh
docker run -p 8889:8889 -e DB_URL=postgres://postgres:mysecretpassword@localhost:5432/db grafana/vectorapi
```

### New database

You can bring up a database using the `ankane/pgvector` image:

```sh
docker run -p 5432:5432 -e POSTGRES_PASSWORD=mysecretpassword -d ankane/pgvector
```

Then, run the VectorAPI container with the `DB_URL` environment variable set to the database URL:

```sh
docker run --network="host" -e DB_URL=postgres://postgres:mysecretpassword@localhost:5432/db grafana/vectorapi
```

Alternatively, using docker compose:

```sh
docker compose up --build
```

To populate the local DB instance with test data from huggingface run:

```sh
make populate-db
```

[Grafana public datasets](https://huggingface.co/grafanalabs)

[API docs](./API.md)
