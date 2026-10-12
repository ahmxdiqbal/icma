"""Isnad bundle: merge chains into one graph and compute the structural facts ICMA reasons over.

Everything here is deterministic. Judgements (is this CL genuine, is this dive a forgery) are left
to the analysis layer; this module only reports what the chains say.

Terms used below, for a node n and the chains passing through it:
  branch         the chains that go from n to one particular student.
  independent    two branches are dependent if they share any transmitter below n. Meeting only
                 at the final collector does not count: one compiler may hear from two lines.
  corroborated   an independent group of branches that splits again somewhere below n, so it
                 rests on more than one path.
  single strand  an independent group with exactly one path that passes through at least
                 MIN_STRAND_TRANSMITTERS transmitters before its collector. Shorter lines (a
                 collector's own teacher, or the collector himself) are ordinary attestations.
"""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from icma.models import Chain, GapLink, Link

PROPHET = "prophet"
MIN_STRAND_TRANSMITTERS = 2


@dataclass(frozen=True, slots=True)
class Path:
    """A chain as node keys, earliest authority first, collector last."""

    chain_id: int
    keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NodeStats:
    key: str
    chain_ids: tuple[int, ...]
    min_depth: int
    student_keys: tuple[str, ...]
    collector_keys: tuple[str, ...]
    independent_branch_count: int
    corroborated_branch_count: int
    single_strand_branch_count: int


@dataclass(frozen=True, slots=True)
class Edge:
    source: str
    target: str
    chain_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class Dive:
    """A chain that reaches an authority above the CL without passing through the CL."""

    chain_id: int
    departs_from: str
    rejoins_at: str | None


@dataclass(frozen=True, slots=True)
class UpperPath:
    """One distinct way the chains through the CL name the authorities above it."""

    labels: tuple[str, ...]
    chain_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class BundleWarning:
    code: str
    message: str
    chain_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class Bundle:
    paths: tuple[Path, ...]
    nodes: tuple[NodeStats, ...]
    edges: tuple[Edge, ...]
    cl_candidates: tuple[str, ...]
    suggested_cl: str | None
    spiders: tuple[str, ...]
    dives: tuple[Dive, ...]
    upper_paths: tuple[UpperPath, ...]
    warnings: tuple[BundleWarning, ...]


# ---------------------------------------------------------------- keys


def narrator_key(narrator_id: int) -> str:
    return f"n:{narrator_id}"


def gap_key(kind: str, chain_id: int, index: int) -> str:
    """Gaps are unique per chain position: two unnamed links are never the same person."""
    return f"g:{kind}:{chain_id}:{index}"


def is_person_key(key: str) -> bool:
    """Any identified transmitter: not the Prophet, not a gap."""
    return key != PROPHET and not key.startswith("g:")


def label_of(key: str) -> str:
    """Key with per-chain identity removed, for grouping paths that differ only by which gap."""
    return ":".join(key.split(":")[:2]) if key.startswith("g:") else key


def _link_key(link: Link, chain_id: int, index: int) -> str:
    if isinstance(link, GapLink):
        return gap_key(link.gap.value, chain_id, index)
    return narrator_key(link.narrator_id)


# ---------------------------------------------------------------- paths


def to_paths(
    chains: Iterable[Chain], prophetic_chain_ids: set[int]
) -> tuple[list[Path], list[BundleWarning]]:
    """Convert chains to key paths. Chains that repeat a narrator are excluded and reported."""
    paths: list[Path] = []
    warnings: list[BundleWarning] = []
    for chain in chains:
        keys = [PROPHET] if chain.id in prophetic_chain_ids else []
        keys += [_link_key(link, chain.id, i) for i, link in enumerate(chain.links)]
        if len(keys) < 2:
            warnings.append(
                BundleWarning("too_short", "chain has fewer than two nodes", (chain.id,))
            )
        elif len(set(keys)) != len(keys):
            warnings.append(
                BundleWarning(
                    "repeated_narrator", "a narrator appears twice in one chain", (chain.id,)
                )
            )
        else:
            paths.append(Path(chain.id, tuple(keys)))
    return paths, warnings


