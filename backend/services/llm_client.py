"""
Unified LLM Client — supports multiple API providers.
All services should import `call_llm` from this module instead of
making direct HTTP calls to a specific provider.

Supported providers:
  - groq      → Groq Cloud (Llama 3, Mixtral, etc.)
  - openrouter → OpenRouter (access to 100+ models)

The active provider is determined by the LLM_PROVIDER setting in config.
"""

import httpx
from config import settings

# ── Provider Configurations ────────────────────────────────────
PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "default_model": "llama-3.3-70b-versatile",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "default_model": "meta-llama/llama-3.3-70b-instruct",
    },
}


def _get_config_for_provider(provider: str) -> dict:
    """Resolve configuration for a specific provider."""
    provider = provider.lower()
    if provider not in PROVIDERS:
        raise ValueError(
            f"Unsupported LLM provider: '{provider}'. "
            f"Supported: {', '.join(PROVIDERS.keys())}"
        )

    cfg = PROVIDERS[provider]

    # Resolve API key
    if provider == "groq":
        api_key = settings.GROQ_API_KEY
    elif provider == "openrouter":
        api_key = settings.OPENROUTER_API_KEY
    else:
        api_key = ""

    if not api_key:
        raise ValueError(f"API key not set for provider '{provider}'.")

    # Use settings model if provider matches target provider, else fall back to default
    model = None
    if settings.LLM_PROVIDER.lower() == provider:
        model = settings.LLM_MODEL
    if not model:
        model = cfg["default_model"]

    return {
        "url": cfg["base_url"],
        "api_key": api_key,
        "model": model,
        "provider": provider,
    }


def _get_provider_config() -> dict:
    """Return the active provider's config."""
    return _get_config_for_provider(settings.LLM_PROVIDER)


async def call_llm(
    prompt: str,
    system_msg: str = None,
    temperature: float = None,
    max_tokens: int = None,
    timeout: float = 60.0,
) -> str:
    """
    Call configured LLM provider with failover support to alternative providers on failure.
    """
    providers_to_try = [settings.LLM_PROVIDER.lower()]
    for p in PROVIDERS.keys():
        if p not in providers_to_try:
            providers_to_try.append(p)

    last_error = None
    import logging
    logger = logging.getLogger(__name__)

    for provider in providers_to_try:
        try:
            cfg = _get_config_for_provider(provider)
        except Exception as e:
            logger.warning(f"Skipping failover provider '{provider}' due to configuration error: {e}")
            last_error = e
            continue

        messages = []
        if system_msg:
            messages.append({"role": "system", "content": system_msg})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        }

        if cfg["provider"] == "openrouter":
            headers["HTTP-Referer"] = "http://localhost:3000"
            headers["X-Title"] = settings.APP_NAME

        payload = {
            "model": cfg["model"],
            "messages": messages,
            "temperature": temperature if temperature is not None else settings.LLM_TEMPERATURE,
            "max_tokens": max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS,
        }

        try:
            logger.info(f"Sending LLM request to: {provider} (model: {cfg['model']})")
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(cfg["url"], headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"LLM request to '{provider}' failed: {e}. Trying alternate failover providers...")
            last_error = e
            continue

    raise RuntimeError(f"All LLM providers failed. Last error: {str(last_error)}")


async def call_llm_stream(
    prompt: str,
    system_msg: str = None,
    temperature: float = None,
    max_tokens: int = None,
    timeout: float = 120.0,
):
    """
    Stream LLM responses with failover support to alternative providers on failure.
    """
    providers_to_try = [settings.LLM_PROVIDER.lower()]
    for p in PROVIDERS.keys():
        if p not in providers_to_try:
            providers_to_try.append(p)

    last_error = None
    import logging
    logger = logging.getLogger(__name__)
    import json

    for provider in providers_to_try:
        try:
            cfg = _get_config_for_provider(provider)
        except Exception as e:
            logger.warning(f"Skipping streaming failover provider '{provider}' due to configuration error: {e}")
            last_error = e
            continue

        messages = []
        if system_msg:
            messages.append({"role": "system", "content": system_msg})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        }

        if cfg["provider"] == "openrouter":
            headers["HTTP-Referer"] = "http://localhost:3000"
            headers["X-Title"] = settings.APP_NAME

        payload = {
            "model": cfg["model"],
            "messages": messages,
            "temperature": temperature if temperature is not None else settings.LLM_TEMPERATURE,
            "max_tokens": max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS,
            "stream": True,
        }

        try:
            logger.info(f"Initiating streaming LLM request to: {provider} (model: {cfg['model']})")
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", cfg["url"], headers=headers, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue
            # If streaming finished successfully, break failover loop and return
            return
        except Exception as e:
            logger.error(f"Streaming LLM request to '{provider}' failed: {e}. Trying alternate providers...")
            last_error = e
            continue

    raise RuntimeError(f"All LLM streaming providers failed. Last error: {str(last_error)}")
