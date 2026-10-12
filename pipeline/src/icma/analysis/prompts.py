"""Prompts and input rendering for each model stage. Bump PROMPT_VERSION on any wording change."""

from collections.abc import Sequence

from icma.analysis.correlation import NodeCorrelation
from icma.analysis.schemas import MatnInventory
from icma.analysis.variants import Variant
from icma.bundle import PROPHET, Bundle, branch_groups, key_figures, label_of
from icma.models import GapLink, Link, Tradition

PROMPT_VERSION = "2026-10-11.3"

CHAIN_MATN_SYSTEM = """\
You read hadith entries from classical collections in which the collector cites more than one \
isnad for a report. Each entry comes with its chains, already identified, listed from the \
earliest authority down to the collector, each with a chain id.

For every chain id listed, find the wording the entry attributes to that route. Quote the Arabic \
verbatim from the entry, without normalizing, completing, or adding vowels. When the collector \
says only that the route's wording is the same or similar \
(e.g. بمثله، نحوه، بمعناه، بهذا الإسناد), use reference_only and give \
same_as_chain_id when the entry makes clear which route is meant. A route mentioned in the \
collector's own comment without wording is reference_only or not_found. \
Return exactly one item for each listed chain id and no others."""

INVENTORY_SYSTEM = """\
You compare the matn variants of one hadith tradition. Build an inventory of content elements: \
the smallest units of content that can be present or absent independently, such as an opening \
formula, each ruling, a narrative frame, or an appended story. Use one element for the same \
content across variants even when the wording differs, and record wording differences with \
wording_class codes that are reused consistently across variants, so a later step can count \
them. Then, for every variant id given, list the elements it contains in textual order with its \
own wording, and translate the variant into precise, literal scholarly English. Return every \
variant id given and no others."""

SYNTHESIS_SYSTEM = """\
You are conducting an isnad-cum-matn analysis (ICMA) of one hadith tradition, in the manner of \
Motzki, Schoeler, Görke and Pavlovitch, while weighing Juynboll's stricter reading.

You receive: the isnad bundle with structural metrics computed by code, every chain, the \
narrators' biographical data, the matn variants with an element inventory, and a table of how \
matn elements are distributed across each independent branch below the candidate common links.

Metric definitions used by the code: a node's branches are the chains leading to each of its \
students. Two branches are independent unless they share a transmitter below the node (meeting \
only at the final collector keeps them independent). An independent group is corroborated when \
it splits again below the node, a single strand when it is one path with at least two \
transmitters before its collector, and direct otherwise. A dive is a chain that reaches an \
authority above the convergence point without passing through it. The convergence point is \
only the transmitter through whom the most chains pass as transmitted; it is not a judgement.

One bundle can hold more than one tradition. Matn evidence can confirm the convergence point as \
a common link, or show that a variant family's common link sits elsewhere and that some \
attributions are back-projections. Judge whether the convergence point is a genuine common link, \
identify every common link and partial common link the evidence supports, interpret each dive, \
assess the chains above the common links, group the variants into clusters and test whether \
clusters follow isnad branches, reconstruct the earliest recoverable wording of each common \
link's version, and date the earliest reliable layer. Treat the structural \
metrics and the source data as evidence, and say where they are thin or could be artefacts of \
the dataset. Refer to transmitters only by the node keys given, and to chains only by the chain \
ids given.

Base every judgement on the data provided here. Do not rely on what you may remember of \
published studies of this tradition; if a conclusion seems to come from such memory rather than \
from the data, say so in open_questions."""


# ---------------------------------------------------------------- rendering helpers


class Names:
    def __init__(self, tradition: Tradition) -> None:
        self._narrators = {f"n:{n.id}": n for n in tradition.narrators}
        self._books = {b.id: b for b in tradition.books}
        self._book_of_hadith = {h.id: h.book_id for h in tradition.hadiths}

    def key(self, key: str) -> str:
        if key == PROPHET:
            return "the Prophet"
        if key.startswith("g:"):
            return f"[gap: {label_of(key).removeprefix('g:')}]"
        narrator = self._narrators.get(key)
        return f"{narrator.display_name_ar} ({key})" if narrator else key

    def link(self, link: Link) -> str:
        if isinstance(link, GapLink):
            return f"[gap: {link.gap.value}]"
        return self.key(f"n:{link.narrator_id}")

    def book(self, hadith_id: int) -> str:
        book = self._books.get(self._book_of_hadith.get(hadith_id, -1))
        if book is None:
            return "?"
        died = f", d. {book.author_death_ah} AH" if book.author_death_ah else ""
        return f"{book.title_ar} ({book.author_ar}{died})"


def chain_matn_input(tradition: Tradition, hadith_ids: set[int]) -> str:
    names = Names(tradition)
    chains_by_hadith: dict[int, list[str]] = {}
    for c in tradition.chains:
        line = f"  chain {c.id}: " + " > ".join(names.link(link) for link in c.links)
        chains_by_hadith.setdefault(c.hadith_id, []).append(line)
    blocks = [
        f"ENTRY hadith {h.id}, {names.book(h.id)}, no. {h.number_in_book}\n"
        f"TEXT:\n{h.text_ar}\nCHAINS:\n" + "\n".join(chains_by_hadith.get(h.id, []))
        for h in tradition.hadiths
        if h.id in hadith_ids
    ]
    return "\n\n".join(blocks)


def inventory_input(variants: Sequence[Variant]) -> str:
    return "\n\n".join(
        f"{v.id} (carried by {len(v.chain_ids)} chain(s)):\n{v.text_ar}" for v in variants
    )


