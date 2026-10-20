"""The wording each chain of a hadith entry carries, found by rules. See docs/chain-wording.md.

An entry interleaves isnads, wordings and the collector's formulas. Each chain is aligned to the
narrator mentions in the text. The text after the chain's isnad is its tail: a wording, a formula
pointing at another chain's wording, or nothing. A chain with nothing after it joins the next
isnad (a tahwil), or, after a wording, is a citation. All matching runs on normalized text; spans
point into the source.
"""

import re
from bisect import bisect_left
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Literal

from icma.analysis import wording_vocab as v
from icma.arabic import is_diacritic, normalize, normalize_with_offsets
from icma.models import Chain, Hadith, NarratorLink, Span

Basis = Literal[
    "own", "shared", "lafz", "same", "similar", "meaning", "partial", "reference", "none"
]
COMPLETE: frozenset[str] = frozenset({"own", "shared", "lafz"})
FormulaKind = Literal["isnad", "same", "similar", "meaning", "reference"]


@dataclass(frozen=True, slots=True)
class ChainWording:
    chain_id: int
    basis: Basis
    span: Span | None  # complete wording for own/shared/lafz, the quoted part for partial
    refers_to: int | None  # chain whose complete wording a formula or partial points at
    formula: str  # the collector's words linking this chain to another, verbatim, or ""


_FORMULAS: tuple[tuple[re.Pattern[str], FormulaKind, bool], ...] = tuple(
    (re.compile(p + v.END), kind, named)  # type: ignore[misc]
    for p, kind, named in v.FORMULA_SOURCES
)
_GAP_PENALTY = 0.01
_SKIP_PENALTY = 0.05
_LEAD_PENALTY = 1.0
_NAME_WORDS = 6
_DESCRIPTOR_WORDS = 3
_COMMENT_REACH = 30  # characters after a cited chain's words that may show they are a comment


# ---------------------------------------------------------------- text with offset maps


@dataclass(frozen=True, slots=True)
class _Text:
    raw: str
    norm: str
    offsets: tuple[int, ...]

    @classmethod
    def of(cls, raw: str) -> "_Text":
        norm, offsets = normalize_with_offsets(raw)
        return cls(raw, norm, offsets)

    def pos(self, raw_index: int) -> int:
        """Normalized position of the first character at or after `raw_index`."""
        return bisect_left(self.offsets, raw_index)

    def trim(self, start: int, end: int) -> tuple[int, int]:
        while start < end and self.norm[start] == " ":
            start += 1
        while end > start and self.norm[end - 1] == " ":
            end -= 1
        return start, end

    def raw_span(self, start: int, end: int) -> Span | None:
        """Source span of norm[start:end], keeping the last letter's diacritics."""
        start, end = self.trim(start, end)
        if start >= end:
            return None
        raw_end = self.offsets[end - 1] + 1
        while raw_end < len(self.raw) and is_diacritic(self.raw[raw_end]):
            raw_end += 1
        return Span(self.offsets[start], raw_end)

    def raw_text(self, start: int, end: int) -> str:
        span = self.raw_span(start, end)
        return self.raw[span.start : span.end] if span else ""

    def raw_between(self, start: int, end: int) -> str:
        """Source characters between normalized positions, punctuation included."""
        if start <= 0 or end >= len(self.offsets):
            return ""
        return self.raw[self.offsets[start - 1] + 1 : self.offsets[end]]

    def words(self, start: int, end: int) -> list[tuple[int, str]]:
        """(position, word) for the words of norm[start:end]; a cut first word counts from start."""
        return [(start + m.start(), m.group()) for m in re.finditer(r"[^ ]+", self.norm[start:end])]


def _is_glue(word: str) -> bool:
    """Transmission words, and editors' numbers such as the '/18' around an unnamed narrator."""
    return word in v.GLUE or (word.startswith("و") and word[1:] in v.GLUE) or word.isdigit()


@dataclass(frozen=True, slots=True)
class _Mention:
    start: int  # normalized
    end: int
    narrator_id: int | None
    words: tuple[str, ...]


def _mentions(hadith: Hadith, text: _Text) -> list[_Mention]:
    found = []
    for m in sorted(hadith.mentions, key=lambda m: m.span.start):
        start, end = text.trim(text.pos(m.span.start), text.pos(m.span.end))
        found.append(_Mention(start, end, m.narrator_id, tuple(text.norm[start:end].split())))
    return found


