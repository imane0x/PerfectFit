# src/query_engine.py

from llama_index.core.prompts import PromptTemplate
from src.llm_model import initialize_llm,initialize_mmllm
from src.multi_modal_index import create_multi_modal_index
from src.embeddings import initialize_text_embedding
from src.vector_store import initialize_vector_store
from llama_index.core import Settings
from llama_index.core import StorageContext, load_index_from_storage


qa_tmpl_str = (
    "Below is the context information:\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "You are PerfectFit, a customer assistant. Please respond to the query in a helpful, concise and friendly manner, using only the relevant information from the context provided. "
    "Do not mention or allude to the source of the information in your response, and avoid any references to images, visuals, or external materials, or the context.\n"
    "Query: {query_str}\n"
    "Answer: "
)
def get_query_engine():
    qa_tmpl = PromptTemplate(qa_tmpl_str)
    Settings.llm = initialize_llm()
    Settings.embed_model = initialize_text_embedding()
    # text_store,image_store = initialize_vector_store()
    # storage_context = StorageContext.from_defaults(
    # vector_store=text_store, persist_dir="./src/storage")
    index = create_multi_modal_index()
    # index = load_index_from_storage(storage_context, image_store=image_store)
    query_engine = index.as_query_engine(llm=initialize_mmllm(), text_qa_template=qa_tmpl)
    return query_engine