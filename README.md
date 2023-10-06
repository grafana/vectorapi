# VectorAPI

This Python package provides an API for sentence embeddings and managing a Vector Database powered by PostgreSQL. It utilizes the `fastapi` framework for handling HTTP requests, `pgvector`, and SQLAlchemy for Vector Database support, and relies on the `pytorch` package for embeddings computation.

## Getting started

To get started with the Vector API, run:

```sh
make up
```

## PGVector

### Collection Operations

#### Create a collection (POST)

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

#### Get a collection (GET)

Endpoint: GET http://localhost:8889/v1/collections/{collection_name}

This request calls postgres and gets the collection {collection_name}.


_Response_

```
{
    "name": "templates",
    "dimension": 128
}
```


#### Delete a collection (POST)

Endpoint: POST http://localhost:8889/v1/collections/delete

This request calls postgres and deletes the collection {collection_name}.

```
{
  "collection_name": "templates"
}

```


#### List collections (GET)

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

### Collection Point Operations

#### Insert collection point (POST)

Endpoint: POST http://localhost:8889/v1/{collection_name}/insert

This request inserts a collection point with the specified id, embedding, and optional metadata into the collection.

```
{
  "id": "point_id_1",
  "embedding": [0.1, 0.2, 0.3],
  "metadata": {
    "key": "value"
  }
}
```

#### Update a collection point (POST)

Endpoint: POST http://localhost:8889/v1/{collection_name}/update

This request updates the collection point with the specified id with new embedding and metadata.

```
{
  "id": "point_id_1",
  "embedding": [0.4, 0.5, 0.6],
  "metadata": {
    "new_key": "new_value"
  }
}
```

#### Get a collection point (GET)

Endpoint: GET http://localhost:8889/v1/{collection_name}/{id}

This request retrieves the collection point with the specified id from the collection.

_Response_

```
{
    "id": "point_id_1",
    "embedding": [0.4, 0.5, 0.6],
    "metadata": {
      "new_key": "new_value"
    }
}
```

#### Delete a collection point (DELETE)

Endpoint: DELETE http://localhost:8889/v1/{collection_name}/delete/{id}

This request deletes the collection point with the specified id from the collection.

#### Query collection points (POST)

Endpoint: POST http://localhost:8889/v1/collection-points/query

This request performs a query on the collection points, searching for points similar to the given query vector. You can specify additional parameters like `limit` and `filter` for filtering results.

```
{
  "query": [0.7, 0.8, 0.9],
  "limit": 10
}
```

_Response_

```
[
  {
    "id": "point_id_1",
    "embedding": [0.4, 0.5, 0.6],
    "metadata": {
      "key": "new_value"
    },
    "cosine_similarity": 0.95
  },
  {
    "id": "point_id_2",
    "embedding": [0.5, 0.6, 0.7],
    "metadata": {
      "key": "value"
    },
    "cosine_similarity": 0.92
  }
]
```

#### Query collection points with advanced filtering (POST)

Endpoint: POST http://localhost:8889/v1/collection-points/query

##### Example 1
```
{
  "query":  [0.4, 0.5, 0.6],
  "top_k": 1,
  "filter":
    {
      "key":
        {
          "$eq": "value"
        }
    },
}
```

_Response_

```
[
  {
    "id": "point_id_2",
    "embedding": [0.5, 0.6, 0.7],
    "metadata": {
      "key": "value"
    },
    "cosine_similarity": 0.92
  }
]
```

This filter passes the equality operator to match the column `key` from the metadata column to the `value` passed.
The API will return the `top_k` (if available) closest points that match the filter.

##### Example 2

```
{
  "query":  [0.4, 0.5, 0.6],
  "top_k": 10,
  "filter": {
    "$or": [
      {
        "key": {
          "$eq": "value"
        }
      },
      {
        "key": {
          "$eq": "new_value"
        }
      }
    ]
  },
}
```

_Response_

```
[
  {
    "id": "point_id_1",
    "embedding": [0.4, 0.5, 0.6],
    "metadata": {
      "key": "new_value"
    },
    "cosine_similarity": 0.95
  },
  {
    "id": "point_id_2",
    "embedding": [0.5, 0.6, 0.7],
    "metadata": {
      "key": "value"
    },
    "cosine_similarity": 0.92
  }
]
```

The `$or` operator supports passing multiple filters to the query call

Supported single value filter operators are:
- Equality: `$eq`
- Inequality: `$ne`

Supported multiple values filter operators are:
- `$or`
- `$and`


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