# ---------------------------------------------------------------- aligning chains to mentions


def _narrators(chain: Chain) -> list[int]:
    """Collector's teacher first, back to the earliest authority; gaps dropped."""
    return [
        link.narrator_id for link in reversed(chain.links[:-1]) if isinstance(link, NarratorLink)
    ]


def _walls(text: _Text, mentions: Sequence[_Mention]) -> tuple[int, ...]:
    """Running count of walls: gaps between adjacent mentions that hold a wording or a formula.
    walls[i] - walls[j] counts the walls between mentions j and i."""
    counts = [0]
    for a, b in pairwise(mentions):
        gap = text.norm[a.end : b.start]
        loose = [w for w in gap.split() if not _is_glue(w)]
        counts.append(counts[-1] + (bool(v.WALL.search(gap)) or len(loose) > v.MAX_LOOSE_WORDS))
    return tuple(counts)


def _align(
    ids: Sequence[int],
    mentions: Sequence[_Mention],
    weight: Mapping[int, float],
    walls: Sequence[int],
) -> tuple[int, ...]:
    """Mention indices for the chain's narrators, in order, maximizing weighted matches.

    A narrator found in fewer of the entry's chains weighs more, so a chain is placed where its
    own narrators are. A chain starts at its first narrator when the text names him. It crosses a
    wall only to the next mention and narrator, or by resuming at its last narrator when he is
    named first after the wall ("قال سفيان: ثم لقيت فلانا فحدثنيه")."""
    mentioned = {m.narrator_id for m in mentions}
    best: dict[tuple[int, int], tuple[float, tuple[int, ...]]] = {}
    for j, nid in enumerate(ids):
        lead_skips = sum(1 for n in ids[:j] if n in mentioned)
        for i, mention in enumerate(mentions):
            if mention.narrator_id != nid:
                continue
            score = weight[nid] - _LEAD_PENALTY * lead_skips
            path: tuple[int, ...] = (i,)
            for (pj, pi), (prev, prev_path) in best.items():
                if pi >= i or pj > j:
                    continue
                if pj == j:  # the same narrator named again
                    if not _resumes(i, pi, walls):
                        continue
                    gain = 0.0
                elif _may_step(j, i, pj, pi, walls):
                    skips = _GAP_PENALTY * (i - pi - 1) + _SKIP_PENALTY * (j - pj - 1)
                    gain = weight[nid] - skips
                else:
                    continue
                if prev + gain > score:
                    score, path = prev + gain, (*prev_path, i)
            best[(j, i)] = (score, path)
    if not best:
        return ()
    return max(best.values(), key=lambda s: s[0])[1]


def _may_step(j: int, i: int, pj: int, pi: int, walls: Sequence[int]) -> bool:
    return walls[i] == walls[pi] or (i == pi + 1 and j == pj + 1)


def _resumes(i: int, pi: int, walls: Sequence[int]) -> bool:
    """Mention i names the same narrator as pi again, first after a wall."""
    return walls[i] != walls[i - 1] and walls[i] != walls[pi]


# ---------------------------------------------------------------- reading a tail


@dataclass(frozen=True, slots=True)
class _Formula:
    kind: FormulaKind
    start: int
    end: int
    name: tuple[str, ...]


@dataclass(slots=True)
class _Tail:
    start: int
    end: int
    wording: tuple[int, int] | None = None  # complete wording, or the quoted part of a partial
    partial: bool = False
    formulas: list[_Formula] = field(default_factory=list)
    joins: bool = False  # nothing here, and another isnad follows: ح, وحدثنا
    cited: bool = False  # nothing here, after a wording: the chain is only cited

    @property
    def empty(self) -> bool:
        return self.wording is None and not self.formulas

    @property
    def complete(self) -> bool:
        return self.wording is not None and not self.partial

    @property
    def kind(self) -> FormulaKind | None:
        for kind in ("same", "similar", "meaning", "reference"):
            if any(f.kind == kind for f in self.formulas):
                return kind
        return "isnad" if self.formulas else None


