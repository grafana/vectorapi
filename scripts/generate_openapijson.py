"""Script to export the OpenAPI json file."""

import json

from vectorapi.main import app

if __name__ == "__main__":
    print(json.dumps(app.openapi()))
