import base64
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as app_module  # noqa: E402
import chat  # noqa: E402

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


@pytest.fixture
def client(monkeypatch, tmp_path):
    product = tmp_path / "dress.png"
    product.write_bytes(PNG)
    calls = {}

    def fake_response(text):
        calls["text"] = text
        return "A red dress", str(product)

    def fake_caption(image_bytes, mime_type):
        calls["caption_input"] = (image_bytes, mime_type)
        return "red summer dress"

    monkeypatch.setattr(app_module, "get_response", fake_response)
    monkeypatch.setattr(app_module, "generate_caption_image", fake_caption)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        c.calls = calls
        yield c


def payload(*parts):
    return {"contents": [{"parts": list(parts)}]}


def test_text_query_returns_answer_and_image(client):
    r = client.post("/predict", json=payload({"text": "red dress"}))
    assert r.status_code == 200
    body = r.get_json()
    assert body["answer"] == "A red dress"
    assert body["file"]["mime_type"] == "image/png"
    assert base64.b64decode(body["file"]["data"]) == PNG


def test_image_query_is_captioned_in_memory(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.iterdir())
    img = {"inline_data": {"data": base64.b64encode(PNG).decode(), "mime_type": "image/png"}}
    r = client.post("/predict", json={**payload({"text": "like this"}, img), "name": "../../evil"})
    assert r.status_code == 200
    assert client.calls["caption_input"] == (PNG, "image/png")
    assert "red summer dress" in client.calls["text"]
    assert set(tmp_path.iterdir()) == before  # nothing written to disk


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"contents": []},
        payload({"inline_data": {"data": "not base64!!", "mime_type": "image/png"}}),
        payload({"inline_data": {"data": base64.b64encode(PNG).decode(), "mime_type": "text/html"}}),
        payload({"text": "   "}),
    ],
)
def test_bad_requests_are_rejected(client, body):
    assert client.post("/predict", json=body).status_code == 400


def test_non_json_body(client):
    assert client.post("/predict", data="x", content_type="text/plain").status_code == 400


def node(score=None, path=None):
    return SimpleNamespace(score=score, metadata={"file_path": path})


def test_best_image_path():
    resp = lambda t, i: SimpleNamespace(metadata={"text_nodes": t, "image_nodes": i})  # noqa: E731
    assert chat.best_image_path(resp([node(0.9)], [node(path="a.jpg")])) == "a.jpg"
    assert chat.best_image_path(resp([node(0.1)], [node(path="a.jpg")])) is None
    assert chat.best_image_path(resp([node(0.9)], [])) is None  # used to raise IndexError
    assert chat.best_image_path(resp([], [node(path="a.jpg")])) is None