def _skip(text: _Text, pos: int, end: int, pattern: re.Pattern[str]) -> int:
    """Position of the next word after `pattern`, if it matches at `pos`."""
    pos = text.trim(pos, end)[0]
    m = pattern.match(text.norm, pos, end)
    return text.trim(m.end(), end)[0] if m else pos


def _after_link(text: _Text, pos: int, end: int) -> int:
    """Skip the link to the Prophet; keep a closing قال that has no colon and an addressee:
    'أن النبي ﷺ قال لمعاوية' keeps 'قال لمعاوية'."""
    m = v.LINK.match(text.norm, text.trim(pos, end)[0], end)
    if m is None:
        return pos
    after = text.trim(m.end(), end)[0]
    verb = (m.group("verb") or "").strip()
    addressed = text.norm.startswith("ل", after) and ":" not in text.raw_between(m.end(), after)
    if verb in ("قال", "فقال") and addressed:
        return text.trim(m.start("verb"), end)[0]
    return after


def _wording_start(text: _Text, pos: int, end: int) -> int:
    """Skip blessings, epithets and notes on the last narrator, and the link to the Prophet."""
    for pattern in (v.HONORIFIC, v.EPITHET, v.GLOSS):
        pos = _skip(text, pos, end, pattern)
    linked = _after_link(text, pos, end)
    return linked if linked != pos else _skip(text, pos, end, v.SAYS)


def _name_after(text: _Text, pos: int, end: int) -> tuple[tuple[str, ...], int]:
    found: list[str] = []
    for start, word in text.words(pos, end)[:_NAME_WORDS]:
        if word in v.NAME_STOP:
            break
        found.append(word)
        pos = start + len(word)
    return tuple(found), pos


def _formula_at(text: _Text, pos: int, end: int) -> _Formula | None:
    pos = text.trim(pos, end)[0]
    at = _skip(text, pos, end, v.LEAD)
    verb = v.VERB.match(text.norm, at, end)
    at = text.trim(verb.end(), end)[0] if verb else at
    for pattern, kind, named in _FORMULAS:
        m = pattern.match(text.norm, at, end)
        if m is None:
            continue
        if not named:
            return _Formula(kind, pos, m.end(), ())
        name, name_end = _name_after(text, m.end(), end)
        if name:
            return _Formula(kind, pos, name_end, name)
    if verb and verb.group("obj"):  # "فذكره": he cited it, no wording
        return _Formula("reference", pos, verb.end(), ())
    return None


def _formulas_from(text: _Text, pos: int, end: int) -> tuple[list[_Formula], int]:
    found: list[_Formula] = []
    while True:
        linked = _after_link(text, pos, end)
        formula = _formula_at(text, linked, end)
        if formula is None:
            return found, linked if found else pos
        found.append(formula)
        pos = formula.end


def _joins(text: _Text, start: int) -> bool:
    """Another isnad starts here: only transmission words before a ح or a 'حدثنا'."""
    for pos, word in text.words(start, min(len(text.norm), start + 80)):
        if word == "ح" or v.ISNAD_VERB.match(text.norm, pos):
            return True
        if not _is_glue(word):
            return False
    return False


def _read_tail(text: _Text, start: int, end: int) -> _Tail:
    tail = _Tail(start, end)
    pos = _wording_start(text, start, end)
    tail.formulas, pos = _formulas_from(text, pos, end)
    if tail.formulas:
        _read_quoted(text, tail, pos, end)
        return tail
    wording = text.trim(pos, end)
    if wording[0] >= wording[1]:
        tail.joins = _joins(text, start)
        return tail
    trailing = v.TRAILING.search(text.norm, wording[0] + 1, wording[1])
    formulas = _formulas_from(text, trailing.end(), wording[1])[0] if trailing else []
    if trailing and formulas:
        tail.formulas = formulas
        tail.wording, tail.partial = text.trim(wording[0], trailing.start()), True
    else:
        tail.wording = wording
    return tail