# ---------------------------------------------------------------- node statistics

Occurrence = tuple[Path, int]


def _occurrences(paths: Sequence[Path]) -> dict[str, list[Occurrence]]:
    occ: dict[str, list[Occurrence]] = defaultdict(list)
    for path in paths:
        for index, key in enumerate(path.keys):
            occ[key].append((path, index))
    return occ


def _find(parent: list[int], i: int) -> int:
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def _components(branch_sets: list[set[str]]) -> list[list[int]]:
    """Group branch indices whose key sets intersect (union-find over shared keys)."""
    parent = list(range(len(branch_sets)))
    owner: dict[str, int] = {}
    for i, keys in enumerate(branch_sets):
        for key in keys:
            if key in owner:
                parent[_find(parent, i)] = _find(parent, owner[key])
            else:
                owner[key] = i
    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(len(branch_sets)):
        groups[_find(parent, i)].append(i)
    return list(groups.values())


@dataclass(frozen=True, slots=True)
class BranchGroup:
    """One independent line below a node: the students it starts from and the chains in it."""

    student_keys: tuple[str, ...]
    chain_ids: tuple[int, ...]
    kind: str  # "corroborated", "single_strand", or "direct"


def _suffix(path: Path, index: int) -> tuple[str, ...]:
    return tuple(label_of(k) for k in path.keys[index + 1 :])


def _kind(suffixes: set[tuple[str, ...]]) -> str:
    if len(suffixes) >= 2:
        return "corroborated"
    if len(next(iter(suffixes))) > MIN_STRAND_TRANSMITTERS:
        return "single_strand"
    return "direct"


def _groups(occurrences: list[Occurrence]) -> list[BranchGroup]:
    """Split the chains below one node into independent groups."""
    by_student: dict[str, list[Occurrence]] = defaultdict(list)
    for path, index in occurrences:
        if index + 1 < len(path.keys):
            by_student[path.keys[index + 1]].append((path, index))
    students = sorted(by_student)
    # Transmitters strictly below the node, excluding each chain's final collector.
    shared = [{k for p, i in by_student[s] for k in p.keys[i + 1 : -1]} for s in students]
    groups: list[BranchGroup] = []
    for component in _components(shared):
        members = [occ for b in component for occ in by_student[students[b]]]
        groups.append(
            BranchGroup(
                student_keys=tuple(students[b] for b in component),
                chain_ids=tuple(sorted({p.chain_id for p, _ in members})),
                kind=_kind({_suffix(p, i) for p, i in members}),
            )
        )
    return sorted(groups, key=lambda g: (-len(g.chain_ids), g.student_keys))


def branch_groups(paths: Sequence[Path], key: str) -> list[BranchGroup]:
    """Independent lines below one node, largest first."""
    return _groups(_occurrences(paths).get(key, []))


def node_stats(paths: Sequence[Path]) -> list[NodeStats]:
    stats: list[NodeStats] = []
    for key, occ in _occurrences(paths).items():
        kinds = [g.kind for g in _groups(occ)]
        stats.append(
            NodeStats(
                key=key,
                chain_ids=tuple(sorted({p.chain_id for p, _ in occ})),
                min_depth=min(i for _, i in occ),
                student_keys=tuple(sorted({p.keys[i + 1] for p, i in occ if i + 1 < len(p.keys)})),
                collector_keys=tuple(sorted({p.keys[-1] for p, _ in occ})),
                independent_branch_count=len(kinds),
                corroborated_branch_count=kinds.count("corroborated"),
                single_strand_branch_count=kinds.count("single_strand"),
            )
        )
    return sorted(stats, key=lambda s: (s.min_depth, -len(s.chain_ids), s.key))


def edges_of(paths: Sequence[Path]) -> list[Edge]:
    """Teacher-to-student edges, each listing the chains that use it."""
    chain_ids: dict[tuple[str, str], set[int]] = defaultdict(set)
    for path in paths:
        for source, target in zip(path.keys, path.keys[1:], strict=False):
            chain_ids[(source, target)].add(path.chain_id)
    return [Edge(s, t, tuple(sorted(ids))) for (s, t), ids in sorted(chain_ids.items())]


