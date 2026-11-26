"""Product catalog: loading, validation and the facet values used for filtering."""
import json
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from src.config import CATALOG_FILE

# Attribute fields stored on every product
FACET_FIELDS = ("category", "color", "gender", "usage", "season")
# Fields the assistant may use as exact filters. Usage and season only help ranking (they are in the
# embedded text) because models tend to guess them when the shopper never asked.
FILTER_FIELDS = ("category", "color", "gender")


@dataclass
class Product:
    id: str
    title: str
    image: str  # path relative to the catalog folder
    description: str = ""
    category: Optional[str] = None
    color: Optional[str] = None
    gender: Optional[str] = None
    usage: Optional[str] = None
    season: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    sizes: List[str] = field(default_factory=list)
    url: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> "Product":
        known = {k: d[k] for k in cls.__dataclass_fields__ if k in d}
        if not known.get("id") or not known.get("title") or not known.get("image"):
            raise ValueError(f"Product needs id, title and image: {d}")
        known["id"] = str(known["id"])
        if known.get("price") is not None:
            known["price"] = float(known["price"])
        return cls(**known)

    def to_dict(self) -> dict:
        return asdict(self)

    def search_text(self) -> str:
        """Text that is embedded and keyword-indexed for this product."""
        attrs = [self.category, self.color, self.gender, self.usage, self.season]
        parts = [self.title, self.description, " ".join(a for a in attrs if a)]
        return ". ".join(p for p in parts if p)

    def summary(self) -> str:
        """Compact description given to the language model."""
        bits = [f"id={self.id}", self.title]
        for name in FACET_FIELDS:
            value = getattr(self, name)
            if value:
                bits.append(f"{name}={value}")
        if self.price is not None:
            bits.append(f"price={self.price:g} {self.currency or ''}".strip())
        if self.sizes:
            bits.append("sizes=" + "/".join(self.sizes))
        if self.description:
            bits.append(self.description[:200])
        return " | ".join(bits)


class Catalog:
    def __init__(self, products: List[Product], root: Path):
        self.root = root.resolve()
        self.products: Dict[str, Product] = {p.id: p for p in products}

    @classmethod
    def load(cls, path: str = CATALOG_FILE) -> "Catalog":
        file = Path(path)
        if not file.exists():
            raise FileNotFoundError(
                f"Catalog not found at {file}. Run `python scripts/download_sample.py` or set PERFECTFIT_CATALOG."
            )
        products = []
        with file.open(encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                if line.strip():
                    try:
                        products.append(Product.from_dict(json.loads(line)))
                    except (ValueError, TypeError) as e:
                        raise ValueError(f"{file}:{line_no}: {e}") from e
        return cls(products, file.parent)

    def get(self, product_id: str) -> Optional[Product]:
        return self.products.get(str(product_id))

    def image_path(self, product: Product) -> Optional[Path]:
        """Absolute image path, only if it stays inside the catalog folder."""
        path = (self.root / product.image).resolve()
        return path if path.is_relative_to(self.root) and path.is_file() else None

    def facets(self) -> Dict[str, List[str]]:
        """Distinct values of each filterable field."""
        values: Dict[str, set] = {name: set() for name in FILTER_FIELDS}
        for p in self.products.values():
            for name in FILTER_FIELDS:
                v = getattr(p, name)
                if v:
                    values[name].add(v)
        return {name: sorted(v) for name, v in values.items() if v}

    def has_prices(self) -> bool:
        return any(p.price is not None for p in self.products.values())


@lru_cache(maxsize=1)
def get_catalog() -> Catalog:
    return Catalog.load()
