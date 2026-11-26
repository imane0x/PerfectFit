from llama_index.llms.ollama import Ollama

from src.config import OLLAMA_BASE_URL, OLLAMA_TIMEOUT, VLM_MODEL


def initialize_mmllm():
    """Vision-language model served by Ollama. It answers queries and can see the retrieved product images."""
    return Ollama(
        model=VLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        request_timeout=OLLAMA_TIMEOUT,
        temperature=0.25,
    )
