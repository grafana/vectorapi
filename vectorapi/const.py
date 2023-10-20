import os

DEFAULT_EMBEDDING_MODEL = os.getenv("DEFAULT_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
VECTORAPI_STORE_SCHEMA = os.getenv("VECTORAPI_STORE_SCHEMA", "vector")
