"""Structured model calls through OpenRouter's chat completions API (any model it routes to)."""

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Literal, TypeVar

from pydantic import BaseModel, ValidationError

from icma.analysis.llm import AnalysisError, CallResult

T = TypeVar("T", bound=BaseModel)

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-opus-5.5"
Effort = Literal["low", "medium", "high", "xhigh", "max"]
JSON = dict[str, object]
Transport = Callable[[JSON, str], JSON]


def _inline(node: object, defs: dict[str, object]) -> object:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str):
            return _inline(defs[ref.removeprefix("#/$defs/")], defs)
        return {k: _inline(v, defs) for k, v in node.items() if k not in ("$defs", "title")}
    if isinstance(node, list):
        return [_inline(item, defs) for item in node]
    return node


def strict_schema(model: type[BaseModel]) -> JSON:
    """The model's JSON schema with every $ref inlined, so any provider's strict mode accepts it."""
    schema = model.model_json_schema()
    defs = schema.get("$defs", {})
    inlined = _inline(schema, defs if isinstance(defs, dict) else {})
    if not isinstance(inlined, dict):
        raise TypeError("schema root must be an object")
    return inlined


def _post(body: JSON, api_key: str) -> JSON:
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=1800) as response:
            payload: JSON = json.loads(response.read())
            return payload
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:500]
        raise AnalysisError(f"OpenRouter HTTP {error.code}: {detail}") from error


def _message(payload: JSON) -> tuple[str, str]:
    """Return (content, finish_reason) from a chat completion payload."""
    if "error" in payload:
        raise AnalysisError(f"OpenRouter error: {payload['error']}")
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise AnalysisError("OpenRouter response has no choices")
    message = choices[0].get("message")
    content = message.get("content") if isinstance(message, dict) else None
    return (content if isinstance(content, str) else ""), str(choices[0].get("finish_reason"))


class OpenRouterCaller:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        effort: Effort = "high",
        max_tokens: int = 128_000,
        api_key: str | None = None,
        transport: Transport = _post,
    ) -> None:
        key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise AnalysisError("OPENROUTER_API_KEY is not set")
        self._key = key
        self._model = model
        self._effort: Effort = effort
        self._max_tokens = max_tokens
        self._transport = transport

    def _body(self, system: str, user: str, schema: type[BaseModel]) -> JSON:
        return {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "reasoning": {"effort": self._effort, "exclude": True},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "strict": True,
                    "schema": strict_schema(schema),
                },
            },
            "provider": {"require_parameters": True},
            "usage": {"include": True},
        }

    def call(self, *, system: str, user: str, schema: type[T]) -> CallResult[T]:
        payload = self._transport(self._body(system, user, schema), self._key)
        content, finish = _message(payload)
        if finish == "length":
            raise AnalysisError(f"{schema.__name__}: output hit max_tokens before finishing")
        try:
            parsed = schema.model_validate_json(content)
        except ValidationError as error:
            raise AnalysisError(
                f"{schema.__name__}: output does not match the schema: {error}"
            ) from error
        usage = payload.get("usage")
        return CallResult(
            parsed=parsed,
            model=str(payload.get("model", self._model)),
            message_id=str(payload.get("id", "")),
            stop_reason=finish,
            usage=usage if isinstance(usage, dict) else {},
        )
