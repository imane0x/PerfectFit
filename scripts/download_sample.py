"""Download a sample catalog from the public "Fashion Product Images (Small)" dataset on Hugging Face.

Usage: python scripts/download_sample.py [--count 400] [--out data/catalog]
Writes products.jsonl plus images/. The dataset has no prices or sizes, so those fields stay empty.
"""
import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

DATASET = "ashraq/fashion-product-images-small"
ROWS_API = "https://datasets-server.huggingface.co/rows"
DATASET_SIZE = 44000  # approximate; used to spread pages across the dataset
PAGE = 100  # maximum rows per API call


def fetch(url: str, retries: int = 3) -> bytes:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "perfectfit-sample-downloader"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=400)
    ap.add_argument("--out", default="data/catalog")
    args = ap.parse_args()

    out = Path(args.out)
    (out / "images").mkdir(parents=True, exist_ok=True)
    pages = max(1, -(-args.count // PAGE))
    step = DATASET_SIZE // pages
    written = 0
    with (out / "products.jsonl").open("w", encoding="utf-8") as f:
        for page in range(pages):
            query = urllib.parse.urlencode(
                {"dataset": DATASET, "config": "default", "split": "train", "offset": page * step, "length": PAGE}
            )
            rows = json.loads(fetch(f"{ROWS_API}?{query}"))["rows"]
            for item in rows:
                if written >= args.count:
                    break
                r = item["row"]
                pid = int(r["id"])
                image_file = out / "images" / f"{pid}.jpg"
                try:
                    if not image_file.exists():
                        image_file.write_bytes(fetch(r["image"]["src"]))
                except Exception as e:
                    print(f"skip {pid}: {e}", file=sys.stderr)
                    continue
                product = {
                    "id": str(pid),
                    "title": r["productDisplayName"],
                    "image": f"images/{pid}.jpg",
                    "category": r["articleType"],
                    "color": r["baseColour"],
                    "gender": r["gender"],
                    "usage": r["usage"],
                    "season": r["season"],
                }
                f.write(json.dumps({k: v for k, v in product.items() if v}) + "\n")
                written += 1
            print(f"{written}/{args.count}", flush=True)
    print(f"Wrote {written} products to {out / 'products.jsonl'}")


if __name__ == "__main__":
    main()
