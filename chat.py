import logging
from typing import Optional, Tuple

from src.config import MATCH_THRESHOLD

logger = logging.getLogger(__name__)


def best_image_path(response) -> Optional[str]:
    """Return the top product image path if the text match is confident enough, else None."""
    text_nodes = response.metadata.get("text_nodes") or []
    image_nodes = response.metadata.get("image_nodes") or []
    if not text_nodes or not image_nodes:
        return None
    top_score = text_nodes[0].score or 0.0
    logger.info("Top text match score: %.3f (threshold %.2f)", top_score, MATCH_THRESHOLD)
    if top_score < MATCH_THRESHOLD:
        return None
    return image_nodes[0].metadata.get("file_path")


def get_response(msg: str) -> Tuple[str, Optional[str]]:
    """Answer a shopping query. Returns (answer text, path of the best matching product image or None)."""
    from src.query_engine import get_query_engine

    response = get_query_engine().query(msg)
    return str(response.response), best_image_path(response)


if __name__ == "__main__":
    print("Let's chat! (type 'quit' to exit)")
    while True:
        sentence = input("You: ")
        if sentence.strip().lower() == "quit":
            break
        answer, image = get_response(sentence)
        print("PerfectFit:", answer)
        if image:
            print("  image:", image)