# ---------------------------------------------------------------- CL, spiders, dives


def cl_candidates(stats: Sequence[NodeStats]) -> list[NodeStats]:
    """Narrators with at least two corroborated independent branches, most chains first."""
    found = [s for s in stats if is_person_key(s.key) and s.corroborated_branch_count >= 2]
    return sorted(found, key=lambda s: (-len(s.chain_ids), s.min_depth, s.key))


def key_figures(stats: Sequence[NodeStats]) -> list[NodeStats]:
    """Every transmitter with at least two independent branches, most chains first.

    Wider than cl_candidates: a figure whose students hand the text straight to collectors is
    a key figure here, as Motzki and Pavlovitch count it, though Juynboll's rule would not.
    """
    found = [s for s in stats if is_person_key(s.key) and s.independent_branch_count >= 2]
    return sorted(found, key=lambda s: (-len(s.chain_ids), s.min_depth, s.key))


def spiders(stats: Sequence[NodeStats]) -> list[str]:
    """Seeming CLs: two or more single strands fan out, and no branch splits again."""
    return [
        s.key
        for s in stats
        if is_person_key(s.key)
        and s.single_strand_branch_count >= 2
        and s.corroborated_branch_count == 0
    ]


def _above_and_below(paths: Sequence[Path], cl: str) -> tuple[set[str], set[str]]:
    above: set[str] = set()
    below: set[str] = set()
    for path in paths:
        if cl in path.keys:
            index = path.keys.index(cl)
            above.update(path.keys[:index])
            below.update(path.keys[index + 1 : -1])
    above.discard(PROPHET)
    return above, below


def dives(paths: Sequence[Path], cl: str) -> list[Dive]:
    above, below = _above_and_below(paths, cl)
    found: list[Dive] = []
    for path in paths:
        if cl in path.keys:
            continue
        shared = [i for i, k in enumerate(path.keys) if k in above]
        if not shared:
            continue
        depart = shared[-1]
        rejoin = next((k for k in path.keys[depart + 1 : -1] if k in below), None)
        found.append(Dive(path.chain_id, path.keys[depart], rejoin))
    return found


def upper_paths(paths: Sequence[Path], cl: str) -> list[UpperPath]:
    groups: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for path in paths:
        if cl in path.keys:
            labels = tuple(label_of(k) for k in path.keys[: path.keys.index(cl)])
            groups[labels].append(path.chain_id)
    ordered = sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))
    return [UpperPath(labels, tuple(sorted(ids))) for labels, ids in ordered]


def cycle_warnings(edges: Sequence[Edge]) -> list[BundleWarning]:
    """Report teacher/student pairs that occur in both directions across chains."""
    pairs = {(e.source, e.target): e.chain_ids for e in edges}
    found: list[BundleWarning] = []
    for (source, target), ids in pairs.items():
        reverse = pairs.get((target, source))
        if reverse is not None and source < target:
            found.append(
                BundleWarning(
                    "reversed_edge",
                    f"{source} and {target} appear as teacher and student of each other",
                    tuple(sorted({*ids, *reverse})),
                )
            )
    return found


# ---------------------------------------------------------------- assembly


def build_bundle(paths: Sequence[Path], warnings: Sequence[BundleWarning] = ()) -> Bundle:
    stats = node_stats(paths)
    edges = edges_of(paths)
    candidates = cl_candidates(stats)
    cl = candidates[0].key if candidates else None
    return Bundle(
        paths=tuple(paths),
        nodes=tuple(stats),
        edges=tuple(edges),
        cl_candidates=tuple(c.key for c in candidates),
        suggested_cl=cl,
        spiders=tuple(spiders(stats)),
        dives=tuple(dives(paths, cl)) if cl else (),
        upper_paths=tuple(upper_paths(paths, cl)) if cl else (),
        warnings=(*warnings, *cycle_warnings(edges)),
    )
