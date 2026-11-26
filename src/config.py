"""Central configuration. Every value can be overridden with an env var or a .env file."""
import os

from dotenv import load_dotenv

load_dotenv()

# Catalog: one JSON object per line, image paths relative to the file's folder (see README)
CATALOG_FILE = os.getenv("PERFECTFIT_CATALOG", "data/catalog/products.jsonl")
QDRANT_PATH = os.getenv("PERFECTFIT_QDRANT_PATH", "qdrant_db")
COLLECTION = "products"

# Embedding models (ONNX via FastEmbed, run on CPU, no torch needed)
TEXT_EMBED_MODEL = os.getenv("PERFECTFIT_TEXT_EMBED_MODEL", "BAAI/bge-base-en-v1.5")
IMAGE_EMBED_MODEL = os.getenv("PERFECTFIT_IMAGE_EMBED_MODEL", "google/siglip2-base-patch16-224")
SPARSE_EMBED_MODEL = "Qdrant/bm25"

# One vision-language model does query understanding, image understanding and answering
VLM_MODEL = os.getenv("PERFECTFIT_VLM_MODEL", "qwen3-vl:4b-instruct")  # any non-thinking Ollama vision model
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))
MAX_OUTPUT_TOKENS = 400  # hard cap so a looping model cannot hang a request

# Retrieval
CANDIDATES_PER_SIGNAL = 30  # results from each of dense / sparse / image search before fusion
# Cosine similarity (bge) needed to map the shopper's item type to a catalog category. Calibrated on the
# sample catalog: "tee" -> Tshirts 0.77, "sofa" -> Shirts 0.68 (rejected).
CATEGORY_MATCH_THRESHOLD = float(os.getenv("PERFECTFIT_CATEGORY_MATCH_THRESHOLD", "0.76"))
RESULTS_FOR_LLM = int(os.getenv("PERFECTFIT_RESULTS_FOR_LLM", "8"))
MAX_PRODUCTS_SHOWN = int(os.getenv("PERFECTFIT_MAX_PRODUCTS_SHOWN", "4"))

# Uploads
MAX_UPLOAD_BYTES = int(os.getenv("PERFECTFIT_MAX_UPLOAD_MB", "8")) * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
