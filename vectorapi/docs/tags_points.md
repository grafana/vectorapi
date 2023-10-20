CollectionPoints are the individual vectors (and their metadata) that make up a collection.

### Metadata search filters

The API supports filtering the search results by metadata, through the `filter` parameter. This can be set in both the `/query` (search by vector) and `/search` (search by text) endpoints.

Supported single value filter operators are:

- Equality: `$eq`
- Inequality: `$ne`

Supported multiple values filter operators are:

- `$or`: The `$or` operator supports passing multiple filters to the query call
- `$and`

#### Example vector search request with simple match filter

Endpoint: POST http://localhost:8889/v1/collections/{collection_name}/search

```json
{
  "input": "A small phone with a great camera",
  "filter": {
    "category": {
      "$eq": "electronics"
    }
  }
}
```

#### Example vector search request with OR filter

Endpoint: POST http://localhost:8889/v1/collections/{collection_name}/query

```json
{
  "query": [0.4, 0.5, 0.6],
  "filter": {
    "$or": [
      {
        "category": {
          "$eq": "electronics"
        }
      },
      {
        "category": {
          "$eq": "clothing"
        }
      }
    ]
  }
}
```
