"""Structured model calls. The runner depends only on the StructuredCaller protocol."""

from dataclasses import dataclass
from typing import Literal, Protocol, TypeVar

import anthropic
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

MODEL = "claude-opus-5-5"
Effort = Literal["low", "medium", "high", "xhigh", "max"]


class AnalysisError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class CallResult[R: BaseModel]:
    parsed: R
    model: str
    message_id: str
    stop_reason: str
    usage: dict[str, object]


class StructuredCaller(Protocol):
    model: str

    def call(self, *, system: str, user: str, schema: type[T]) -> CallResult[T]: ...


class AnthropicCaller:
    """Claude with adaptive thinking, streaming, and server-side refusal fallback."""

    def __init__(
        self,
        client: anthropic.Anthropic | None = None,
        model: str = MODEL,
        effort: Effort = "high",
        max_tokens: int = 64000,
    ) -> None:
        self._client = client or anthropic.Anthropic()
        self.model = model
        self._effort: Effort = effort
        self._max_tokens = max_tokens

    def call(self, *, system: str, user: str, schema: type[T]) -> CallResult[T]:
        with self._client.beta.messages.stream(
            model=self.model,
            max_tokens=self._max_tokens,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            thinking={"type": "adaptive"},
            output_config={"effort": self._effort},
            output_format=schema,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            message = stream.get_final_message()
        if message.stop_reason in ("refusal", "max_tokens"):
            raise AnalysisError(f"{schema.__name__}: model stopped with {message.stop_reason}")
        parsed = message.parsed_output
        if parsed is None:
            raise AnalysisError(f"{schema.__name__}: no parsed output in response {message.id}")
        return CallResult(
            parsed=parsed,
            model=message.model,
            message_id=message.id,
            stop_reason=str(message.stop_reason),
            usage=message.usage.to_dict(),
        )