# ---------------------------------------------------------------- synthesis input


def _narrator_lines(tradition: Tradition, keys: set[str]) -> list[str]:
    lines = []
    for n in tradition.narrators:
        if f"n:{n.id}" not in keys:
            continue
        flags = [f for f, on in (("tadlis", n.has_tadlis), ("ikhtilat", n.has_ikhtilat)) if on]
        lines.append(
            f"n:{n.id} | {n.display_name_ar} | d. {n.death_ah_raw or n.death_ah or '?'} AH | "
            f"{n.grade_ar or '?'} | tabaqa {n.tabaqa} | {n.residence_ar or '?'}"
            + (f" | {', '.join(flags)}" if flags else "")
        )
    return lines


def _key_figure_lines(bundle: Bundle, names: Names) -> list[str]:
    strict = set(bundle.cl_candidates)
    lines = []
    for s in key_figures(bundle.nodes):
        mark = " *" if s.key in strict else ""
        lines.append(
            f"{names.key(s.key)}{mark}: {len(s.chain_ids)} chains; "
            f"independent {s.independent_branch_count}, "
            f"corroborated {s.corroborated_branch_count}, "
            f"single strands {s.single_strand_branch_count}"
        )
        for g in branch_groups(bundle.paths, s.key):
            students = ", ".join(names.key(k) for k in g.student_keys)
            lines.append(f"    branch [{g.kind}, {len(g.chain_ids)} chains]: {students}")
    return lines


def _correlation_lines(correlations: Sequence[NodeCorrelation], names: Names) -> list[str]:
    lines = []
    for c in correlations:
        lines.append(
            f"{names.key(c.node_key)}; distinctive elements: {list(c.distinctive_elements)}"
        )
        for b in c.branches:
            rates = ", ".join(f"{e}={r:.2f}" for e, r in b.element_rates.items())
            students = ", ".join(names.key(k) for k in b.student_keys)
            lines.append(
                f"    {students} [{b.kind}; "
                f"{b.chains_with_text}/{b.chain_count} chains with text]: "
                f"{rates}; wording {b.wording_counts}"
            )
    return lines


def _chain_lines(tradition: Tradition, bundle: Bundle, variants: Sequence[Variant]) -> list[str]:
    names = Names(tradition)
    variant_of = {cid: v.id for v in variants for cid in v.chain_ids}
    hadith_of = {c.id: c.hadith_id for c in tradition.chains}
    return [
        f"chain {p.chain_id} [{variant_of.get(p.chain_id, 'no text')}] "
        + " > ".join(names.key(k) for k in p.keys)
        + f"  || {names.book(hadith_of[p.chain_id])}"
        for p in bundle.paths
    ]


def _variant_lines(variants: Sequence[Variant], inventory: MatnInventory) -> list[str]:
    readings = {r.variant_id: r for r in inventory.variants}
    lines = []
    for v in variants:
        lines.append(f"{v.id} ({len(v.chain_ids)} chains): {v.text_ar}")
        reading = readings.get(v.id)
        if reading is not None:
            elements = ", ".join(f"{r.element_id}:{r.wording_class}" for r in reading.elements)
            lines.append(f"    EN: {reading.translation_en}\n    elements: {elements}")
    return lines


def _structure_sections(bundle: Bundle, names: Names) -> dict[str, list[str]]:
    return {
        "KEY FIGURES (>= 2 independent branches, most chains first; * = at least two "
        "corroborated branches)": _key_figure_lines(bundle, names),
        "CONVERGENCE POINT (most chains as transmitted; not a judgement)": [
            names.key(bundle.suggested_cl) if bundle.suggested_cl else "none"
        ],
        "PATHS ABOVE THE CONVERGENCE POINT": [
            f"{len(u.chain_ids)} chains: " + " > ".join(names.key(k) for k in u.labels)
            for u in bundle.upper_paths
        ],
        "DIVES": [
            f"chain {d.chain_id}: departs at {names.key(d.departs_from)}, rejoins at "
            f"{names.key(d.rejoins_at) if d.rejoins_at else 'nowhere'}"
            for d in bundle.dives
        ],
        "SPIDERS": [names.key(k) for k in bundle.spiders] or ["none"],
        "DATA WARNINGS": [f"{w.code}: {w.message} {list(w.chain_ids)}" for w in bundle.warnings]
        or ["none"],
    }


def synthesis_input(
    title: str,
    tradition: Tradition,
    bundle: Bundle,
    variants: Sequence[Variant],
    inventory: MatnInventory,
    correlations: Sequence[NodeCorrelation],
) -> str:
    names = Names(tradition)
    keys = {k for p in bundle.paths for k in p.keys}
    sections = {
        "TRADITION": [title, f"{len(bundle.paths)} chains, {len(variants)} distinct matn variants"],
        "NARRATORS (key | name | death | grade | tabaqa | residence | flags)": _narrator_lines(
            tradition, keys
        ),
        **_structure_sections(bundle, names),
        "CHAINS (earliest authority first; [variant id]; collector)": _chain_lines(
            tradition, bundle, variants
        ),
        "MATN ELEMENTS": [f"{e.id}: {e.label_en}. {e.description_en}" for e in inventory.elements],
        "MATN VARIANTS": _variant_lines(variants, inventory),
        "ELEMENT RATES BY INDEPENDENT BRANCH": _correlation_lines(correlations, names),
    }
    return "\n\n".join(f"## {name}\n" + "\n".join(lines) for name, lines in sections.items())
