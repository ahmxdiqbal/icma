from icma.arabic import normalize, normalize_with_offsets


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


def test_normalize_with_offsets_matches_normalize_and_points_into_the_source() -> None:
    text = "  قَالَ : خُذُوا عَنِّي ، الْبِكْرُ  "
    norm, offsets = normalize_with_offsets(text)
    assert norm == normalize(text)
    assert len(offsets) == len(norm)
    assert all(text[offsets[i]] in (" ", ":", "،") for i, ch in enumerate(norm) if ch == " ")
    assert "".join(text[offsets[i]] for i, ch in enumerate(norm) if ch != " ") == norm.replace(
        " ", ""
    )
