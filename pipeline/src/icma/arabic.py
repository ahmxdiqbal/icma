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
