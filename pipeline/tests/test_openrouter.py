import json

import pytest

from icma.analysis.llm import AnalysisError
from icma.analysis.openrouter import JSON, OpenRouterCaller, strict_schema
from icma.analysis.schemas import ChainMatnSet, IcmaAnalysis

MATN = {
    "chain_id": 1,
    "relation": "full_text",
    "matn_ar": "خذوا عني",
    "same_as_chain_id": None,
    "reference_formula_ar": "",
    "note_en": "",
}


def reply(content: str, finish: str = "stop") -> JSON:
    return {
        "id": "gen-1",
        "model": "anthropic/claude-opus-5.5",
        "choices": [{"message": {"content": content}, "finish_reason": finish}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.01},
    }


def caller(response: JSON, seen: list[JSON] | None = None) -> OpenRouterCaller:
    def transport(body: JSON, key: str) -> JSON:
        assert key == "k"
        if seen is not None:
            seen.append(body)
        return response

    return OpenRouterCaller(api_key="k", transport=transport)


def at(node: object, *path: str) -> object:
    for key in path:
        assert isinstance(node, dict)
        node = node[key]
    return node


def test_strict_schema_inlines_refs_everywhere() -> None:
    text = json.dumps(strict_schema(IcmaAnalysis))
    assert "$ref" not in text and "$defs" not in text
    item = at(strict_schema(ChainMatnSet), "properties", "chains", "items")
    assert at(item, "additionalProperties") is False


def test_request_asks_for_strict_json_and_reasoning() -> None:
    seen: list[JSON] = []
    caller(reply(json.dumps({"chains": [MATN]})), seen).call(
        system="s", user="u", schema=ChainMatnSet
    )
    body = seen[0]
    assert body["model"] == "anthropic/claude-opus-5.5"
    assert body["reasoning"] == {"effort": "high", "exclude": True}
    assert body["provider"] == {"require_parameters": True}
    assert at(body, "response_format", "json_schema", "strict") is True


def test_parses_content_and_keeps_usage() -> None:
    result = caller(reply(json.dumps({"chains": [MATN]}))).call(
        system="s", user="u", schema=ChainMatnSet
    )
    assert result.parsed.chains[0].matn_ar == "خذوا عني"
    assert result.usage["cost"] == 0.01
    assert result.message_id == "gen-1"


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (reply("{}", finish="length"), "max_tokens"),
        (reply('{"chains": [{"chain_id": "x"}]}'), "does not match"),
        ({"error": {"message": "rate limited"}}, "rate limited"),
        ({"choices": []}, "no choices"),
    ],
)
def test_failures_raise_analysis_error(response: JSON, message: str) -> None:
    with pytest.raises(AnalysisError, match=message):
        caller(response).call(system="s", user="u", schema=ChainMatnSet)


def test_missing_key_is_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(AnalysisError, match="OPENROUTER_API_KEY"):
        OpenRouterCaller()
