# VectorAPI API docs

## Collection Operations

A collection represents a set of vectors with metadata, which can be queried and searched.
In postgres, they're are stored as tables under the schema defined by the `VECTORAPI_STORE_SCHEMA` environment variable (default: `vector`).

### Create a collection (POST)

Endpoint: POST http://localhost:8889/v1/collections/create

Create a collection under `vector` schema with the following columns.

- id: string
- embedding: a list of floats with the dimension specified in the request.
- metadata: JSON metadata column

```json
{
  "collection_name": "templates",
  "dimension": 128
}
```

_Response_

```json
{
  "name": "templates",
  "dimension": 128
}
```

### Get a collection (GET)

Endpoint: GET http://localhost:8889/v1/collections/{collection_name}

Get the collection {collection_name}.

_Response_

```json
{
  "name": "templates",
  "dimension": 128
}
```

### Delete a collection (POST)

Endpoint: POST http://localhost:8889/v1/collections/delete

Delete the collection {collection_name}.

```json
{
  "collection_name": "templates"
}
```

### List collections (GET)

Endpoint: GET http://localhost:8889/v1/collections

Get all collections that are present in the DB.

_Response_

```json
[
  {
    "name": "templates",
    "dimension": 128
  },
  {
    "name": "alerts",
    "dimension": 384
  }
]
```

## Collection Point Operations

### Upsert collection point (POST)

Endpoint: POST http://localhost:8889/v1/{collection_name}/upsert

Upsert a collection point with the specified id, embedding, and optional metadata into the collection.

#### Upserting with an embedding input

```json
{
  "id": "point_id_1",
  "embedding": [0.1, 0.2, 0.3],
  "metadata": {
    "key": "value"
  }
}
```

#### Upserting from text input

Upsert a collection point using text. Embeddings will be calculated on the fly using the model specified in `model_name`.

```json
{
  "id": "point_id_1",
  "input": "foo",
  "metadata": {
    "key": "value"
  },
  "model_name": "BAAI/bge-small-en-v1.5"
}
```

#### Get a collection point (GET)

Endpoint: GET http://localhost:8889/v1/{collection_name}/get/{id}

Retrieve the collection point with the specified id from the collection.

_Response_

```json
{
  "id": "point_id_1",
  "embedding": [0.4, 0.5, 0.6],
  "metadata": {
    "new_key": "new_value"
  }
}
```

### Delete a collection point (DELETE)

Endpoint: DELETE http://localhost:8889/v1/{collection_name}/delete/{id}

Delete the collection point with the specified id from the collection.

### Query collection points (POST)

Endpoint: POST http://localhost:8889/v1/{collection_name}/query

Query the collection points, searching for points similar to the given query vector. You can specify additional parameters:

- `top_k`: the number of results to return (default: 10)
- `filter`: search filters to apply on the metadata

```json
{
  "query": [0.7, 0.8, 0.9],
  "top_k": 10
}
```

_Response_

```json
[
  {
    "id": "point_id_1",
    "embedding": [0.4, 0.5, 0.6],
    "metadata": {
      "key": "new_value"
    },
    "score": 0.95
  },
  {
    "id": "point_id_2",
    "embedding": [0.5, 0.6, 0.7],
    "metadata": {
      "key": "value"
    },
    "score": 0.92
  }
]
```

#### Query collection points with advanced filtering (POST)

Endpoint: POST http://localhost:8889/v1/collection-points/query

#### Example 1

```json
{
  "query": [0.4, 0.5, 0.6],
  "top_k": 1,
  "filter": {
    "key": {
      "$eq": "value"
    }
  }
}
```

_Response_

```json
[
  {
    "id": "point_id_2",
    "embedding": [0.5, 0.6, 0.7],
    "metadata": {
      "key": "value"
    },
    "score": 0.92
  }
]
```

This filter passes the equality operator to match the column `key` from the metadata column to the `value` passed.
The API will return the `top_k` (if available) closest points that match the filter.

#### Example 2

```json
{
  "query": [0.4, 0.5, 0.6],
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
  }
}
```

_Response_

```json
[
  {
    "id": "point_id_1",
    "embedding": [0.4, 0.5, 0.6],
    "metadata": {
      "key": "new_value"
    },
    "score": 0.95
  },
  {
    "id": "point_id_2",
    "embedding": [0.5, 0.6, 0.7],
    "metadata": {
      "key": "value"
    },
    "score": 0.92
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

### Search collection points (POST)

Endpoint: POST http://localhost:8889/v1/{collection_name}/search

Search the collection points, searching for points similar to the given input text. It it similar to the /query endpoint which takes a vector input, whereas the /search endpoint takes a text input (and does the embedding on the fly).

- `top_k`: the number of results to return (default: 10)
- `top_k`: the number of results to return (default: 10)
- `filter`: search filters to apply on the metadata

```json
{
  "input": "foo",
  "top_k": 10
}
```

_Response_

```json
[
  {
    "id": "point_id_1",
    "embedding": [0.4, 0.5, 0.6],
    "metadata": {
      "key": "new_value"
    },
    "score": 0.95
  },
  {
    "id": "point_id_2",
    "embedding": [0.5, 0.6, 0.7],
    "metadata": {
      "key": "value"
    },
    "score": 0.92
  }
]
```

## Embeddings

### Calculate Embeddings

Endpoint: POST http://localhost:8889/v1/embeddings

```json
{
  "input": "Why is Loki sloww2?",
  "model": "BAAI/bge-small-en-v1.5"
}
```

_Response_

```json
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

### Get Sentence Similarity

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
