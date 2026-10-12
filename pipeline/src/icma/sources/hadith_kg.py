"""Reader for the hadith-kg SQLite dataset (huggingface.co/datasets/emadjumaah/hadith-kg)."""

import sqlite3
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import replace
from pathlib import Path

from icma.models import (
    Book,
    Chain,
    GapKind,
    GapLink,
    Hadith,
    HadithType,
    Link,
    Mention,
    Narrator,
    NarratorLink,
    Span,
    Tradition,
)

# hadith-kg stores chain gaps as pseudo-narrators. Their source grade code (12, "fabricator")
# is an artifact and must never be read as a judgement on a real person.
GAP_RAWI_IDS: dict[int, GapKind] = {
    30002: GapKind.IRSAL,
    30000: GapKind.INQITA,
    30001: GapKind.TALIQ,
    1131: GapKind.MUBHAM,
}

_HADITH_TYPES: dict[int, HadithType] = {
    0: HadithType.QUDSI,
    1: HadithType.MARFU,
    2: HadithType.MAWQUF,
    3: HadithType.MAQTU,
}

Row = tuple[object, ...]


def _opt_text(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _opt_int(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _int(value: object) -> int:
    if not isinstance(value, int):
        raise TypeError(f"expected int, got {value!r}")
    return value


def _str(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"expected str, got {value!r}")
    return value


def _marks(count: int) -> str:
    return ",".join("?" * count)


class HadithKgReader:
    def __init__(self, path: Path) -> None:
        if not path.is_file():
            raise FileNotFoundError(path)
        # immutable=1: the file is a read-only WAL-mode snapshot; skip locking and -shm creation.
        self._db = sqlite3.connect(f"file:{path}?immutable=1", uri=True)

    def close(self) -> None:
        self._db.close()

    def _rows(self, sql: str, params: Sequence[object] = ()) -> list[Row]:
        return self._db.execute(sql, params).fetchall()

    def load_tradition(self, group_id: int, anchor_narrator_ids: Iterable[int]) -> Tradition:
        """Load every chain in a meaning group that passes through at least one anchor narrator."""
        anchors = sorted(set(anchor_narrator_ids))
        if not anchors:
            raise ValueError("at least one anchor narrator is required")
        chain_rows = self._rows(
            f"""SELECT s.id, s.hadith_id, s.hukum FROM sanads s
                WHERE s.group_id = ? AND EXISTS (
                  SELECT 1 FROM sanad_rawis sr
                  WHERE sr.sanad_id = s.id AND sr.rawi_id IN ({_marks(len(anchors))}))
                ORDER BY s.id""",
            [group_id, *anchors],
        )
        chains = self._load_chains(chain_rows)
        hadiths = self._load_hadiths(sorted({c.hadith_id for c in chains}))
        narrator_ids = {
            link.narrator_id
            for chain in chains
            for link in chain.links
            if isinstance(link, NarratorLink)
        } | {m.narrator_id for h in hadiths for m in h.mentions if m.narrator_id is not None}
        narrators = self.load_narrators(sorted(narrator_ids))
        known = {n.id for n in narrators}
        hadiths = [_drop_unknown_mentions(h, known) for h in hadiths]
        books = self._load_books(sorted({h.book_id for h in hadiths}))
        return Tradition(tuple(books), tuple(narrators), tuple(hadiths), tuple(chains))

    def _load_chains(self, chain_rows: list[Row]) -> list[Chain]:
        ids = [_int(r[0]) for r in chain_rows]
        links: dict[int, list[Link]] = defaultdict(list)
        # pos 0 is the collector; descending pos yields earliest authority first.
        for sanad_id, rawi_id in self._rows(
            f"""SELECT sanad_id, rawi_id FROM sanad_rawis
                WHERE sanad_id IN ({_marks(len(ids))}) ORDER BY sanad_id, pos DESC""",
            ids,
        ):
            rid = _int(rawi_id)
            gap = GAP_RAWI_IDS.get(rid)
            links[_int(sanad_id)].append(GapLink(gap) if gap else NarratorLink(rid))
        return [
            Chain(
                id=_int(r[0]),
                hadith_id=_int(r[1]),
                grade_ar=_str(r[2]),
                links=tuple(links[_int(r[0])]),
            )
            for r in chain_rows
        ]

    def _load_hadiths(self, ids: list[int]) -> list[Hadith]:
        mentions: dict[int, list[Mention]] = defaultdict(list)
        for hadith_id, rawi_id, start, end in self._rows(
            f"""SELECT hadith_id, rawi_id, start, end FROM hadith_rawis
                WHERE hadith_id IN ({_marks(len(ids))}) ORDER BY hadith_id, seq""",
            ids,
        ):
            rid = _opt_int(rawi_id)
            narrator = None if rid is None or rid in GAP_RAWI_IDS else rid
            mentions[_int(hadith_id)].append(Mention(Span(_int(start), _int(end)), narrator))
        rows = self._rows(
            f"""SELECT id, book_id, no_inbook, page_no, type_no, matn, nass, matn_start, matn_end
                FROM hadiths WHERE id IN ({_marks(len(ids))}) ORDER BY id""",
            ids,
        )
        return [_hadith(r, tuple(mentions[_int(r[0])])) for r in rows]

    def load_narrators(self, ids: list[int]) -> list[Narrator]:
        rows = self._rows(
            f"""SELECT id, name, nickname, tabaka, rank_no, rank, death_year, death_year_raw, iqama,
                       has_tadlis, has_ikhtilat, is_bukhari, is_muslim, is_stub
                FROM rawis WHERE id IN ({_marks(len(ids))}) ORDER BY id""",
            ids,
        )
        return [
            Narrator(
                id=_int(r[0]),
                name_ar=_str(r[1]),
                display_name_ar=_opt_text(r[2]) or _str(r[1]),
                tabaqa=_int(r[3]),
                grade_code=_int(r[4]),
                grade_ar=_opt_text(r[5]),
                death_ah=_opt_int(r[6]),
                death_ah_raw=_opt_text(r[7]),
                residence_ar=_opt_text(r[8]),
                has_tadlis=bool(r[9]),
                has_ikhtilat=bool(r[10]),
                in_bukhari=bool(r[11]),
                in_muslim=bool(r[12]),
                is_stub=bool(r[13]),
            )
            for r in rows
        ]

    def _load_books(self, ids: list[int]) -> list[Book]:
        rows = self._rows(
            f"""SELECT id, name, author_name, author_death_year, tasnif, dar, city, tabaa
                FROM books WHERE id IN ({_marks(len(ids))}) ORDER BY id""",
            ids,
        )
        return [
            Book(
                id=_int(r[0]),
                title_ar=_str(r[1]),
                author_ar=_str(r[2]),
                author_death_ah=_opt_int(r[3]),
                category_ar=_str(r[4]),
                publisher_ar=_opt_text(r[5]),
                city_ar=_opt_text(r[6]),
                printing_ar=_opt_text(r[7]),
            )
            for r in rows
        ]


def _hadith(r: Row, mentions: tuple[Mention, ...]) -> Hadith:
    start, end = _opt_int(r[7]), _opt_int(r[8])
    return Hadith(
        id=_int(r[0]),
        book_id=_int(r[1]),
        number_in_book=_int(r[2]),
        page=_int(r[3]),
        type=_HADITH_TYPES[_int(r[4])],
        grade_ar=_str(r[5]),
        text_ar=_str(r[6]),
        matn_span=Span(start, end) if start is not None and end is not None else None,
        mentions=mentions,
    )


def _drop_unknown_mentions(hadith: Hadith, known: set[int]) -> Hadith:
    """Mentions pointing at ids with no narrator record are kept as unresolved spans."""
    fixed = tuple(
        m if m.narrator_id is None or m.narrator_id in known else Mention(m.span, None)
        for m in hadith.mentions
    )
    return hadith if fixed == hadith.mentions else replace(hadith, mentions=fixed)
