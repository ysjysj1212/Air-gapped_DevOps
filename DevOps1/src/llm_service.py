import logging
import os

import requests

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def ask_ollama(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """Send a prompt to Ollama and return the generated text.

    Returns the response string, or raises RuntimeError on failure.
    """
    endpoint = f"{OLLAMA_URL}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}

    try:
        response = requests.post(endpoint, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except requests.exceptions.ConnectionError as exc:
        logger.error("Cannot connect to Ollama at %s: %s", OLLAMA_URL, exc)
        raise RuntimeError(f"Ollama is not available at {OLLAMA_URL}") from exc
    except requests.exceptions.Timeout as exc:
        logger.error("Ollama request timed out: %s", exc)
        raise RuntimeError("Ollama request timed out") from exc
    except requests.exceptions.RequestException as exc:
        logger.error("Ollama request failed: %s", exc)
        raise RuntimeError(f"Ollama request failed: {exc}") from exc
