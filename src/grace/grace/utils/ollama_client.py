"""
grace_agi/utils/ollama_client.py
Thin async-friendly wrapper around the Ollama / NVIDIA Nemotron API.
Falls back to rule-based responses if the endpoint is unreachable.
"""
import os
import json
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Wraps the Ollama REST API (or NVIDIA cloud compatible endpoint).

    Usage
    -----
    client = OllamaClient(host="http://localhost:11434",
                          model="nemotron")
    reply = client.chat("What do you see?", system="You are GRACE.")
    """

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "nemotron",
        api_key: Optional[str] = None,
        timeout: float = 60.0,
        max_tokens: int = 512,
        temperature: float = 1.25,
    ):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature

        self._headers = {"Content-Type": "application/json"}
        self._nvidia_mode = False   # always use native Ollama API

    # ── Public API ────────────────────────────────────────────────────────────

    def chat(
        self,
        user_message: str,
        system: str = "You are GRACE, a thoughtful robot.",
        history: Optional[list] = None,
    ) -> str:
        """Send a chat message and return the assistant reply as a string."""
        messages = [{"role": "system", "content": system}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        try:
            if self._nvidia_mode:
                return self._nvidia_chat(messages)
            else:
                return self._ollama_chat(messages)
        except Exception as exc:
            logger.warning(f"OllamaClient: LLM call failed ({exc}), using fallback.")
            return self._fallback(user_message)

    def embed(self, text: str) -> list[float]:
        """Return an embedding vector for the given text (local Ollama only)."""
        if self._nvidia_mode:
            logger.warning("Embeddings not supported in NVIDIA cloud mode; returning zeros.")
            return [0.0] * 768
        try:
            url = f"{self.host}/api/embeddings"
            payload = {"model": self.model, "prompt": text}
            resp = requests.post(url, json=payload, headers=self._headers, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("embedding", [])
        except Exception as exc:
            logger.warning(f"OllamaClient.embed failed: {exc}")
            return [0.0] * 768

    # ── Internal ──────────────────────────────────────────────────────────────

    def _ollama_chat(self, messages: list) -> str:
        url = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {
                "temperature": self.temperature,
                "min_p": 0.2,
                "num_predict": self.max_tokens,
            },
        }
        resp = requests.post(url, json=payload,
                            headers=self._headers, timeout=self.timeout)
        resp.raise_for_status()

        data = resp.json()

        # Get content, ignore thinking field entirely
        content = data["message"]["content"].strip()

        # Strip <think>...</think> blocks if they leaked into content
        import re
        content = re.sub(r"<think>.*?</think>", "", content,
                        flags=re.DOTALL).strip()

        # Strip markdown code fences
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines).strip()

        # If model wrapped JSON in explanation text, extract just the JSON
        # Find first { or [ and last } or ]
        json_start = -1
        json_end   = -1
        for i, ch in enumerate(content):
            if ch in "{[" and json_start == -1:
                json_start = i
            if ch in "}]":
                json_end = i

        if json_start != -1 and json_end != -1 and json_end > json_start:
            content = content[json_start:json_end + 1]

        return content

    def _nvidia_chat(self, messages: list) -> str:
        url = f"{self.host}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False,
        }
        resp = requests.post(url, json=payload, headers=self._headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    @staticmethod
    def _fallback(user_message: str) -> str:
        return f"[GRACE offline] Cannot process: '{user_message[:60]}'"
