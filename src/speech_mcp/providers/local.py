import logging

import anyio
import requests

logger = logging.getLogger(__name__)


class LocalLLMProvider:
    """
    SOTA Provider for local LLM orchestration.
    Handles dynamic model elicitation from Ollama and LM Studio.
    """

    async def list_models(self, provider: str, base_url: str) -> list[str]:
        """
        Asynchronously fetches available models from the local provider.
        Priority: Ollama. Default fallback provided if offline.
        """
        try:
            return await anyio.to_thread.run_sync(self._fetch, provider, base_url)
        except Exception as e:
            logger.debug(f"Local provider {provider} unreachable at {base_url}: {e}")
            return []

    def _fetch(self, provider: str, base_url: str) -> list[str]:
        """Synchronous fetch logic executed in a thread pool."""
        if provider == "ollama":
            # Ollama API: GET /api/tags
            url = f"{base_url.rstrip('/')}/api/tags"
            resp = requests.get(url, timeout=1.5)
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]

        elif provider == "lmstudio":
            # LM Studio / OpenAI-Compatible API: GET /v1/models
            url = f"{base_url.rstrip('/')}/v1/models"
            resp = requests.get(url, timeout=1.5)
            resp.raise_for_status()
            data = resp.json()
            return [m["id"] for m in data.get("data", [])]

        return []

    async def generate(self, provider: str, base_url: str, model: str, prompt: str, system: str = "") -> str:
        """
        Asynchronously generates a response from the local LLM.
        Grounded context should be injected into the prompt before calling this.
        """
        try:
            return await anyio.to_thread.run_sync(self._generate_sync, provider, base_url, model, prompt, system)
        except Exception as e:
            logger.error(f"Local generation failed ({provider}): {e}")
            return f"Generation failed: {e}"

    def _generate_sync(self, provider: str, base_url: str, model: str, prompt: str, system: str) -> str:
        """Synchronous generation logic executed in a thread pool."""
        if provider == "ollama":
            # Ollama API: POST /api/generate
            url = f"{base_url.rstrip('/')}/api/generate"
            payload = {"model": model, "prompt": prompt, "system": system, "stream": False}
            resp = requests.post(url, json=payload, timeout=30.0)
            resp.raise_for_status()
            return resp.json().get("response", "")

        elif provider == "lmstudio":
            # LM Studio / OpenAI-Compatible API: POST /v1/chat/completions
            url = f"{base_url.rstrip('/')}/v1/chat/completions"
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            payload = {"model": model, "messages": messages, "temperature": 0.7, "stream": False}
            resp = requests.post(url, json=payload, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

        return "Unsupported provider for generation."


local_llm_provider = LocalLLMProvider()
