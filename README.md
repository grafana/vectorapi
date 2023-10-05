# Vector API

This Python package provides an API for sentence embeddings and managing a Vector Database powered by PostgreSQL. It utilizes the `fastapi` framework for handling HTTP requests, `pgvector`, and SQLAlchemy for Vector Database support, and relies on the `pytorch` package for embeddings computation.

## Getting started

To get started with the Vector API, run:

```sh
make up
```

## PGVector

### Collection Operations

#### Create a collection

Endpoint: POST http://localhost:8889/v1/collections/create

This request calls postgres and creates a collection under `vector` schema with the following columns.

- id: string
- embedding: a list of floats with the dimension specified in the request.
- metadata: JSON metadata column

```
{
  "collection_name": "templates",
  "dimension": 128
}
```


_Response_

```
{
    "name": "templates",
    "dimension": 128
}
```

#### Get a collection

Endpoint: GET http://localhost:8889/v1/collections/{collection_name}

This request calls postgres and gets the collection {collection_name}.


_Response_

```
{
    "name": "templates",
    "dimension": 128
}
```


#### Delete a collection

Endpoint: POST http://localhost:8889/v1/collections/delete

This request calls postgres and deletes the collection {collection_name}.

```
{
  "collection_name": "templates"
}

```


#### List collections

Endpoint: GET http://localhost:8889/v1/collections

This request calls postgres and get all collections created in the DB.


_Response_

```
[
    {
        "name": "templates",
        "dimension": 128
    },
    {
        "name": "alerts",
        "dimension": 384
    },
]
```

### Embeddings

#### Calculate Embeddings

Endpoint: POST http://localhost:8889/v1/embeddings

```json
{
  "input": "Why is Loki sloww2?",
  "model": "BAAI/bge-small-en-v1.5"
}
```

_Response_

```
{
    "index": 0,
    "object": "embedding",
    "embedding": [
        -0.06351014971733093,
        -0.02376665361225605,
        ...
        -0.010538085363805294,
        0.04279552400112152
    ]
}
```

#### Get Sentence Similarity

Endpoint: POST http://localhost:8889/v1/similarity

```json
{
  "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
  "sourceSentence": "Machine learning is so easy.",
  "sentences": [
    "Machine learning is very easy.",
    "Machine learning is extremely hard.",
    "Artificial intelligence is easy."
  ]
}
```

_Response_

```
[
    0.9684778451919556,
    0.36870819330215454,
    0.8106681108474731
]
```

## Updating OpenAPI docs

To update the docs, run the `make docs` command.