def _read_quoted(text: _Text, tail: _Tail, pos: int, end: int) -> None:
    """Words after a formula are this chain's own only when introduced as such ('غير أن ...',
    'قال: ...'); after مثله, نحوه or بمعناه anything else is the collector's comment. Words
    that start another isnad ('وسمعت فلانا') are not quoted words."""
    pos = text.trim(pos, end)[0]
    led = _skip(text, _skip(text, pos, end, v.PARTIAL_LEAD), end, v.PARTIAL_LEAD)
    if led == pos and tail.kind in ("same", "similar", "meaning"):
        return
    rest = text.trim(led, end)
    first = text.words(rest[0], rest[1])[:1]
    if rest[0] < rest[1] and not (first and _is_glue(first[0][1])):
        tail.wording, tail.partial = rest, True


# ---------------------------------------------------------------- boundaries


def _back_off(text: _Text, pos: int, floor: int) -> int:
    """Move left over the transmission words that introduce an isnad starting at `pos`."""
    for start, word in reversed(text.words(floor, pos)):
        bare = word[1:] if word.startswith("و") and len(word) > 1 else word
        if word not in v.BACKOFF and bare not in v.BACKOFF:
            break
        pos = start
    return pos


def _boundary(text: _Text, start: int, after: int, anchors: Sequence[int]) -> int:
    """Where the text from `start` stops being a tail: the next isnad (a narrator any chain
    passes through, after `after`), a transmission verb, or the collector's comment."""
    later = [a for a in anchors if a >= after]
    candidates = [len(text.norm)]
    candidates += [_back_off(text, min(later), start)] if later else []
    for pattern, backs_off in ((v.ISNAD_VERB, True), (v.COMMENTARY, False)):
        m = pattern.search(text.norm, start)
        if m:
            candidates.append(_back_off(text, m.end(), start) if backs_off else m.end())
    return max(start, min(candidates))


# ---------------------------------------------------------------- the entry


@dataclass(slots=True)
class _Group:
    tail: _Tail
    chains: list[int]  # chain ids, in text order of their isnads


class _Entry:
    def __init__(
        self,
        hadith: Hadith,
        chains: Sequence[Chain],
        names: Mapping[int, Sequence[str]] | None = None,
    ) -> None:
        self.text = _Text.of(hadith.text_ar)
        self.names = {
            nid: [tuple(normalize(n).split()) for n in known]
            for nid, known in (names or {}).items()
        }
        self.mentions = _mentions(hadith, self.text)
        self.ids = {c.id: _narrators(c) for c in chains}
        counts = Counter(n for ids in self.ids.values() for n in set(ids))
        weight = {n: 1 / counts[n] for n in counts}
        walls = _walls(self.text, self.mentions)
        self.paths = {
            cid: _align(ids, self.mentions, weight, walls) for cid, ids in self.ids.items()
        }
        self.anchors = sorted({self.mentions[i].start for p in self.paths.values() for i in p})
        self.groups = self._groups()

    def start_of(self, cid: int) -> int:
        path = self.paths[cid]
        return self.mentions[path[0]].start if path else len(self.text.norm)

    def _isnad_end(self, path: tuple[int, ...]) -> tuple[int, int]:
        """(tail start, end of the last narrator): extended over unidentified narrators the
        isnad continues with ('أخبرني عمومتي من الأنصار'), and moved back to where a story
        starts when the last narrator is named inside it ('قال: كنت عند ابن عمر')."""
        last = path[-1]
        while last + 1 < len(self.mentions) and self.mentions[last + 1].narrator_id is None:
            gap = self.text.norm[self.mentions[last].end : self.mentions[last + 1].start]
            if not all(_is_glue(w) for w in gap.split()):
                break
            last += 1
        end = self.mentions[last].end
        story = self._story_start(path[-1]) if last == path[-1] and path[-1] > 0 else None
        return (story if story is not None else end), end

    def _story_start(self, i: int) -> int | None:
        """Start of the story naming mention i, if one comes between him and the narrator
        before: 'قال: كنت عند ابن عمر' gives 'كنت'. A short run of words followed by
        transmission words describes a narrator ('ابن أخي بني رقاش عن', 'من أهل مصر قال')."""
        gap = self.text.words(self.mentions[i - 1].end, self.mentions[i].start)
        k = 0
        while k < len(gap):
            if _is_glue(gap[k][1]):
                k += 1
                continue
            run = next((m for m in range(k, len(gap)) if _is_glue(gap[m][1])), len(gap))
            if run == len(gap) or run - k > _DESCRIPTOR_WORDS:
                return gap[k][0] if k > 0 else None
            k = run
        return None

    def _groups(self) -> list[_Group]:
        ends: dict[tuple[int, int], list[int]] = {}
        for cid in sorted(self.paths, key=self.start_of):
            if self.paths[cid]:
                ends.setdefault(self._isnad_end(self.paths[cid]), []).append(cid)
        groups = [
            _Group(
                _read_tail(self.text, start, _boundary(self.text, start, end, self.anchors)), cids
            )
            for (start, end), cids in sorted(ends.items())
        ]
        return _join_empty(groups)

    def chains_through(self, mention_index: int) -> list[int]:
        on_path = [cid for cid, path in self.paths.items() if mention_index in path]
        narrator = self.mentions[mention_index].narrator_id
        return on_path or [cid for cid, ids in self.ids.items() if narrator in ids]

    def mention_named(self, name: Sequence[str], before: int) -> tuple[int, int] | None:
        """(mention index, words used) for the longest prefix of `name` naming a mention."""
        for size in range(len(name), 0, -1):
            part = name[:size]
            if size == 1 and _fold(part[0]) in ("بن", "ابو", "ابي"):
                continue
            hits = [
                i for i, m in enumerate(self.mentions) if m.start < before and self._is(part, m)
            ]
            if hits:
                return hits[-1], size
        return None

    def _is(self, name: Sequence[str], mention: _Mention) -> bool:
        """The mention's words or the narrator's full name contain `name`."""
        known = self.names.get(mention.narrator_id or -1, [])
        return _names(name, mention.words) or any(_names(name, full) for full in known)

    def introduced_by_addition(self, cid: int) -> bool:
        """The chain is cited for what it adds: 'وزاد الليث ...'."""
        start = self.start_of(cid)
        lead = self.text.words(_back_off(self.text, start, 0), start)
        return any(w in ("زاد", "وزاد") for _, w in lead)


