from llama_index.embeddings.clip import ClipEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from src.config import TEXT_EMBED_MODEL


def initialize_text_embedding():
    return HuggingFaceEmbedding(model_name=TEXT_EMBED_MODEL)


def initialize_image_embedding():
    return ClipEmbedding()
