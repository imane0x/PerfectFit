from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.core import PromptTemplate
from src.config import LLM_MODEL_NAME, TOKENIZER_NAME,MM_LLM
from llama_index.multi_modal_llms.ollama import OllamaMultiModal
def initialize_llm():
    query_wrapper_prompt = PromptTemplate(
        "Below is an instruction that describes a task. "
        "Write a response that appropriately completes the request.\n\n"
        "### Instruction:\n{query_str}\n\n### Response:"
    )
    return HuggingFaceLLM(
        model_name=LLM_MODEL_NAME,
        tokenizer_name=TOKENIZER_NAME,
        query_wrapper_prompt=query_wrapper_prompt,
        device_map="auto",
        context_window=2048,
        max_new_tokens=256,
        generate_kwargs={"temperature": 0.25, "do_sample": False},
    )
def initialize_mmllm():
    return  OllamaMultiModal(model=MM_LLM)