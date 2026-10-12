import json
from pathlib import Path

import pytest

from icma.analysis.schemas import IcmaAnalysis
from icma.evaluate import load_key, score

KEY: dict[str, object] = {
    "common_links": {"n:1": {}, "n:2": {}},
    "not_common_links": {"n:9": {}},
    "unresolved": {"n:5": {}},
    "partial_common_links": {"n:3": {}, "n:4": {}},
    "not_partial_common_links": {"n:8": {}},
    "convergence_point": {"node_key": "n:9", "expected_verdicts": ["rejected", "doubtful"]},
}


def judgement(key: str, verdict: str = "supported") -> dict[str, object]:
    return {"node_key": key, "verdict": verdict, "reasoning": ""}


def analysis(
    cls: list[dict[str, object]],
    pcls: list[dict[str, object]],
    convergence: dict[str, object],
) -> IcmaAnalysis:
    return IcmaAnalysis.model_validate(
        {
            "convergence_point": convergence,
            "common_links": [{**c, "cluster_labels": []} for c in cls],
            "partial_common_links": pcls,
            "upper_isnad": "",
            "dives": [],
            "matn_clusters": [],
            "correlation": {"finding": "partial", "reasoning": ""},
            "reconstructions": [],
            "dating": {
                "earliest_reliable_node_key": "n:1",
                "date_range_ah": "",
                "date_range_ce": "",
                "reasoning": "",
            },
            "alternative_readings": [],
            "open_questions": [],
            "confidence": "medium",
        }
    )


def test_scores_recall_precision_and_errors() -> None:
    result = score(
        analysis(
            [judgement("n:1"), judgement("n:9"), judgement("n:5"), judgement("n:2", "rejected")],
            [judgement("n:3"), judgement("n:8", "doubtful")],
            judgement("n:9", "rejected"),
        ),
        load_key(KEY),
    )
    assert result.cl_recall == 0.5
    assert result.cl_precision == 0.5  # n:5 is unresolved and neutral
    assert result.false_common_links == ("n:9",)
    assert result.missed_common_links == ("n:2",)
    assert result.pcl_recall == 0.5
    assert result.false_partial_common_links == ("n:8",)
    assert result.convergence_verdict_correct


def test_hedged_pcl_named_as_cl_counts_as_found() -> None:
    result = score(analysis([judgement("n:4")], [], judgement("n:9", "supported")), load_key(KEY))
    assert result.pcl_recall == 0.5
    assert not result.convergence_verdict_correct


def test_empty_claims_score_zero_without_dividing_by_zero() -> None:
    result = score(analysis([], [], judgement("n:9", "doubtful")), load_key(KEY))
    assert (result.cl_recall, result.cl_precision, result.pcl_recall) == (0.0, 0.0, 0.0)


def test_real_key_file_loads() -> None:
    path = Path(__file__).parents[2] / "eval/gold/ubada-pavlovitch-2011.key.json"
    key = load_key(json.loads(path.read_text(encoding="utf-8")))
    assert "n:3795" in key.common_links
    assert key.convergence_key == "n:1239"


def test_malformed_key_is_rejected() -> None:
    with pytest.raises(ValueError, match="convergence_point"):
        load_key({"common_links": {}})
