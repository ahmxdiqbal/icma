from icma.arabic import normalize


def test_strips_harakat_and_shadda() -> None:
    assert normalize("حَدَّثَنَا شُعْبَةُ") == "حدثنا شعبه"


def test_folds_alef_variants_and_alef_maqsura() -> None:
    assert normalize("أَبُو إِسْحَاقَ آمَنَ ٱللَّهُ عَلَى") == "ابو اسحاق امن الله علي"


def test_removes_superscript_alef_and_tatweel() -> None:
    assert normalize("هَٰذَا كتـــاب") == "هذا كتاب"


def test_drops_punctuation_and_collapses_spaces() -> None:
    assert normalize("قَالَ : حَدَّثَنَا ،  عَنْ") == "قال حدثنا عن"


def test_keeps_digits() -> None:
    assert normalize("سورة البقرة آية 143") == "سوره البقره ايه 143"


def test_empty_and_whitespace() -> None:
    assert normalize("") == ""
    assert normalize("  \n ") == ""
