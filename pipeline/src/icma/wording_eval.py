"""Score the wording rules (analysis/wording.py) against labels in eval/gold/chain-wording/.

A label gives a chain's basis, its words as two normalized anchors ("from", "to", and "after" to
skip an earlier occurrence), and the chain a formula refers to. Two references agree when they
name the same chain or chains whose gold wordings are identical.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from icma.analysis.wording import ChainWording, extract_wordings
from icma.arabic import normalize
from icma.cli import load_corrected
from icma.models import Tradition
from icma.sources.hadith_kg import HadithKgReader

Label = dict[str, object]


@dataclass(frozen=True, slots=True)
class ChainError:
    hadith_id: int
    chain_id: int
    problems: tuple[str, ...]


@dataclass(slots=True)
class WordingScore:
    chains: int = 0
    correct: int = 0
    entries: int = 0
    entries_correct: int = 0
    errors: list[ChainError] = field(default_factory=list)


def load_gold(path: Path) -> dict[str, object]:
    gold: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    return gold


def load_selection(gold: dict[str, object], db: Path, root: Path) -> Tradition:
    """The entries a gold file labels: listed hadith ids, or a meaning group with anchors."""
    selection = gold["selection"]
    assert isinstance(selection, dict)
    if "hadith_ids" in selection:
        return HadithKgReader(db).load_entries(selection["hadith_ids"])
    corrections = selection.get("corrections")
    path = root / corrections if isinstance(corrections, str) else None
    return load_corrected(db, selection["group"], tuple(selection["anchors"]), path)[0]


def gold_wording(label: Label, text_ar: str) -> str | None:
    """The labelled words, normalized; raises ValueError when an anchor is missing."""
    if "from" not in label:
        return None
    norm = normalize(text_ar)
    base = norm.find(str(label["after"])) if "after" in label else 0
    start = norm.find(str(label["from"]), base) if base >= 0 else -1
    end = norm.find(str(label["to"]), start) if start >= 0 else -1
    if min(base, start, end) < 0:
        raise ValueError(f"chain {label['chain']}: an anchor is not in the text")
    return norm[start : end + len(str(label["to"]))]


def score(gold: dict[str, object], tradition: Tradition) -> WordingScore:
    chains = gold["chains"]
    assert isinstance(chains, list)
    labels: dict[int, Label] = {int(g["chain"]): g for g in chains}
    hadith_of = {c.id: c.hadith_id for c in tradition.chains}
    texts = {h.id: h.text_ar for h in tradition.hadiths}
    expected = {cid: gold_wording(g, texts[hadith_of[cid]]) for cid, g in labels.items()}
    found = _extract(tradition, {hadith_of[cid] for cid in labels})
    result = WordingScore()
    for cid, label in labels.items():
        problems = _compare(label, found[cid], texts[hadith_of[cid]], expected)
        result.chains += 1
        result.correct += not problems
        if problems:
            result.errors.append(ChainError(hadith_of[cid], cid, problems))
    wrong = {e.hadith_id for e in result.errors}
    result.entries = len({hadith_of[cid] for cid in labels})
    result.entries_correct = result.entries - len(wrong)
    return result


def _extract(tradition: Tradition, hadith_ids: set[int]) -> dict[int, ChainWording]:
    names = {n.id: (n.name_ar, n.display_name_ar) for n in tradition.narrators}
    found: dict[int, ChainWording] = {}
    for hadith in tradition.hadiths:
        if hadith.id in hadith_ids:
            chains = [c for c in tradition.chains if c.hadith_id == hadith.id]
            found.update((r.chain_id, r) for r in extract_wordings(hadith, chains, names))
    return found


def _compare(
    label: Label, record: ChainWording, text_ar: str, expected: dict[int, str | None]
) -> tuple[str, ...]:
    problems: list[str] = []
    if record.basis != label["basis"]:
        problems.append(f"basis {record.basis}, gold {label['basis']}")
    span = record.span
    got = normalize(text_ar[span.start : span.end]) if span else None
    if got != expected[record.chain_id]:
        problems.append(f"wording\n    got:  {got}\n    gold: {expected[record.chain_id]}")
    gold_ref = label.get("refers_to")
    if (gold_ref is not None or record.refers_to is not None) and not _same_target(
        record.refers_to, gold_ref, expected
    ):
        problems.append(f"refers_to {record.refers_to}, gold {gold_ref}")
    return tuple(problems)


def _same_target(found: int | None, gold: object, expected: dict[int, str | None]) -> bool:
    """The same chain, or two chains whose gold wordings are the same words."""
    if found == gold:
        return True
    if found is None or not isinstance(gold, int):
        return False
    words = expected.get(found)
    return words is not None and words == expected.get(gold)
