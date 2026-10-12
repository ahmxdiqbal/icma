"""Isnad-matn correlation: does each independent branch below a node carry its own matn profile?"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from icma.analysis.schemas import MatnInventory
from icma.analysis.variants import Variant
from icma.bundle import BranchGroup


@dataclass(frozen=True, slots=True)
class BranchProfile:
    student_keys: tuple[str, ...]
    kind: str
    chain_count: int
    chains_with_text: int
    element_rates: dict[str, float]
    wording_counts: dict[str, dict[str, int]]


@dataclass(frozen=True, slots=True)
class NodeCorrelation:
    node_key: str
    branches: tuple[BranchProfile, ...]
    distinctive_elements: tuple[str, ...]


DISTINCTIVE_GAP = 0.5


def _variant_by_chain(variants: Sequence[Variant]) -> dict[int, str]:
    return {chain_id: v.id for v in variants for chain_id in v.chain_ids}


def branch_profile(
    group: BranchGroup, variant_of: dict[int, str], inventory: MatnInventory
) -> BranchProfile:
    readings = {v.variant_id: v for v in inventory.variants}
    present: Counter[str] = Counter()
    wording: dict[str, Counter[str]] = {e.id: Counter() for e in inventory.elements}
    with_text = 0
    for chain_id in group.chain_ids:
        reading = readings.get(variant_of.get(chain_id, ""))
        if reading is None:
            continue
        with_text += 1
        for r in reading.elements:
            present[r.element_id] += 1
            wording.setdefault(r.element_id, Counter())[r.wording_class] += 1
    rates = {e.id: (present[e.id] / with_text if with_text else 0.0) for e in inventory.elements}
    return BranchProfile(
        student_keys=group.student_keys,
        kind=group.kind,
        chain_count=len(group.chain_ids),
        chains_with_text=with_text,
        element_rates=rates,
        wording_counts={k: dict(c) for k, c in wording.items() if c},
    )


def distinctive(profiles: Sequence[BranchProfile], element_ids: Sequence[str]) -> list[str]:
    """Elements whose presence rate differs by at least DISTINCTIVE_GAP between two branches."""
    usable = [p for p in profiles if p.chains_with_text > 0]
    found: list[str] = []
    for element in element_ids:
        rates = [p.element_rates[element] for p in usable]
        if len(rates) >= 2 and max(rates) - min(rates) >= DISTINCTIVE_GAP:
            found.append(element)
    return found


def correlate(
    node_key: str,
    groups: Sequence[BranchGroup],
    variants: Sequence[Variant],
    inventory: MatnInventory,
) -> NodeCorrelation:
    variant_of = _variant_by_chain(variants)
    profiles = [branch_profile(g, variant_of, inventory) for g in groups]
    elements = [e.id for e in inventory.elements]
    return NodeCorrelation(node_key, tuple(profiles), tuple(distinctive(profiles, elements)))
