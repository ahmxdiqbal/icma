"""Arabic text normalization for matching. Never applied to stored source text."""

import re

# Harakat, tanwin, shadda, sukun, superscript alef, and Quranic annotation marks.
_DIACRITICS = re.compile("[ً-ٰٟۖ-ۭ]")
_TATWEEL = "ـ"
_LETTER_MAP = str.maketrans(
    {
        "آ": "ا",  # alef with madda -> alef
        "أ": "ا",  # alef with hamza above -> alef
        "إ": "ا",  # alef with hamza below -> alef
        "ٱ": "ا",  # alef wasla -> alef
        "ى": "ي",  # alef maqsura -> ya
        "ة": "ه",  # ta marbuta -> ha
    }
)
_NON_LETTERS = re.compile(r"[^ء-ي0-9\s]")
_SPACES = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Strip diacritics and punctuation and fold letter variants, for search and comparison."""
    stripped = _DIACRITICS.sub("", text).replace(_TATWEEL, "")
    folded = stripped.translate(_LETTER_MAP)
    letters_only = _NON_LETTERS.sub(" ", folded)
    return _SPACES.sub(" ", letters_only).strip()


def normalize_with_offsets(text: str) -> tuple[str, tuple[int, ...]]:
    """`normalize(text)` plus, for each of its characters, the index of the source character.

    A collapsed run of spaces and punctuation maps to the run's first source character."""
    chars: list[str] = []
    offsets: list[int] = []
    gap_at: int | None = None
    for i, ch in enumerate(text):
        if ch == _TATWEEL or _DIACRITICS.match(ch):
            continue
        folded = ch.translate(_LETTER_MAP)
        if folded.isspace() or _NON_LETTERS.match(folded):
            if chars and gap_at is None:
                gap_at = i
            continue
        if gap_at is not None:
            chars.append(" ")
            offsets.append(gap_at)
            gap_at = None
        chars.append(folded)
        offsets.append(i)
    return "".join(chars), tuple(offsets)


def is_diacritic(ch: str) -> bool:
    return ch == _TATWEEL or bool(_DIACRITICS.match(ch))
