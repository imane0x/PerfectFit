import base64

import pytest

import app as app_module
from src.assistant import Turn

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


class FakeAssistant:
    def __init__(self, catalog):
        self.catalog = catalog
        self.calls = []

    def ask(self, text, image=None):
        self.calls.append((text, image))
        return Turn("A red dress", [self.catalog.get("1"), self.catalog.get("4")], True)


@pytest.fixture
def client(monkeypatch, catalog):
    fake = FakeAssistant(catalog)
    monkeypatch.setattr(app_module, "get_assistant", lambda: fake)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        c.fake = fake
        yield c


def payload(*parts):
    return {"contents": [{"parts": list(parts)}]}


def test_text_query_returns_product_cards(client):
    r = client.post("/predict", json=payload({"text": "red dress"}))
    assert r.status_code == 200
    body = r.get_json()
    assert body["answer"] == "A red dress"
    assert body["exact_match"] is True
    assert body["products"][0]["image_url"] == "/products/1/image"
    assert body["products"][1]["price"] == 39.0 and body["products"][1]["url"] == "https://example.com/4"


def test_image_query_is_passed_in_memory(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.iterdir())
    img = {"inline_data": {"data": base64.b64encode(PNG).decode(), "mime_type": "image/png"}}
    r = client.post("/predict", json={**payload(img), "name": "../../evil"})
    assert r.status_code == 200
    assert client.fake.calls == [("", PNG)]
    assert set(tmp_path.iterdir()) == before  # nothing written to disk


def test_product_image_route(client):
    r = client.get("/products/1/image")
    assert r.status_code == 200 and r.data == b"\xff\xd8fakejpeg"
    assert client.get("/products/nope/image").status_code == 404
    assert client.get("/products/..%2F..%2Fapp.py/image").status_code == 404


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


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}
