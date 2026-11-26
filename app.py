import base64
import binascii
import logging
import os

from flask import Flask, abort, jsonify, render_template, request, send_file

from src.config import ALLOWED_IMAGE_TYPES, MAX_UPLOAD_BYTES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("perfectfit")

app = Flask(__name__)
# Base64 makes uploads ~33% larger than the raw image, plus JSON overhead.
app.config["MAX_CONTENT_LENGTH"] = int(MAX_UPLOAD_BYTES * 1.4) + 64 * 1024


def get_assistant():
    from src.assistant import get_assistant as _get

    return _get()


def parse_request(data):
    """Extract (text, image_bytes, mime_type) from the Gemini-style payload the frontend sends."""
    contents = data.get("contents") if isinstance(data, dict) else None
    if not contents or not isinstance(contents, list):
        raise ValueError("No contents provided")
    text, image_bytes, mime_type = "", None, None
    for part in contents[0].get("parts", []):
        if part.get("text"):
            text = str(part["text"])
        elif isinstance(part.get("inline_data"), dict):
            mime_type = part["inline_data"].get("mime_type")
            if mime_type not in ALLOWED_IMAGE_TYPES:
                raise ValueError("Unsupported image type. Use JPEG, PNG or WebP.")
            try:
                image_bytes = base64.b64decode(part["inline_data"].get("data") or "", validate=True)
            except (binascii.Error, ValueError):
                raise ValueError("Image data is not valid base64")
            if not image_bytes:
                raise ValueError("Image is empty")
            if len(image_bytes) > MAX_UPLOAD_BYTES:
                raise ValueError("Image is too large")
    return text, image_bytes, mime_type


def product_card(p):
    return {
        "id": p.id,
        "title": p.title,
        "price": p.price,
        "currency": p.currency,
        "color": p.color,
        "category": p.category,
        "url": p.url,
        "image_url": f"/products/{p.id}/image",
    }


@app.get("/")
def index_get():
    return render_template("base.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/products/<product_id>/image")
def product_image(product_id):
    # Look the product up by id; the client never supplies a file path.
    catalog = get_assistant().catalog
    product = catalog.get(product_id)
    path = catalog.image_path(product) if product else None
    if path is None:
        abort(404)
    return send_file(path, max_age=86400)


@app.post("/predict")
def predict():
    try:
        text, image_bytes, _mime_type = parse_request(request.get_json(silent=True))
    except ValueError as e:
        return jsonify({"answer": str(e)}), 400
    if not text.strip() and image_bytes is None:
        return jsonify({"answer": "No valid text or image data found"}), 400

    try:
        turn = get_assistant().ask(text.strip(), image_bytes)
        return jsonify(
            {
                "answer": turn.answer,
                "exact_match": turn.exact_match,
                "products": [product_card(p) for p in turn.products],
            }
        )
    except Exception:
        logger.exception("Error during prediction")
        return jsonify({"answer": "An error occurred while processing your request"}), 500


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
