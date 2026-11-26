"""Thin wrapper around the Ollama vision-language model with JSON-schema structured output."""
import json
import logging
from functools import lru_cache
from typing import List, Optional

from src.config import MAX_OUTPUT_TOKENS, OLLAMA_BASE_URL, OLLAMA_TIMEOUT, VLM_MODEL

logger = logging.getLogger(__name__)


class VLM:
    def __init__(self, model: str = VLM_MODEL):
        import ollama

        self.model = model
        self.client = ollama.Client(host=OLLAMA_BASE_URL, timeout=OLLAMA_TIMEOUT)

    def json(self, system: str, user: str, schema: dict, images: Optional[List[bytes]] = None) -> dict:
        message = {"role": "user", "content": user}
        if images:
            message["images"] = images
        response = self.client.chat(
            model=self.model,
            messages=[{"role": "system", "content": system}, message],
            format=schema,
            options={"temperature": 0, "num_predict": MAX_OUTPUT_TOKENS},
            keep_alive="30m",
        )
        content = response.message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Model returned invalid JSON: %r", content[:500])
            return {}


@lru_cache(maxsize=1)
def get_vlm() -> VLM:
    return VLM()
