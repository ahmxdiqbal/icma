"""Serialize a tradition and its bundle into the JSON package the web app reads.

Schema version 1. Text offsets are Unicode code point indices into text_ar.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from icma.bundle import PROPHET, Bundle, BundleWarning, Dive, Edge, NodeStats, UpperPath
from icma.corrections import Correction
from icma.models import Book, Chain, GapLink, Hadith, Link, Narrator, Tradition

SCHEMA_VERSION = 1
JSON = dict[str, object]


@dataclass(frozen=True, slots=True)
class PackageMeta:
    id: str
    title_en: str
    group_id: int
    anchor_narrator_ids: tuple[int, ...]


SOURCE = {
    "dataset": "hadith-kg",
    "url": "https://huggingface.co/datasets/emadjumaah/hadith-kg",
    "license": "CC BY 4.0",
    "attribution": "Emad Jumaah, Hadith Knowledge Graph (2026)",
}


def _book(b: Book) -> JSON:
    return {
        "id": b.id,
        "title_ar": b.title_ar,
        "author_ar": b.author_ar,
        "author_death_ah": b.author_death_ah,
        "category_ar": b.category_ar,
        "edition": {
            "publisher_ar": b.publisher_ar,
            "city_ar": b.city_ar,
            "printing_ar": b.printing_ar,
        },
    }


def _narrator(n: Narrator) -> JSON:
    return {
        "id": n.id,
        "name_ar": n.name_ar,
        "display_name_ar": n.display_name_ar,
        "tabaqa": n.tabaqa,
        "grade_code": n.grade_code,
        "grade_ar": n.grade_ar,
        "death_ah": n.death_ah,
        "death_ah_raw": n.death_ah_raw,
        "residence_ar": n.residence_ar,
        "has_tadlis": n.has_tadlis,
        "has_ikhtilat": n.has_ikhtilat,
        "in_bukhari": n.in_bukhari,
        "in_muslim": n.in_muslim,
        "is_stub": n.is_stub,
    }


def _hadith(h: Hadith) -> JSON:
    return {
        "id": h.id,
        "book_id": h.book_id,
        "number_in_book": h.number_in_book,
        "page": h.page,
        "type": h.type.value,
        "grade_ar": h.grade_ar,
        "text_ar": h.text_ar,
        "matn_span": [h.matn_span.start, h.matn_span.end] if h.matn_span else None,
        "mentions": [
            {"start": m.span.start, "end": m.span.end, "narrator_id": m.narrator_id}
            for m in h.mentions
        ],
        "translation_en": None,
        "translation_source": None,
    }


def _link(link: Link) -> JSON:
    if isinstance(link, GapLink):
        return {"kind": "gap", "gap": link.gap.value}
    return {"kind": "narrator", "narrator_id": link.narrator_id}


def _chain(c: Chain, in_bundle: bool) -> JSON:
    return {
        "id": c.id,
        "hadith_id": c.hadith_id,
        "grade_ar": c.grade_ar,
        "in_bundle": in_bundle,
        "links": [_link(link) for link in c.links],
    }


def _node(s: NodeStats) -> JSON:
    base: JSON = {"key": s.key}
    if s.key == PROPHET:
        base |= {"kind": "prophet"}
    elif s.key.startswith("g:"):
        base |= {"kind": "gap", "gap": s.key.split(":")[1]}
    else:
        base |= {"kind": "narrator", "narrator_id": int(s.key.removeprefix("n:"))}
    return base | {
        "chain_ids": list(s.chain_ids),
        "min_depth": s.min_depth,
        "student_keys": list(s.student_keys),
        "collector_keys": list(s.collector_keys),
        "independent_branch_count": s.independent_branch_count,
        "corroborated_branch_count": s.corroborated_branch_count,
        "single_strand_branch_count": s.single_strand_branch_count,
    }


def _edge(e: Edge) -> JSON:
    return {"source": e.source, "target": e.target, "chain_ids": list(e.chain_ids)}


def _dive(d: Dive) -> JSON:
    return {"chain_id": d.chain_id, "departs_from": d.departs_from, "rejoins_at": d.rejoins_at}


def _upper(u: UpperPath) -> JSON:
    return {"labels": list(u.labels), "chain_ids": list(u.chain_ids)}


def _warning(w: BundleWarning) -> JSON:
    return {"code": w.code, "message": w.message, "chain_ids": list(w.chain_ids)}


def _correction(c: Correction) -> JSON:
    return {
        "chain_id": c.chain_id,
        "op": c.op,
        "from_narrator_id": c.from_narrator_id,
        "to_narrator_id": c.to_narrator_id,
        "links": [_link(link) for link in c.links] if c.links is not None else None,
        "reason": c.reason,
        "evidence": c.evidence,
        "author": c.author,
        "date": c.date,
    }


def bundle_json(b: Bundle) -> JSON:
    return {
        "root": PROPHET,
        "nodes": [_node(s) for s in b.nodes],
        "edges": [_edge(e) for e in b.edges],
        "cl_candidates": list(b.cl_candidates),
        "suggested_cl": b.suggested_cl,
        "spiders": list(b.spiders),
        "dives": [_dive(d) for d in b.dives],
        "upper_paths": [_upper(u) for u in b.upper_paths],
        "warnings": [_warning(w) for w in b.warnings],
    }


def package_json(
    meta: PackageMeta,
    tradition: Tradition,
    bundle: Bundle,
    corrections: Sequence[Correction],
    generated_at: datetime | None = None,
) -> JSON:
    bundled = {p.chain_id for p in bundle.paths}
    return {
        "schema_version": SCHEMA_VERSION,
        "id": meta.id,
        "title_en": meta.title_en,
        "generated_at": (generated_at or datetime.now(UTC)).isoformat(timespec="seconds"),
        "source": SOURCE
        | {
            "selection": {
                "group_id": meta.group_id,
                "anchor_narrator_ids": list(meta.anchor_narrator_ids),
            }
        },
        "corrections_applied": [_correction(c) for c in corrections],
        "books": [_book(b) for b in tradition.books],
        "narrators": [_narrator(n) for n in tradition.narrators],
        "hadiths": [_hadith(h) for h in tradition.hadiths],
        "chains": [_chain(c, c.id in bundled) for c in tradition.chains],
        "bundle": bundle_json(bundle),
    }
