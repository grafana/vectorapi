import ast
from datasets import load_dataset

import requests
import ast
import hashlib
from typing import Dict, List


from tqdm import tqdm

COLLECTION = "test1.promql.templates"
VECTORAPI = "http://localhost:8889/v1"


def create_vector_collection(name: str, dimension: int) -> Dict:
    payload = {"collection_name": name, "dimension": dimension, "exist_ok": True}
    response = requests.post(f"{VECTORAPI}/collections/create", headers={}, json=payload)
    response.raise_for_status()
    return response.json()


def upsert_point(payload: Dict) -> None:
    url = f"{VECTORAPI}/collections/{COLLECTION}/upsert"
    response = requests.post(url, headers={}, json=payload)
    response.raise_for_status()


def load_and_format_dataset() -> List[Dict]:
    # Load dataset from HuggingFace
    dataset = load_dataset("grafanalabs/promql-test-data")
    data = dataset["test"]
    data = [{**row, "embeddings": ast.literal_eval(row["embeddings"])} for row in data]
    return data


def generate_payload(data: List[Dict]) -> List[Dict]:
    return [
        {
            "id": hashlib.sha256(row["promql"].encode("utf-8")).hexdigest(),
            "embedding": row["embeddings"],
            "metadata": {
                "promql": row["promql"],
                "description": row["description"],
                "metric_type": row["metric_type"],
            },
        }
        for row in data
    ]


if __name__ == "__main__":
    data = load_and_format_dataset()

    # Create vector collection
    create_vector_collection(COLLECTION, len(data[0]["embeddings"]))

    # Generate payloads
    payloads = generate_payload(data)

    # Upsert each payload point
    for payload in tqdm(payloads):
        upsert_point(payload)
