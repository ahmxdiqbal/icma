"""Score an ICMA synthesis against a scoring key built from a published study."""

from collections.abc import Mapping
from dataclasses import dataclass

from icma.analysis.schemas import IcmaAnalysis

IDENTIFIED = {"supported", "doubtful"}


@dataclass(frozen=True, slots=True)
class ScoringKey:
    common_links: frozenset[str]
    not_common_links: frozenset[str]
    unresolved: frozenset[str]
    partial_common_links: frozenset[str]
    not_partial_common_links: frozenset[str]
    convergence_key: str
    convergence_expected: frozenset[str]


@dataclass(frozen=True, slots=True)
class Score:
    cl_recall: float
    cl_precision: float
    false_common_links: tuple[str, ...]
    missed_common_links: tuple[str, ...]
    pcl_recall: float
    false_partial_common_links: tuple[str, ...]
    convergence_verdict_correct: bool


def _keys(raw: Mapping[str, object], field: str) -> frozenset[str]:
    value = raw.get(field, {})
    if not isinstance(value, Mapping):
        raise ValueError(f"scoring key field '{field}' must be an object keyed by node key")
    return frozenset(str(k) for k in value)


def load_key(raw: Mapping[str, object]) -> ScoringKey:
    convergence = raw.get("convergence_point")
    if not isinstance(convergence, Mapping):
        raise ValueError("scoring key needs a convergence_point object")
    expected = convergence.get("expected_verdicts")
    if not isinstance(expected, list):
        raise ValueError("convergence_point.expected_verdicts must be a list")
    return ScoringKey(
        common_links=_keys(raw, "common_links"),
        not_common_links=_keys(raw, "not_common_links"),
        unresolved=_keys(raw, "unresolved"),
        partial_common_links=_keys(raw, "partial_common_links"),
        not_partial_common_links=_keys(raw, "not_partial_common_links"),
        convergence_key=str(convergence.get("node_key")),
        convergence_expected=frozenset(str(v) for v in expected),
    )


def _ratio(hits: int, total: int) -> float:
    return hits / total if total else 0.0


def score(analysis: IcmaAnalysis, key: ScoringKey) -> Score:
    claimed_cls = {c.node_key for c in analysis.common_links if c.verdict in IDENTIFIED}
    claimed_pcls = {p.node_key for p in analysis.partial_common_links if p.verdict in IDENTIFIED}
    judged_cls = claimed_cls - key.unresolved
    # A figure the study hedges between CL and PCL counts as found if named in either list.
    found_pcls = (claimed_pcls | claimed_cls) & key.partial_common_links
    convergence = analysis.convergence_point
    return Score(
        cl_recall=_ratio(len(claimed_cls & key.common_links), len(key.common_links)),
        cl_precision=_ratio(len(judged_cls & key.common_links), len(judged_cls)),
        false_common_links=tuple(sorted(claimed_cls & key.not_common_links)),
        missed_common_links=tuple(sorted(key.common_links - claimed_cls)),
        pcl_recall=_ratio(len(found_pcls), len(key.partial_common_links)),
        false_partial_common_links=tuple(sorted(claimed_pcls & key.not_partial_common_links)),
        convergence_verdict_correct=convergence.node_key == key.convergence_key
        and convergence.verdict in key.convergence_expected,
    )
