# agent/llm.py
# Configures OpenRouter as the LLM backend for LangChain
# OpenRouter uses the OpenAI-compatible API format

import os
from langchain_community.chat_models import ChatOpenAI


def get_llm():
    """
    Returns a LangChain LLM configured to use OpenRouter.
    OpenRouter is OpenAI-API compatible — just different base_url and key.
    """
    return ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3-70b-instruct:nitro"),
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.2,
        max_tokens=1000,
        model_kwargs={
            "headers": {
                "HTTP-Referer": "https://github.com/agentic-devops",
                "X-Title": "Agentic AI DevOps Assistant",
            }
        },
    )
