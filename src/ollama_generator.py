from __future__ import annotations

import json
from typing import Any
from urllib import request


def ollama_generate(
    prompt: str,
    model: str = "llama3.1:8b",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.1,
    timeout: int = 120,
) -> str:
    """Generate an answer with a locally running Ollama model.

    Ollama exposes a local HTTP API on port 11434. This helper uses only the
    Python standard library, so no extra client dependency is needed.
    """

    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    url = f"{base_url.rstrip('/')}/api/generate"
    http_request = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=timeout) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except OSError as exc:
        raise ConnectionError(
            "Could not connect to Ollama. Make sure Ollama is running locally "
            f"at {base_url} and that the model '{model}' is pulled."
        ) from exc

    return str(response_data.get("response", "")).strip()
