from functools import lru_cache

from llama_index.core.prompts import PromptTemplate

from src.config import IMAGE_TOP_K, TEXT_TOP_K
from src.llm_model import initialize_mmllm
from src.multi_modal_index import load_index

QA_TEMPLATE = PromptTemplate(
    "Below is the context information:\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "You are PerfectFit, a shopping assistant. Respond to the query in a helpful, concise and friendly "
    "manner, using only the relevant information from the context provided. If no product in the context "
    "matches the request, say so honestly and suggest the closest alternative.\n"
    "Do not mention the source of the information, the context, or any images.\n"
    "Query: {query_str}\n"
    "Answer: "
)


@lru_cache(maxsize=1)
def get_query_engine():
    """Build the query engine once per process. Models and index are loaded a single time."""
    index = load_index()
    return index.as_query_engine(
        llm=initialize_mmllm(),
        text_qa_template=QA_TEMPLATE,
        similarity_top_k=TEXT_TOP_K,
        image_similarity_top_k=IMAGE_TOP_K,
    )
