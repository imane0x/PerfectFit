import hashlib
import math
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qdrant_client import QdrantClient, models  # noqa: E402

from src.catalog import Catalog, Product  # noqa: E402

DIM = 64


def _bucket(token: str) -> int:
    return int(hashlib.md5(token.encode()).hexdigest(), 16) % DIM


def _bow(text: str):
    v = [0.0] * DIM
    for t in re.findall(r"[a-z]+", text.lower()):
        v[_bucket(t)] += 1.0
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


class StubEmbedders:
    """Deterministic bag-of-words vectors. Images are 'embedded' from their file name / bytes content,
    so a test image whose bytes say b"red dress" is close to a product image named red_dress.jpg."""

    text_dim = DIM
    image_dim = DIM

    def text(self, texts):
        return [_bow(t) for t in texts]

    def text_query(self, q):
        return _bow(q)

    def sparse(self, texts):
        out = []
        for t in texts:
            counts = {}
            for tok in re.findall(r"[a-z]+", t.lower()):
                counts[_bucket(tok)] = counts.get(_bucket(tok), 0) + 1.0
            out.append(models.SparseVector(indices=list(counts), values=list(counts.values())))
        return out

    def sparse_query(self, q):
        return self.sparse([q])[0]

    def image(self, images):
        return [_bow(i.decode() if isinstance(i, bytes) else Path(i).stem.replace("_", " ")) for i in images]

    def image_text(self, texts):
        return [_bow(t) for t in texts]


PRODUCTS = [
    dict(id="1", title="Red Summer Dress", image="red_dress.jpg", category="Dresses", color="Red", gender="Women"),
    dict(id="2", title="Blue Denim Jeans", image="blue_jeans.jpg", category="Jeans", color="Blue", gender="Men"),
    dict(id="3", title="Navy Blue Check Shirt", image="navy_check_shirt.jpg", category="Shirts", color="Navy Blue", gender="Men"),
    dict(id="4", title="White Linen Shirt", image="white_linen_shirt.jpg", category="Shirts", color="White", gender="Women",
         price=39.0, currency="EUR", sizes=["S", "M"], url="https://example.com/4"),
    dict(id="5", title="Silver Steel Watch", image="silver_watch.jpg", category="Watches", color="Silver", gender="Women",
         price=120.0, currency="EUR"),
]


@pytest.fixture
def catalog(tmp_path):
    for p in PRODUCTS:
        (tmp_path / p["image"]).write_bytes(b"\xff\xd8fakejpeg")
    return Catalog([Product.from_dict(p) for p in PRODUCTS], tmp_path)


@pytest.fixture
def embedders():
    return StubEmbedders()


@pytest.fixture
def indexed(catalog, embedders):
    from src.search import index_products

    client = QdrantClient(":memory:")
    products = list(catalog.products.values())
    index_products(client, embedders, products, [str(catalog.image_path(p)) for p in products])
    yield client
    client.close()
