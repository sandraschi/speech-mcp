import asyncio
import json
import logging

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
            return await asyncio.to_thread(lambda: self._fetch(provider, base_url))
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

    async def generate(
        self,
        provider: str,
        base_url: str,
        model: str,
        prompt: str,
        system: str = "",
        timeout: float = 30.0,
        options: dict | None = None,
    ) -> str:
        """
        Asynchronously generates a response from the local LLM.
        Grounded context should be injected into the prompt before calling this.
        """
        try:
            return await asyncio.to_thread(
                lambda: self._generate_sync(provider, base_url, model, prompt, system, timeout, options)
            )
        except Exception as e:
            logger.error(f"Local generation failed ({provider}): {e}")
            return f"Generation failed: {e}"

    def _generate_sync(
        self,
        provider: str,
        base_url: str,
        model: str,
        prompt: str,
        system: str,
        timeout: float,
        options: dict | None = None,
    ) -> str:
        """Synchronous generation logic executed in a thread pool."""
        if provider == "ollama":
            # Ollama API: POST /api/generate
            url = f"{base_url.rstrip('/')}/api/generate"
            payload: dict = {"model": model, "prompt": prompt, "system": system, "stream": False}
            if options:
                payload["options"] = options
            resp = requests.post(url, json=payload, timeout=timeout)
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
            resp = requests.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

        return "Unsupported provider for generation."

    async def generate_stream_capped(
        self,
        provider: str,
        base_url: str,
        model: str,
        prompt: str,
        system: str = "",
        max_tokens: int = 2000,
        timeout: float = 300.0,
    ) -> str:
        """Streaming Ollama generation with a hard client-side token cap.

        Reads tokens until `done` or `max_tokens`, whichever comes first, then
        disconnects. A runaway model can never hang the caller past the cap.
        Returns the accumulated text (may be truncated mid-JSON if capped).
        """
        if provider != "ollama":
            return await self.generate(provider, base_url, model, prompt, system, timeout)
        try:
            return await asyncio.to_thread(
                lambda: self._generate_stream_capped_sync(base_url, model, prompt, system, max_tokens, timeout)
            )
        except Exception as e:
            logger.error(f"Local streaming generation failed (ollama): {e}")
            return f"Generation failed: {e}"

    def _generate_stream_capped_sync(
        self,
        base_url: str,
        model: str,
        prompt: str,
        system: str,
        max_tokens: int,
        timeout: float,
    ) -> str:
        url = f"{base_url.rstrip('/')}/api/generate"
        payload = {"model": model, "prompt": prompt, "system": system, "stream": True}
        resp = requests.post(url, json=payload, timeout=timeout, stream=True)
        resp.raise_for_status()
        chunks: list[str] = []
        count = 0
        try:
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except ValueError:
                    continue
                token = data.get("response", "") or ""
                if token:
                    chunks.append(token)
                    count += 1
                if data.get("done") or count >= max_tokens:
                    break
        finally:
            resp.close()
        return "".join(chunks)


local_llm_provider = LocalLLMProvider()
