"""Central configuration. Every value can be overridden with an env var or a .env file."""
import os

from dotenv import load_dotenv

load_dotenv()

# Catalog folder with product images and text files (used by ingest.py)
DATA_PATH = os.getenv("PERFECTFIT_DATA_PATH", "data/catalog")
QDRANT_PATH = os.getenv("PERFECTFIT_QDRANT_PATH", "qdrant_mm_db")
TEXT_COLLECTION = "text_collection"
IMAGE_COLLECTION = "image_collection"

# Models
TEXT_EMBED_MODEL = os.getenv("PERFECTFIT_TEXT_EMBED_MODEL", "BAAI/bge-large-en-v1.5")
VLM_MODEL = os.getenv("PERFECTFIT_VLM_MODEL", "llava")  # any Ollama vision model
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "180"))

# Optional: Gemini captions for uploaded images. Without a key, the Ollama VLM captions instead.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("PERFECTFIT_GEMINI_MODEL", "gemini-2.5-flash")

# Retrieval
CHUNK_SIZE = 512
TEXT_TOP_K = int(os.getenv("PERFECTFIT_TEXT_TOP_K", "3"))
IMAGE_TOP_K = int(os.getenv("PERFECTFIT_IMAGE_TOP_K", "1"))
# Minimum text-match score before we show a product image
MATCH_THRESHOLD = float(os.getenv("PERFECTFIT_MATCH_THRESHOLD", "0.55"))

# Uploads
MAX_UPLOAD_BYTES = int(os.getenv("PERFECTFIT_MAX_UPLOAD_MB", "8")) * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
