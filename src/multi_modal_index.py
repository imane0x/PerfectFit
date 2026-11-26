from llama_index.core import Settings, SimpleDirectoryReader, StorageContext
from llama_index.core.indices.multi_modal.base import MultiModalVectorStoreIndex

from src.config import CHUNK_SIZE, DATA_PATH
from src.embeddings import initialize_image_embedding, initialize_text_embedding
from src.vector_store import index_exists, initialize_vector_store


def _configure_settings():
    Settings.chunk_size = CHUNK_SIZE
    Settings.embed_model = initialize_text_embedding()


def build_index(data_path: str = DATA_PATH) -> MultiModalVectorStoreIndex:
    """Embed the catalog and write it to Qdrant. Run once through ingest.py, not per request."""
    _configure_settings()
    text_store, image_store = initialize_vector_store()
    storage_context = StorageContext.from_defaults(vector_store=text_store, image_store=image_store)
    documents = SimpleDirectoryReader(data_path, recursive=True).load_data()
    return MultiModalVectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        image_embed_model=initialize_image_embedding(),
        show_progress=True,
    )


def load_index() -> MultiModalVectorStoreIndex:
    """Load the existing index from Qdrant without re-embedding anything."""
    if not index_exists():
        raise RuntimeError("No product index found. Run `python ingest.py` first.")
    _configure_settings()
    text_store, image_store = initialize_vector_store()
    return MultiModalVectorStoreIndex.from_vector_store(
        vector_store=text_store,
        image_vector_store=image_store,
        image_embed_model=initialize_image_embedding(),
    )
