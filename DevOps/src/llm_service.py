"""Ollama integration helpers."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests


DEFAULT_OLLAMA_URL = "http://localhost:11434"


class OllamaService:
    """Small wrapper around the Ollama HTTP API."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        self.base_url = (base_url or os.getenv("OLLAMA_URL") or DEFAULT_OLLAMA_URL).rstrip("/")
        self.api_endpoint = f"{self.base_url}/api"
        self.timeout = timeout

    def is_healthy(self) -> bool:
        """Return whether the Ollama HTTP API is reachable."""
        try:
            response = requests.get(f"{self.api_endpoint}/tags", timeout=self.timeout)
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False

    def list_models(self) -> List[str]:
        """List model names exposed by Ollama."""
        try:
            response = requests.get(f"{self.api_endpoint}/tags", timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            return [item.get("name", "") for item in payload.get("models", []) if item.get("name")]
        except (requests.RequestException, ValueError):
            return []

    def get_available_models(self) -> List[str]:
        """Compatibility wrapper used by tests."""
        return self.list_models()

    def ask(self, prompt: str, model: str = "llama2") -> str:
        """Ask Ollama and return the generated text."""
        response = self.ask_ollama(prompt, model=model)
        if response is None:
            raise RuntimeError("Ollama is unavailable or returned an invalid response")
        return response

    def ask_ollama(self, prompt: str, model: str = "llama2") -> Optional[str]:
        """Ask Ollama and return None on failures."""
        try:
            response = requests.post(
                f"{self.api_endpoint}/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload: Dict[str, Any] = response.json()
            return payload.get("response")
        except (requests.RequestException, ValueError):
            return None

    def generate_pipeline_description(self, requirements: str, model: str = "llama2") -> Optional[str]:
        """Generate a short pipeline summary from plain-text requirements."""
        prompt = (
            "Summarize the CI/CD pipeline requirements below as build, test, and deploy steps.\n\n"
            f"Requirements:\n{requirements}"
        )
        return self.ask_ollama(prompt, model=model)


def is_ollama_available(base_url: Optional[str] = None) -> bool:
    """Convenience helper used by tests and endpoints."""
    return OllamaService(base_url=base_url).is_healthy()
