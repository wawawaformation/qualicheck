import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

from config import load_config
from logging_utils import format_log_line

OPENAI_API_VERSION = "2024-02-01"
ANTHROPIC_API_VERSION = "2023-06-01"
ANTHROPIC_MAX_TOKENS = 256
READ_TIMEOUT_SECONDS = 30
CALLS_PER_PROMPT = 5
PROMPTS = {
    "short": "dis ok",
    "long": "pourquoi le ciel est bleu en 5 phrases",
}
ANTHROPIC_MODELS = {"claude-sonnet-4-6", "claude-haiku-4-5"}

BASE_DIR = Path(__file__).resolve().parent
MODELS_JSON_PATH = BASE_DIR / "models.json"
LOG_PATH = BASE_DIR / "logs" / "benchmark.log"


def _call_openai(resource: str, api_key: str, model: str, prompt: str) -> requests.Response:
    url = f"https://{resource}.openai.azure.com/openai/deployments/{model}/chat/completions"
    params = {"api-version": OPENAI_API_VERSION}
    headers = {"api-key": api_key, "Content-Type": "application/json"}
    body = {"messages": [{"role": "user", "content": prompt}]}
    return requests.post(url, params=params, headers=headers, json=body, timeout=READ_TIMEOUT_SECONDS)


def _call_anthropic(resource: str, api_key: str, model: str, prompt: str) -> requests.Response:
    url = f"https://{resource}.services.ai.azure.com/anthropic/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_API_VERSION,
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "max_tokens": ANTHROPIC_MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }
    return requests.post(url, headers=headers, json=body, timeout=READ_TIMEOUT_SECONDS)


def call_model(resource: str, api_key: str, model: str, prompt: str) -> tuple[float, str, str | None]:
    send_request = _call_anthropic if model in ANTHROPIC_MODELS else _call_openai

    start = time.monotonic()
    try:
        response = send_request(resource, api_key, model, prompt)
        latency_ms = (time.monotonic() - start) * 1000
        if response.status_code >= 400:
            return latency_ms, "error", f"HTTP {response.status_code}: {response.text[:200]}"
        return latency_ms, "ok", None
    except requests.exceptions.RequestException as exc:
        latency_ms = (time.monotonic() - start) * 1000
        return latency_ms, "error", str(exc)


def run_benchmark() -> None:
    load_dotenv(BASE_DIR / ".env")
    regions = load_config(MODELS_JSON_PATH)

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as log_file:
        for region in regions:
            for model in region.models:
                for prompt_type, prompt_text in PROMPTS.items():
                    for _ in range(CALLS_PER_PROMPT):
                        latency_ms, status, error = call_model(
                            region.resource, region.api_key, model, prompt_text
                        )
                        line = format_log_line(
                            timestamp=datetime.now(),
                            region=region.name,
                            model=model,
                            prompt_type=prompt_type,
                            latency_ms=round(latency_ms, 1),
                            status=status,
                            error=error,
                        )
                        log_file.write(line + "\n")
                        log_file.flush()


def main() -> None:
    run_benchmark()


if __name__ == "__main__":
    main()
