def read_markdown_file(filepath: str):
    with open(filepath, "r") as fh:
        return fh.read()


OPENAPI_DESCRIPTION = read_markdown_file("vectorapi/docs/description.md")


OPENAPI_TAGS_METADATA = [
    {"name": "embeddings", "description": read_markdown_file("vectorapi/docs/tags_embeddings.md")},
    {
        "name": "collections",
        "description": read_markdown_file("vectorapi/docs/tags_collections.md"),
    },
    {
        "name": "points",
        "description": read_markdown_file("vectorapi/docs/tags_points.md"),
    },
]
