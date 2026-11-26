"""Index the product catalog into the local Qdrant database.

Usage: python ingest.py [path/to/catalog]
The folder can contain product images (.jpg/.png/...) and text files (.txt/.md/.csv/...) with descriptions.
"""
import shutil
import sys

from src.config import DATA_PATH, QDRANT_PATH


def main():
    data_path = sys.argv[1] if len(sys.argv) > 1 else DATA_PATH
    # Rebuild from scratch so re-running never duplicates products.
    shutil.rmtree(QDRANT_PATH, ignore_errors=True)
    from src.multi_modal_index import build_index

    build_index(data_path)
    print(f"Indexed catalog from {data_path} into {QDRANT_PATH}")


if __name__ == "__main__":
    main()