def _join_empty(groups: list[_Group]) -> list[_Group]:
    """An isnad followed by another isnad shares what follows that one (tahwil). After a
    wording, an isnad followed by nothing is a citation."""
    joined: list[_Group] = []
    carried: list[int] = []
    seen_wording = False
    for group in groups:
        if group.tail.empty and (group.tail.joins or not seen_wording):
            carried += group.chains
            continue
        group.tail.cited = group.tail.empty
        joined.append(_Group(group.tail, carried + group.chains))
        carried = []
        seen_wording = seen_wording or group.tail.complete or group.tail.partial
    if carried:
        end = groups[-1].tail.end
        joined.append(_Group(_Tail(end, end, cited=seen_wording), carried))
    return joined


def _fold(word: str) -> str:
    return "بن" if word == "ابن" else word


def _names(name: Sequence[str], words: Sequence[str]) -> bool:
    """True if `name` occurs as consecutive words of a mention ("ابن جعفر" in "محمد بن جعفر")."""

    def same(a: str, b: str) -> bool:
        return _fold(a) == _fold(b) or (b.startswith("و") and _fold(a) == _fold(b[1:]))

    size = len(name)
    return any(
        all(same(name[k], words[i + k]) for k in range(size)) for i in range(len(words) - size + 1)
    )


# ---------------------------------------------------------------- assigning wordings


def extract_wordings(
    hadith: Hadith, chains: Sequence[Chain], names: Mapping[int, Sequence[str]] | None = None
) -> list[ChainWording]:
    """One record per chain of the entry, in the order given. `names` (narrator id to his
    known names) lets the collector's 'لفظ الحماني' find Yahya b. 'Abd al-Hamid al-Himmani."""
    entry = _Entry(hadith, chains, names)
    found: dict[int, ChainWording] = {}
    zone = _commentary_zone(entry)
    last_complete: int | None = None
    for group in entry.groups:
        for record in _records(entry, group, found, last_complete, zone):
            found[record.chain_id] = record
        if found[group.chains[0]].basis in COMPLETE:
            last_complete = group.chains[0]
    _apply_lafz(entry, found)
    _apply_differences(entry, found)
    return [found.get(c.id, ChainWording(c.id, "none", None, None, "")) for c in chains]


