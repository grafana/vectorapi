import requests
import hashlib
from datasets import load_dataset
from typing import Dict, List
from tqdm import tqdm


COLLECTION = "test1.promql.templates"
VECTORAPI = "http://localhost:8889/v1"


def create_vector_collection(name: str, dimension: int) -> Dict:
    payload = {"collection_name": name, "dimension": dimension, "exist_ok": True}
    response = requests.post(
        f"{VECTORAPI}/collections/create", headers={}, json=payload, timeout=10
    )
    response.raise_for_status()
    return response.json()


def upsert_point(payload: Dict) -> None:
    url = f"{VECTORAPI}/collections/{COLLECTION}/upsert"
    response = requests.post(url, headers={}, json=payload, timeout=10)
    response.raise_for_status()


def load_and_format_dataset() -> List[Dict]:
    # Load dataset from HuggingFace
    dataset = load_dataset(
        "grafanalabs/promql-templates",
    )
    return dataset["train"]


def generate_payload(data: List[Dict]) -> List[Dict]:
    return [
        {
            "id": hashlib.sha256(row["promql"].encode("utf-8")).hexdigest(),
            "embedding": row["embedding"],
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
    create_vector_collection(COLLECTION, len(data[0]["embedding"]))

    # Generate payloads
    payloads = generate_payload(data)

    # Upsert each payload point
    for payload in tqdm(payloads):
        upsert_point(payload)
