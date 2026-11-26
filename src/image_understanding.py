"""Caption a user-uploaded image so it can be combined with the text query."""
import logging

from llama_index.core.llms import ChatMessage, ImageBlock, TextBlock

from src.config import GEMINI_MODEL, GOOGLE_API_KEY

logger = logging.getLogger(__name__)

CAPTION_PROMPT = (
    "Describe this product concisely for a shop search: type of item, colour, material, "
    "pattern and style. Answer in at most 77 characters."
)


def _caption_with_gemini(image_bytes: bytes, mime_type: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GOOGLE_API_KEY)
    result = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime_type), CAPTION_PROMPT],
    )
    return (result.text or "").strip()


def _caption_with_ollama(image_bytes: bytes, mime_type: str) -> str:
    from src.llm_model import initialize_mmllm

    message = ChatMessage(
        role="user",
        blocks=[ImageBlock(image=image_bytes, image_mimetype=mime_type), TextBlock(text=CAPTION_PROMPT)],
    )
    return (initialize_mmllm().chat([message]).message.content or "").strip()


def generate_caption_image(image_bytes: bytes, mime_type: str) -> str:
    """Return a short caption. Uses Gemini if GOOGLE_API_KEY is set, otherwise the local Ollama VLM."""
    if GOOGLE_API_KEY:
        logger.info("Captioning uploaded image with Gemini (%s)", GEMINI_MODEL)
        return _caption_with_gemini(image_bytes, mime_type)
    logger.info("Captioning uploaded image with local Ollama VLM")
    return _caption_with_ollama(image_bytes, mime_type)