def _commentary_zone(entry: _Entry) -> int:
    """Start of the collector's commentary: the first marker after the first wording."""
    starts = [g.tail.wording[0] for g in entry.groups if g.tail.wording and g.tail.complete]
    m = v.COMMENTARY.search(entry.text.norm, min(starts)) if starts else None
    return m.end() if m else len(entry.text.norm)


def _records(
    entry: _Entry,
    group: _Group,
    found: Mapping[int, ChainWording],
    last_complete: int | None,
    zone: int,
) -> list[ChainWording]:
    tail, text = group.tail, entry.text
    in_zone = min(entry.start_of(c) for c in group.chains) > zone
    if in_zone and tail.wording and tail.complete:  # words, unless they are about isnads
        reach = min(len(text.norm), tail.wording[1] + _COMMENT_REACH)
        in_zone = bool(v.ABOUT_ISNADS.search(text.norm, tail.wording[0], reach))
    if tail.empty and not tail.cited:
        return [ChainWording(c, "none", None, None, "") for c in group.chains]
    added = all(entry.introduced_by_addition(c) for c in group.chains)
    if tail.wording and tail.complete and not in_zone and not added:
        basis: Basis = "own" if len(group.chains) == 1 else "shared"
        span = text.raw_span(*tail.wording)
        return [ChainWording(c, basis, span, None, "") for c in group.chains]
    target = _target(entry, tail, found, last_complete)
    formula = text.raw_text(tail.formulas[0].start, tail.formulas[-1].end) if tail.formulas else ""
    if tail.cited or (in_zone and not tail.formulas):
        return [ChainWording(c, "reference", None, target, "") for c in group.chains]
    if (tail.partial or added) and tail.wording:
        span = text.raw_span(*tail.wording)
        return [ChainWording(c, "partial", span, target, formula) for c in group.chains]
    kind = tail.kind or "isnad"
    basis = "reference" if kind == "isnad" else kind
    return [ChainWording(c, basis, None, target, formula) for c in group.chains]


def _complete(cid: int, found: Mapping[int, ChainWording]) -> int | None:
    record = found.get(cid)
    if record is None:
        return None
    return cid if record.basis in COMPLETE else record.refers_to


def _target(
    entry: _Entry, tail: _Tail, found: Mapping[int, ChainWording], last_complete: int | None
) -> int | None:
    """The chain whose wording a formula means: the one it names, else the last wording."""
    for formula in tail.formulas:
        hit = entry.mention_named(formula.name, formula.start) if formula.name else None
        for cid in entry.chains_through(hit[0]) if hit else []:
            resolved = _complete(cid, found)
            if resolved is not None:
                return resolved
    return last_complete


def _named_chains(entry: _Entry, start: int, before: int) -> tuple[set[int], int]:
    """Chains through the narrator named at `start`, and where the name ends."""
    name, _ = _name_after(entry.text, start, len(entry.text.norm))
    if not name or name[0] in v.NOT_NAMES:
        return set(), start
    hit = entry.mention_named(name, before)
    if hit is None:
        return set(), start
    words = entry.text.words(start, len(entry.text.norm))
    pos, word = words[hit[1] - 1]
    return set(entry.chains_through(hit[0])), pos + len(word)


def _complete_group(
    entry: _Entry, chains: set[int], found: Mapping[int, ChainWording]
) -> _Group | None:
    for group in entry.groups:
        if chains & set(group.chains) and any(found[c].basis in COMPLETE for c in group.chains):
            return group
    return None


def _apply_lafz(entry: _Entry, found: dict[int, ChainWording]) -> None:
    """'واللفظ لفلان', 'هذا حديث فلان': the wording is that chain's; the others are similar."""
    text = entry.text
    for m in v.LAFZ_HIS.finditer(text.norm):
        before = [i for i, mention in enumerate(entry.mentions) if mention.end <= m.start()]
        if before:
            _mark_lafz(entry, found, set(entry.chains_through(before[-1])), m.start(), m.end())
    for m in v.LAFZ_NAMED.finditer(text.norm):
        chains, end = _named_chains(entry, m.end(), m.start())
        _mark_lafz(entry, found, chains, m.start(), end)


