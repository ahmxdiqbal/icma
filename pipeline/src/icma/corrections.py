"""Manual, evidence-backed fixes to source chains. Each one is also a labelled training example."""

import json
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

from icma.models import Chain, GapKind, GapLink, Link, NarratorLink


@dataclass(frozen=True, slots=True)
class Correction:
    chain_id: int
    op: Literal["replace", "set_links", "exclude"]
    reason: str
    evidence: str
    author: str
    date: str
    from_narrator_id: int | None = None
    to_narrator_id: int | None = None
    links: tuple[Link, ...] | None = None


class CorrectionError(ValueError):
    pass


def _fail(entry: dict[str, object], message: str) -> CorrectionError:
    return CorrectionError(f"correction for chain {entry.get('chain_id')!r}: {message}")


def _req_int(entry: dict[str, object], field: str) -> int:
    value = entry.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        raise _fail(entry, f"'{field}' must be an integer")
    return value


def _req_str(entry: dict[str, object], field: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        raise _fail(entry, f"'{field}' must be a non-empty string")
    return value


def _parse_link(entry: dict[str, object], raw: object) -> Link:
    if isinstance(raw, dict):
        narrator_id = raw.get("narrator_id")
        if isinstance(narrator_id, int) and not isinstance(narrator_id, bool):
            return NarratorLink(narrator_id)
        gap = raw.get("gap")
        if isinstance(gap, str) and gap in GapKind:
            return GapLink(GapKind(gap))
    raise _fail(entry, f"invalid link {raw!r}")


def _req_links(entry: dict[str, object]) -> tuple[Link, ...]:
    raw = entry.get("links")
    if not isinstance(raw, list) or len(raw) < 2:
        raise _fail(entry, "'links' must list at least two links, earliest authority first")
    return tuple(_parse_link(entry, item) for item in raw)


def _parse(entry: dict[str, object]) -> Correction:
    op = entry.get("op")
    if op != "replace" and op != "set_links" and op != "exclude":
        raise _fail(entry, f"unknown op {op!r}")
    is_replace = op == "replace"
    return Correction(
        chain_id=_req_int(entry, "chain_id"),
        op=op,
        reason=_req_str(entry, "reason"),
        evidence=_req_str(entry, "evidence"),
        author=_req_str(entry, "author"),
        date=_req_str(entry, "date"),
        from_narrator_id=_req_int(entry, "from_narrator_id") if is_replace else None,
        to_narrator_id=_req_int(entry, "to_narrator_id") if is_replace else None,
        links=_req_links(entry) if op == "set_links" else None,
    )


def load_corrections(path: Path) -> list[Correction]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries = raw.get("corrections") if isinstance(raw, dict) else None
    if not isinstance(entries, list):
        raise CorrectionError(f"{path}: expected an object with a 'corrections' list")
    corrections = [_parse(e) for e in entries if isinstance(e, dict)]
    if len(corrections) != len(entries):
        raise CorrectionError(f"{path}: every correction must be an object")
    ids = [c.chain_id for c in corrections]
    if len(ids) != len(set(ids)):
        raise CorrectionError(f"{path}: more than one correction for the same chain")
    return corrections


def _replace_narrator(chain: Chain, correction: Correction) -> Chain:
    if correction.from_narrator_id is None or correction.to_narrator_id is None:
        raise CorrectionError(f"chain {chain.id}: replace needs from and to narrator ids")
    target = NarratorLink(correction.from_narrator_id)
    if target not in chain.links:
        raise CorrectionError(
            f"chain {chain.id}: narrator {correction.from_narrator_id} not found; stale correction?"
        )
    new = NarratorLink(correction.to_narrator_id)
    return replace(chain, links=tuple(new if link == target else link for link in chain.links))


def apply_corrections(
    chains: Sequence[Chain], corrections: Sequence[Correction]
) -> tuple[list[Chain], list[Correction]]:
    """Return corrected chains and the corrections that applied to them."""
    by_chain = {c.chain_id: c for c in corrections}
    result: list[Chain] = []
    applied: list[Correction] = []
    for chain in chains:
        correction = by_chain.get(chain.id)
        if correction is None:
            result.append(chain)
            continue
        applied.append(correction)
        if correction.op == "replace":
            result.append(_replace_narrator(chain, correction))
        elif correction.op == "set_links" and correction.links is not None:
            result.append(replace(chain, links=correction.links))
    return result, applied
