"""Attach a matn to every chain and group identical matns into variants. Deterministic."""

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from icma.analysis.schemas import ChainMatn
from icma.arabic import normalize
from icma.models import Tradition

TextSource = Literal["span", "extracted", "inherited", "missing"]


@dataclass(frozen=True, slots=True)
class ChainText:
    chain_id: int
    hadith_id: int
    text_ar: str | None
    source: TextSource


@dataclass(frozen=True, slots=True)
class Variant:
    id: str
    text_ar: str
    chain_ids: tuple[int, ...]


def multi_chain_hadith_ids(tradition: Tradition) -> set[int]:
    counts = Counter(c.hadith_id for c in tradition.chains)
    return {hadith_id for hadith_id, n in counts.items() if n > 1}


def _span_text(tradition: Tradition) -> dict[int, str | None]:
    texts: dict[int, str | None] = {}
    for h in tradition.hadiths:
        span = h.matn_span
        texts[h.id] = h.text_ar[span.start : span.end].strip() if span else None
    return texts


def _squash(normalized: str) -> str:
    return normalized.replace(" ", "")


def _verbatim(text: str, entry: str) -> bool:
    """Word for word after normalization, ignoring spacing: the source has glitches like
    "الثيببالثيب", and a quote that restores the space is still faithful. `entry` is normalized."""
    return bool(text.strip()) and _squash(normalize(text)) in _squash(entry)


def _extracted(
    matn: ChainMatn,
    by_chain: Mapping[int, ChainMatn],
    entries: Mapping[int, str],
    hadith_of: Mapping[int, int],
) -> tuple[str | None, TextSource]:
    """Quoted wording counts only if it occurs word for word in its entry; labels are advisory."""
    entry = entries.get(hadith_of.get(matn.chain_id, -1), "")
    if _verbatim(matn.matn_ar, entry):
        return matn.matn_ar.strip(), "extracted"
    source = by_chain.get(matn.same_as_chain_id) if matn.same_as_chain_id is not None else None
    if source is not None:
        source_entry = entries.get(hadith_of.get(source.chain_id, -1), "")
        if _verbatim(source.matn_ar, source_entry):
            return source.matn_ar.strip(), "inherited"
    return None, "missing"


def chain_texts(tradition: Tradition, extracted: Sequence[ChainMatn]) -> list[ChainText]:
    """Single-chain entries use the dataset's matn span; multi-chain entries use extractions."""
    spans = _span_text(tradition)
    multi = multi_chain_hadith_ids(tradition)
    by_chain = {m.chain_id: m for m in extracted}
    entries = {h.id: normalize(h.text_ar) for h in tradition.hadiths}
    hadith_of = {c.id: c.hadith_id for c in tradition.chains}
    result: list[ChainText] = []
    for chain in tradition.chains:
        matn = by_chain.get(chain.id)
        if chain.hadith_id in multi and matn is not None:
            text, source = _extracted(matn, by_chain, entries, hadith_of)
        else:
            text = spans.get(chain.hadith_id)
            source = "span" if text else "missing"
        result.append(ChainText(chain.id, chain.hadith_id, text, source))
    return result


def extraction_warnings(tradition: Tradition, extracted: Sequence[ChainMatn]) -> list[str]:
    """Quotes that are not in their entry, and relation labels that contradict the quote."""
    entries = {h.id: normalize(h.text_ar) for h in tradition.hadiths}
    hadith_of = {c.id: c.hadith_id for c in tradition.chains}
    warnings: list[str] = []
    for m in extracted:
        quoted = bool(m.matn_ar.strip())
        if quoted and not _verbatim(m.matn_ar, entries.get(hadith_of.get(m.chain_id, -1), "")):
            warnings.append(f"chain_matns: chain {m.chain_id} quote is not in its entry; ignored")
        if quoted != (m.relation in ("full_text", "partial_text")):
            warnings.append(
                f"chain_matns: chain {m.chain_id} relation '{m.relation}' contradicts its quote"
            )
    return warnings


def group_variants(texts: Sequence[ChainText]) -> list[Variant]:
    """Chains whose matns normalize to the same string share a variant. Largest first."""
    groups: dict[str, list[ChainText]] = defaultdict(list)
    for t in texts:
        if t.text_ar:
            groups[normalize(t.text_ar)].append(t)
    ordered = sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))
    return [
        Variant(f"V{i}", members[0].text_ar or "", tuple(sorted(m.chain_id for m in members)))
        for i, (_, members) in enumerate(ordered, start=1)
    ]
