# agent/llm.py
# Configures OpenRouter as the LLM backend for LangChain
# Uses OpenRouter's OpenAI-compatible API

import os
import requests
from langchain.llms.base import LLM
from typing import Optional, List
from pydantic import Field


class OpenRouterLLM(LLM):
    """
    Custom LangChain LLM that calls OpenRouter directly via requests.
    Avoids all SDK compatibility issues.
    """

    model: str = Field(default="meta-llama/llama-3-70b-instruct:nitro")
    api_key: str = Field(default="")
    temperature: float = Field(default=0.2)
    max_tokens: int = Field(default=1000)

    # FIX ADDED HERE
    openai_api_base: str = Field(
        default="https://openrouter.ai/api/v1"
    )

    @property
    def _llm_type(self) -> str:
        return "openrouter"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> str:

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/agentic-devops",
            "X-Title": "Agentic AI DevOps Assistant",
        }

        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if stop:
            body["stop"] = stop

        resp = requests.post(
            f"{self.openai_api_base}/chat/completions",
            headers=headers,
            json=body,
            timeout=60,
        )

        resp.raise_for_status()

        return resp.json()["choices"][0]["message"]["content"]

    @property
    def _identifying_params(self):
        return {"model": self.model}


def get_llm():
    """Returns OpenRouter LLM configured for LangChain"""

    return OpenRouterLLM(
        model=os.getenv(
            "OPENROUTER_MODEL",
            "meta-llama/llama-3-70b-instruct:nitro"
        ),
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        temperature=0.2,
        max_tokens=1000,
    )