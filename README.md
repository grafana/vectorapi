# Vector API

This directory contains a Python package with HTTP endpoints and logic for sentence embeddings.
It uses `fastapi` for the HTTP framework, and makes use of the `pytorch` package for much of the computation.

## Getting started

```sh
make up
```

### Examples: Embeddings

#### Request

POST http://localhost:8889/v1/embeddings

```json
{
  "input": "Why is Loki sloww2?",
  "model": "BAAI/bge-small-en-v1.5"
}
```

#### Response

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

### Examples: Sentence Similarity

POST http://localhost:8889/v1/similarity

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

#### Response

```
[
    0.9684778451919556,
    0.36870819330215454,
    0.8106681108474731
]
```

## Updating OpenAPI docs

To update the docs, run the `make docs` command.
