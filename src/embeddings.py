"""Embedding models. Real ones use FastEmbed (ONNX); tests swap in a stub with the same methods."""
import io
from functools import lru_cache
from typing import List, Sequence, Union

from qdrant_client import models

from src.config import IMAGE_EMBED_MODEL, SPARSE_EMBED_MODEL, TEXT_EMBED_MODEL

ImageInput = Union[str, bytes]


class Embedders:
    def __init__(self):
        from fastembed import ImageEmbedding, SparseTextEmbedding, TextEmbedding

        self._text = TextEmbedding(TEXT_EMBED_MODEL)
        self._sparse = SparseTextEmbedding(SPARSE_EMBED_MODEL)
        self._image = ImageEmbedding(IMAGE_EMBED_MODEL)
        self._image_text = TextEmbedding(IMAGE_EMBED_MODEL)  # text tower of the same model, for text -> image search

    @property
    def text_dim(self) -> int:
        return len(self.text(["x"])[0])

    @property
    def image_dim(self) -> int:
        return len(self.image_text(["x"])[0])

    def text(self, texts: Sequence[str]) -> List[List[float]]:
        return [v.tolist() for v in self._text.embed(list(texts))]

    def text_query(self, query: str) -> List[float]:
        return next(iter(self._text.query_embed(query))).tolist()

    def sparse(self, texts: Sequence[str]) -> List[models.SparseVector]:
        return [models.SparseVector(indices=v.indices.tolist(), values=v.values.tolist()) for v in self._sparse.embed(list(texts))]

    def sparse_query(self, query: str) -> models.SparseVector:
        v = next(iter(self._sparse.query_embed(query)))
        return models.SparseVector(indices=v.indices.tolist(), values=v.values.tolist())

    def image(self, images: Sequence[ImageInput]) -> List[List[float]]:
        from PIL import Image

        loaded = [Image.open(io.BytesIO(i)).convert("RGB") if isinstance(i, bytes) else i for i in images]
        return [v.tolist() for v in self._image.embed(loaded)]

    def image_text(self, texts: Sequence[str]) -> List[List[float]]:
        return [v.tolist() for v in self._image_text.embed([f"a photo of {t}" for t in texts])]


@lru_cache(maxsize=1)
def get_embedders() -> Embedders:
    return Embedders()
