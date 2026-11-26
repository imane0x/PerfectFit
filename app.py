import base64
import binascii
import logging
import mimetypes
import os

from flask import Flask, jsonify, render_template, request

from src.config import ALLOWED_IMAGE_TYPES, MAX_UPLOAD_BYTES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("perfectfit")

app = Flask(__name__)
# Base64 makes uploads ~33% larger than the raw image, plus JSON overhead.
app.config["MAX_CONTENT_LENGTH"] = int(MAX_UPLOAD_BYTES * 1.4) + 64 * 1024


def get_response(text):
    from chat import get_response as _get_response

    return _get_response(text)


def generate_caption_image(image_bytes, mime_type):
    from src.image_understanding import generate_caption_image as _caption

    return _caption(image_bytes, mime_type)


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


def encode_image(path):
    mime_type, _ = mimetypes.guess_type(path)
    with open(path, "rb") as f:
        return {"data": base64.b64encode(f.read()).decode("ascii"), "mime_type": mime_type or "image/jpeg"}


@app.get("/")
def index_get():
    return render_template("base.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/predict")
def predict():
    try:
        text, image_bytes, mime_type = parse_request(request.get_json(silent=True))
    except ValueError as e:
        return jsonify({"answer": str(e)}), 400

    try:
        if image_bytes is not None:
            caption = generate_caption_image(image_bytes, mime_type)
            logger.info("Image caption: %s", caption)
            text = f"{text} Here is how it looks: {caption}".strip()

        if not text.strip():
            return jsonify({"answer": "No valid text or image data found"}), 400

        answer, image_path = get_response(text)
        file_info = encode_image(image_path) if image_path else None
        return jsonify({"answer": answer, "file": file_info})
    except Exception:
        logger.exception("Error during prediction")
        return jsonify({"answer": "An error occurred while processing your request"}), 500


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
