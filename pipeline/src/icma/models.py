"""Source-agnostic records for one tradition: books, narrators, hadith texts and their chains."""

from dataclasses import dataclass
from enum import StrEnum


class GapKind(StrEnum):
    """A position in a chain that is not an identified person."""

    IRSAL = "irsal"  # chain stops below the companion (mursal)
    INQITA = "inqita"  # a link is missing mid-chain
    TALIQ = "taliq"  # the collector suspends the chain, omitting his own informants
    MUBHAM = "mubham"  # a person is mentioned but not named


class HadithType(StrEnum):
    QUDSI = "qudsi"
    MARFU = "marfu"
    MAWQUF = "mawquf"
    MAQTU = "maqtu"


@dataclass(frozen=True, slots=True)
class Book:
    id: int
    title_ar: str
    author_ar: str
    author_death_ah: int | None
    category_ar: str
    publisher_ar: str | None
    city_ar: str | None
    printing_ar: str | None


@dataclass(frozen=True, slots=True)
class Narrator:
    id: int
    name_ar: str
    display_name_ar: str
    tabaqa: int
    grade_code: int
    grade_ar: str | None
    death_ah: int | None
    death_ah_raw: str | None
    residence_ar: str | None
    has_tadlis: bool
    has_ikhtilat: bool
    in_bukhari: bool
    in_muslim: bool
    is_stub: bool


@dataclass(frozen=True, slots=True)
class NarratorLink:
    narrator_id: int


@dataclass(frozen=True, slots=True)
class GapLink:
    gap: GapKind


Link = NarratorLink | GapLink


@dataclass(frozen=True, slots=True)
class Chain:
    """One isnad, ordered from the earliest authority down to the collector."""

    id: int
    hadith_id: int
    grade_ar: str
    links: tuple[Link, ...]


@dataclass(frozen=True, slots=True)
class Span:
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class Mention:
    span: Span
    narrator_id: int | None


@dataclass(frozen=True, slots=True)
class Hadith:
    id: int
    book_id: int
    number_in_book: int
    page: int
    type: HadithType
    grade_ar: str
    text_ar: str
    matn_span: Span | None
    mentions: tuple[Mention, ...]


@dataclass(frozen=True, slots=True)
class Tradition:
    books: tuple[Book, ...]
    narrators: tuple[Narrator, ...]
    hadiths: tuple[Hadith, ...]
    chains: tuple[Chain, ...]
