"""Index the product catalog into the local Qdrant database.

Usage: python ingest.py [path/to/products.jsonl]
Re-running rebuilds the collection, so products are never duplicated.
"""
import sys

from src.catalog import Catalog
from src.config import CATALOG_FILE, QDRANT_PATH


def main():
    catalog = Catalog.load(sys.argv[1] if len(sys.argv) > 1 else CATALOG_FILE)
    products, images = [], []
    for p in catalog.products.values():
        path = catalog.image_path(p)
        if path is None:
            print(f"skipping {p.id}: image {p.image!r} not found inside {catalog.root}")
            continue
        products.append(p)
        images.append(str(path))
    if not products:
        sys.exit("No products with images to index.")

    from src.embeddings import get_embedders
    from src.search import get_client, index_products

    print(f"Embedding {len(products)} products (the first run downloads the models)...")
    index_products(
        get_client(), get_embedders(), products, images,
        progress=lambda done, total: print(f"  {done}/{total}", flush=True),
    )
    print(f"Indexed {len(products)} products into {QDRANT_PATH}")


if __name__ == "__main__":
    main()
