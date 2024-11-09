# src/vector_store.py

import qdrant_client
from llama_index.vector_stores.qdrant import QdrantVectorStore

def initialize_vector_store():
    client = qdrant_client.QdrantClient(path="qdrant_mm_db")
    text_store = QdrantVectorStore(client=client, collection_name="text_collection")
    image_store = QdrantVectorStore(client=client, collection_name="image_collection")
    return text_store, image_store