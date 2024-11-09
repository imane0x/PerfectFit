# src/multi_modal_index.py

from llama_index.core.indices.multi_modal.base import MultiModalVectorStoreIndex
from src.vector_store import initialize_vector_store
from src.embeddings import initialize_image_embedding
from llama_index.core import  StorageContext, SimpleDirectoryReader

from src.config import PATH
def create_multi_modal_index():
    text_store, image_store = initialize_vector_store()
    storage_context = StorageContext.from_defaults(vector_store=text_store, image_store=image_store)
    documents = SimpleDirectoryReader(PATH).load_data()
    image_embed_model = initialize_image_embedding()
    return MultiModalVectorStoreIndex.from_documents(documents, storage_context=storage_context, image_embed_model=image_embed_model)