def _mark_lafz(
    entry: _Entry, found: dict[int, ChainWording], chains: set[int], start: int, end: int
) -> None:
    group = _complete_group(entry, chains, found)
    lafz = [c for c in group.chains if c in chains] if group else []
    if group is None or not lafz or len(lafz) == len(group.chains):
        return
    phrase = entry.text.raw_text(start, end)
    for cid in group.chains:
        record = found[cid]
        if cid in lafz:
            found[cid] = ChainWording(cid, "lafz", record.span, None, phrase)
        elif record.basis in COMPLETE:
            found[cid] = ChainWording(cid, "similar", None, lafz[0], phrase)


@dataclass(frozen=True, slots=True)
class _Difference:
    start: int  # the marker, e.g. "وقال محمد بن العلاء في حديثه"
    quoted: int  # where the chain's own words start
    chains: frozenset[int]


def _apply_differences(entry: _Entry, found: dict[int, ChainWording]) -> None:
    """'وفي رواية فلان: ...', 'وقال فلان في حديثه: ...', 'زاد فلان', 'قال فلان': the words that
    follow are that chain's only, when he is one of several chains sharing the wording."""
    for group in entry.groups:
        if len(group.chains) > 1 and group.tail.wording:
            _split_group(entry, group, found)


def _split_group(entry: _Entry, group: _Group, found: dict[int, ChainWording]) -> None:
    text, (start, end) = entry.text, group.tail.wording or (0, 0)
    verb = v.ISNAD_VERB.search(text.norm, end)
    limit = min(
        _next_anchor(entry, end), _back_off(text, verb.end(), end) if verb else len(text.norm)
    )
    limit = max(end, limit)
    members = set(group.chains)
    found_differences: list[_Difference] = []
    for m in v.DIFFERENCE.finditer(text.norm, start, limit):
        chains, name_end = _named_chains(entry, m.end(), start)
        explicit = not m.group().strip().endswith("قال") or bool(
            v.DIFFERENCE_TAIL.match(text.norm, text.trim(name_end, limit)[0])
        )
        if not explicit and _in_story(entry, start, m.start(), m.end(), name_end):
            continue  # 'قال علي' where 'Ali is a character of the story
        chains &= members
        if chains and chains != members:
            quoted = _skip(
                text, _skip(text, name_end, limit, v.DIFFERENCE_TAIL), limit, v.PARTIAL_LEAD
            )
            found_differences.append(
                _Difference(text.trim(m.start(), limit)[0], quoted, frozenset(chains))
            )
    named = set().union(*(d.chains for d in found_differences)) if found_differences else set()
    if not found_differences or named == members:
        return
    _cut_wording(entry, group, found, found_differences[0].start, named)
    if group.tail.partial:  # the named chains keep all the words quoted for them
        return
    base = next(c for c in group.chains if c not in named)
    stops = [d.start for d in found_differences[1:]] + [limit]
    for difference, stop in zip(found_differences, stops, strict=True):
        comment = v.COMMENTARY.search(text.norm, difference.quoted, stop)
        span = text.raw_span(difference.quoted, comment.start() if comment else stop)
        marker = text.raw_text(difference.start, difference.quoted)
        for cid in difference.chains:
            if span is not None:
                found[cid] = ChainWording(cid, "partial", span, base, marker)


def _in_story(entry: _Entry, start: int, marker: int, name_start: int, name_end: int) -> bool:
    """The name after a bare 'قال' already occurs in the wording before it."""
    name = entry.text.norm[name_start:name_end].split()
    told = entry.text.norm[start:marker].split()
    return bool(name) and _names(name[:1], told)


def _next_anchor(entry: _Entry, pos: int) -> int:
    later = [a for a in entry.anchors if a > pos]
    return _back_off(entry.text, min(later), pos) if later else len(entry.text.norm)


def _cut_wording(
    entry: _Entry, group: _Group, found: dict[int, ChainWording], cut: int, named: set[int]
) -> None:
    """End the shared words before the first difference, for the chains it does not name."""
    start = group.tail.wording[0] if group.tail.wording else cut
    span = entry.text.raw_span(start, cut)
    for cid in group.chains:
        record = found[cid]
        if cid in named and group.tail.partial:
            continue
        if record.span is not None and span is not None and span.end < record.span.end:
            found[cid] = ChainWording(cid, record.basis, span, record.refers_to, record.formula)
