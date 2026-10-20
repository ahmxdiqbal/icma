import pytest

from icma.analysis.correlation import BranchProfile, correlate, distinctive
from icma.analysis.schemas import (
    ChainMatn,
    ElementReading,
    MatnElement,
    MatnInventory,
    VariantReading,
)
from icma.analysis.variants import (
    ChainText,
    Variant,
    chain_texts,
    extraction_warnings,
    group_variants,
    multi_chain_hadith_ids,
)
from icma.bundle import BranchGroup
from icma.models import Chain, Hadith, HadithType, NarratorLink, Span, Tradition

TEXT = "حدثنا فلان عن فلان قال خذوا عني البكر بالبكر"


def hadith(hid: int, span: Span | None) -> Hadith:
    return Hadith(hid, 1, hid, 1, HadithType.MARFU, "", TEXT, span, ())


def chain(cid: int, hid: int) -> Chain:
    return Chain(cid, hid, "", (NarratorLink(1), NarratorLink(2)))


def matn(cid: int, relation: str, text: str = "", same: int | None = None) -> ChainMatn:
    return ChainMatn.model_validate(
        {
            "chain_id": cid,
            "relation": relation,
            "matn_ar": text,
            "same_as_chain_id": same,
            "reference_formula_ar": "",
            "note_en": "",
        }
    )


TRADITION = Tradition(
    books=(),
    narrators=(),
    hadiths=(hadith(10, Span(23, 31)), hadith(11, None), hadith(12, Span(0, 5))),
    chains=(chain(1, 10), chain(2, 11), chain(3, 12), chain(4, 12), chain(5, 12)),
)


def test_multi_chain_detection() -> None:
    assert multi_chain_hadith_ids(TRADITION) == {12}


def test_chain_texts_use_span_extraction_and_inheritance() -> None:
    extracted = [
        matn(3, "full_text", "البكر بالبكر"),
        matn(4, "reference_only", same=3),
        matn(5, "reference_only"),
    ]
    texts = {t.chain_id: (t.text_ar, t.source) for t in chain_texts(TRADITION, extracted)}
    assert texts == {
        1: ("خذوا عني", "span"),
        2: (None, "missing"),
        3: ("البكر بالبكر", "extracted"),
        4: ("البكر بالبكر", "inherited"),
        5: (None, "missing"),
    }


def test_multi_chain_without_extraction_falls_back_to_span() -> None:
    texts = {t.chain_id: t.source for t in chain_texts(TRADITION, [])}
    assert texts[3] == "span"


def test_variants_group_by_normalized_text_largest_first() -> None:
    texts = [
        ChainText(1, 10, "خُذُوا عَنِّي", "span"),
        ChainText(2, 11, "خذوا عني", "span"),
        ChainText(3, 12, "البكر بالبكر", "extracted"),
        ChainText(4, 12, None, "missing"),
    ]
    variants = group_variants(texts)
    assert [(v.id, v.chain_ids) for v in variants] == [("V1", (1, 2)), ("V2", (3,))]


def inventory() -> MatnInventory:
    def reading(vid: str, *elements: tuple[str, str]) -> VariantReading:
        return VariantReading(
            variant_id=vid,
            elements=[
                ElementReading(element_id=e, wording_ar="", wording_class=c) for e, c in elements
            ],
            translation_en="",
            notes_en="",
        )

    return MatnInventory(
        elements=[
            MatnElement(id="E1", label_en="", description_en="", exemplar_ar=""),
            MatnElement(id="E2", label_en="", description_en="", exemplar_ar=""),
        ],
        variants=[
            reading("V1", ("E1", "a"), ("E2", "x")),
            reading("V2", ("E1", "b")),
        ],
    )


def test_correlation_profiles_each_branch() -> None:
    groups = [
        BranchGroup(("P1",), (1, 2), "corroborated"),
        BranchGroup(("P2",), (3, 4), "corroborated"),
    ]
    variants = [Variant("V1", "", (1, 2)), Variant("V2", "", (3,))]
    result = correlate("CL", groups, variants, inventory())
    p1, p2 = result.branches
    assert (p1.chains_with_text, p1.element_rates) == (2, {"E1": 1.0, "E2": 1.0})
    assert (p2.chain_count, p2.chains_with_text, p2.element_rates) == (2, 1, {"E1": 1.0, "E2": 0.0})
    assert p1.wording_counts["E1"] == {"a": 2}
    assert result.distinctive_elements == ("E2",)


@pytest.mark.parametrize(("gap", "expected"), [(0.4, []), (0.5, ["E1"])])
def test_distinctive_threshold(gap: float, expected: list[str]) -> None:
    a = BranchProfile(("A",), "corroborated", 2, 2, {"E1": 1.0}, {})
    b = BranchProfile(("B",), "corroborated", 2, 2, {"E1": 1.0 - gap}, {})
    assert distinctive([a, b], ["E1"]) == expected


def test_branches_without_text_are_ignored_for_distinctiveness() -> None:
    a = BranchProfile(("A",), "corroborated", 2, 2, {"E1": 1.0}, {})
    empty = BranchProfile(("B",), "direct", 1, 0, {"E1": 0.0}, {})
    assert distinctive([a, empty], ["E1"]) == []


def test_quotes_must_be_verbatim_and_labels_are_advisory() -> None:
    extracted = [
        matn(3, "not_found", "البكر بالبكر"),  # mislabelled but verbatim: kept
        matn(4, "full_text", "نص مختلق"),  # not in the entry: ignored
        matn(5, "reference_only", same=3),
    ]
    texts = {t.chain_id: (t.text_ar, t.source) for t in chain_texts(TRADITION, extracted)}
    assert texts[3] == ("البكر بالبكر", "extracted")
    assert texts[4] == (None, "missing")
    assert texts[5] == ("البكر بالبكر", "inherited")
    warnings = extraction_warnings(TRADITION, extracted)
    assert "chain_matns: chain 3 relation 'not_found' contradicts its quote" in warnings
    assert "chain_matns: chain 4 quote is not in its entry; ignored" in warnings
    assert len(warnings) == 2


def test_verbatim_ignores_spacing_glitches_in_the_source() -> None:
    entry = Hadith(20, 1, 1, 1, HadithType.MARFU, "", "قال والثيببالثيب جلد", None, ())
    glitched = Tradition(
        books=(), narrators=(), hadiths=(entry,), chains=(chain(7, 20), chain(8, 20))
    )
    texts = chain_texts(glitched, [matn(7, "full_text", "والثيب بالثيب جلد")])
    assert texts[0].source == "extracted"
