# src/embeddings.py
from llama_index.embeddings.clip import ClipEmbedding
from src.config import EMBED_MODEL_NAME
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
def initialize_text_embedding():
    return HuggingFaceEmbedding(
        model_name="BAAI/bge-large-en-v1.5")

def initialize_image_embedding():
    return ClipEmbedding()