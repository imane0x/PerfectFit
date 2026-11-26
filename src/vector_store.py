from functools import lru_cache

import qdrant_client
from llama_index.vector_stores.qdrant import QdrantVectorStore

from src.config import IMAGE_COLLECTION, QDRANT_PATH, TEXT_COLLECTION


@lru_cache(maxsize=1)
def get_client() -> qdrant_client.QdrantClient:
    # Local (embedded) Qdrant locks its folder, so only one client per process is allowed.
    return qdrant_client.QdrantClient(path=QDRANT_PATH)


def initialize_vector_store():
    client = get_client()
    text_store = QdrantVectorStore(client=client, collection_name=TEXT_COLLECTION)
    image_store = QdrantVectorStore(client=client, collection_name=IMAGE_COLLECTION)
    return text_store, image_store


def index_exists() -> bool:
    client = get_client()
    return client.collection_exists(TEXT_COLLECTION) and client.collection_exists(IMAGE_COLLECTION)
