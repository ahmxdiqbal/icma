from pathlib import Path

from kg_fixture import build
from pydantic import BaseModel

from icma.analysis.llm import CallResult
from icma.analysis.runner import analysis_json, analyze, check_chain_matns
from icma.analysis.schemas import ChainMatn, ChainMatnSet, IcmaAnalysis, MatnInventory
from icma.cli import bundle_of, load_corrected

INVENTORY: dict[str, object] = {
    "elements": [{"id": "E1", "label_en": "take from me", "description_en": "", "exemplar_ar": ""}],
    "variants": [
        {
            "variant_id": "V1",
            "elements": [{"element_id": "E1", "wording_ar": "خذوا عني", "wording_class": "a"}],
            "translation_en": "Take from me.",
            "notes_en": "",
        }
    ],
}

JUDGEMENT = {"node_key": "n:2", "verdict": "supported", "reasoning": "r"}
SYNTHESIS: dict[str, object] = {
    "convergence_point": JUDGEMENT,
    "common_links": [{**JUDGEMENT, "cluster_labels": ["A"]}],
    "partial_common_links": [{**JUDGEMENT, "node_key": "n:99"}],
    "upper_isnad": "",
    "dives": [{"chain_id": 1001, "interpretation": "undecidable", "reasoning": ""}],
    "matn_clusters": [
        {"label": "A", "defining_features": "", "variant_ids": ["V1"], "branch_node_keys": []}
    ],
    "correlation": {"finding": "insufficient_data", "reasoning": ""},
    "reconstructions": [
        {"node_key": "n:2", "text_ar": "", "translation_en": "", "uncertain_elements": []}
    ],
    "dating": {
        "earliest_reliable_node_key": "n:2",
        "date_range_ah": "",
        "date_range_ce": "",
        "reasoning": "",
    },
    "alternative_readings": [],
    "open_questions": [],
    "confidence": "low",
}

MATN_ITEM: dict[str, object] = {
    "chain_id": 0,
    "relation": "full_text",
    "matn_ar": "خذوا عني",
    "same_as_chain_id": None,
    "reference_formula_ar": "",
    "note_en": "",
}
CHAIN_MATNS: dict[str, object] = {
    "chains": [{**MATN_ITEM, "chain_id": cid} for cid in (1000, 1001, 4242)]
}


class FakeCaller:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self._outputs: dict[type[BaseModel], dict[str, object]] = {
            ChainMatnSet: CHAIN_MATNS,
            MatnInventory: INVENTORY,
            IcmaAnalysis: SYNTHESIS,
        }

    def call[M: BaseModel](self, *, system: str, user: str, schema: type[M]) -> CallResult[M]:
        self.calls.append(schema.__name__)
        parsed = schema.model_validate(self._outputs[schema])
        return CallResult(parsed, "fake", "msg_1", "end_turn", {"output_tokens": 1})


def run(tmp_path: Path, caller: FakeCaller) -> dict[str, object]:
    db = tmp_path / "kg.db"
    tradition, _ = load_corrected(db if db.exists() else build(db), 730, (1,), None)
    bundle = bundle_of(tradition)
    result = analyze("t", tradition, bundle, caller, tmp_path / "out")
    return analysis_json("t", result)


def test_runs_all_three_model_stages_and_validates_references(tmp_path: Path) -> None:
    caller = FakeCaller()
    output = run(tmp_path, caller)
    assert caller.calls == ["ChainMatnSet", "MatnInventory", "IcmaAnalysis"]
    assert output["status"] == "unreviewed"
    warnings = output["warnings"]
    assert isinstance(warnings, list)
    assert "chain_matns: unknown chain id 4242 dropped" in warnings
    assert "icma_synthesis: unknown node key n:99" in warnings
    assert not any("unknown chain 1001" in w for w in warnings)


def test_rerun_with_same_inputs_uses_cache(tmp_path: Path) -> None:
    first = FakeCaller()
    run(tmp_path, first)
    second = FakeCaller()
    run(tmp_path, second)
    assert second.calls == []
    assert len(list((tmp_path / "out").glob("*.json"))) == 3


def test_check_chain_matns_reports_duplicates_and_missing() -> None:
    def m(cid: int) -> ChainMatn:
        return ChainMatn.model_validate({**MATN_ITEM, "chain_id": cid})

    kept, warnings = check_chain_matns([m(1), m(1), m(7)], {1, 2})
    assert [k.chain_id for k in kept] == [1]
    assert warnings == [
        "chain_matns: duplicate chain id 1; first kept",
        "chain_matns: unknown chain id 7 dropped",
        "chain_matns: no extraction for chain 2",
    ]
