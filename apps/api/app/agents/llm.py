"""LLM call wrappers for the four agents (Section 7 / Section 21):
DeepSeek-R1 for Agents 1-3 (cheaper chain-of-thought), Claude Sonnet reserved
for Agent 4 (final synthesis/risk audit).

Both wrappers ask the model to answer in JSON and parse leniently — DeepSeek's
reasoning models don't reliably support OpenAI's `response_format=json_object`
constrained decoding, so this extracts the first top-level `{...}` block from
the response text instead of trusting the model to emit *only* JSON.
"""

import json
import re

from anthropic import Anthropic
from openai import OpenAI

from app.config import settings


class LLMNotConfigured(RuntimeError):
    pass


class LLMResponseError(RuntimeError):
    pass


_deepseek_client: OpenAI | None = None
_anthropic_client: Anthropic | None = None


def _get_deepseek_client() -> OpenAI:
    global _deepseek_client
    if _deepseek_client is None:
        if not settings.deepseek_api_key:
            raise LLMNotConfigured("DEEPSEEK_API_KEY is not configured")
        _deepseek_client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
    return _deepseek_client


def _get_anthropic_client() -> Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        if not settings.anthropic_api_key:
            raise LLMNotConfigured("ANTHROPIC_API_KEY is not configured")
        _anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise LLMResponseError(f"No JSON object found in model output: {text[:200]!r}")
    try:
        return json.loads(match.group())
    except json.JSONDecodeError as exc:
        raise LLMResponseError(f"Model output was not valid JSON: {exc}") from exc


def call_deepseek(system: str, user_prompt: str) -> tuple[dict, int]:
    """Returns (parsed_json_response, total_tokens_used)."""
    client = _get_deepseek_client()
    response = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt + "\n\nRespond with a single JSON object only."},
        ],
        max_tokens=2000,
    )
    content = response.choices[0].message.content or ""
    tokens = response.usage.total_tokens if response.usage else 0
    return extract_json(content), tokens


def call_claude(system: str, user_prompt: str) -> tuple[dict, int]:
    """Returns (parsed_json_response, total_tokens_used)."""
    client = _get_anthropic_client()
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=2000,
        system=system,
        messages=[
            {"role": "user", "content": user_prompt + "\n\nRespond with a single JSON object only."}
        ],
    )
    content = "".join(block.text for block in response.content if block.type == "text")
    tokens = response.usage.input_tokens + response.usage.output_tokens
    return extract_json(content), tokens
