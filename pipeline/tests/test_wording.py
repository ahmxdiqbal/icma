from icma.analysis.wording import ChainWording, extract_wordings
from icma.models import Chain, Hadith, HadithType, Mention, NarratorLink, Span

COLLECTOR = 1
NAMES = {
    "يحيى": 10,
    "عمرو": 11,
    "ابن المثنى": 12,
    "ابن بشار": 13,
    "محمد بن جعفر": 14,
    "حجاج": 15,
    "هشيم": 20,
    "شعبة": 21,
    "قتادة": 30,
    "الحسن": 40,
    "عبادة": 50,
    "وكيع": 60,
}


def entry(text: str, *chains: tuple[int, ...]) -> tuple[Hadith, list[Chain]]:
    """An entry whose narrator mentions are every occurrence of a name in NAMES."""
    mentions = []
    for name, narrator in NAMES.items():
        start = text.find(name)
        while start >= 0:
            mentions.append(Mention(Span(start, start + len(name)), narrator))
            start = text.find(name, start + len(name))
    mentions.sort(key=lambda m: m.span.start)
    hadith = Hadith(1, 1, 1, 1, HadithType.MARFU, "", text, None, tuple(mentions))
    built = [
        Chain(100 + k, 1, "", tuple(NarratorLink(n) for n in (*reversed(ids), COLLECTOR)))
        for k, ids in enumerate(chains)
    ]
    return hadith, built


def run(text: str, *chains: tuple[int, ...]) -> list[ChainWording]:
    hadith, built = entry(text, *chains)
    return extract_wordings(hadith, built)


def words(text: str, record: ChainWording) -> str | None:
    return text[record.span.start : record.span.end] if record.span else None


UBADA = (40, 50)


def test_own_wording_starts_after_the_link_to_the_prophet() -> None:
    text = "حدثنا يحيى عن قتادة عن الحسن عن عبادة قال: قال رسول الله ﷺ: خذوا عني خذوا عني"
    (record,) = run(text, (10, 30, *UBADA))
    assert (record.basis, words(text, record)) == ("own", "خذوا عني خذوا عني")


def test_a_story_that_names_the_prophet_is_kept() -> None:
    text = "حدثنا يحيى عن الحسن عن عبادة قال: كان رسول الله ﷺ إذا نزل عليه الوحي كرب لذلك"
    (record,) = run(text, (10, *UBADA))
    assert words(text, record) == "كان رسول الله ﷺ إذا نزل عليه الوحي كرب لذلك"


def test_second_chain_with_mithlahu_takes_the_same_wording() -> None:
    text = (
        "حدثنا يحيى عن هشيم عن الحسن عن عبادة قال رسول الله ﷺ: خذوا عني، "
        "وحدثنا عمرو حدثنا هشيم بهذا الإسناد مثله"
    )
    first, second = run(text, (10, 20, *UBADA), (11, 20, *UBADA))
    assert (first.basis, words(text, first)) == ("own", "خذوا عني")
    assert (second.basis, second.span, second.refers_to) == ("same", None, first.chain_id)
    assert second.formula == "بهذا الإسناد مثله"


def test_nahwahu_is_similar_and_bimanahu_is_meaning() -> None:
    base = "حدثنا يحيى عن الحسن عن عبادة قال رسول الله ﷺ: خذوا عني، وحدثنا عمرو عن الحسن "
    for formula, basis in (("نحوه", "similar"), ("بمعناه", "meaning")):
        records = run(base + formula, (10, *UBADA), (11, *UBADA))
        assert (records[1].basis, records[1].refers_to) == (basis, 100)


def test_teachers_joined_by_wa_share_one_wording() -> None:
    text = "حدثنا ابن المثنى وابن بشار قالا حدثنا شعبة عن الحسن عن عبادة قال رسول الله ﷺ: خذوا عني"
    records = run(text, (12, 21, *UBADA), (13, 21, *UBADA))
    assert [r.basis for r in records] == ["shared", "shared"]
    assert {words(text, r) for r in records} == {"خذوا عني"}


def test_tahwil_chains_share_the_wording_after_the_last_isnad() -> None:
    text = (
        "حدثنا يحيى عن هشيم. ح وحدثنا عمرو حدثنا شعبة عن الحسن عن عبادة قال رسول الله ﷺ: خذوا عني"
    )
    records = run(text, (10, 20, *UBADA), (11, 21, *UBADA))
    assert [r.basis for r in records] == ["shared", "shared"]


def test_named_reference_points_at_the_named_chain() -> None:
    text = (
        "حدثنا محمد بن جعفر عن الحسن عن عبادة قال رسول الله ﷺ: خذوا عني، "
        "وحدثنا يحيى عن الحسن عن عبادة قال رسول الله ﷺ: خذوا، "
        "وحدثنا حجاج عن الحسن مثله، يعني مثل حديث ابن جعفر"
    )
    records = run(text, (14, *UBADA), (10, *UBADA), (15, *UBADA))
    assert (records[2].basis, records[2].refers_to) == ("same", 100)


def test_differences_only_are_partial() -> None:
    text = (
        "حدثنا يحيى عن قتادة عن الحسن عن عبادة قال رسول الله ﷺ: البكر جلد مائة، "
        "وحدثنا عمرو عن قتادة بهذا الإسناد، غير أن في حديثه: البكر يجلد لا يذكر مائة"
    )
    _, second = run(text, (10, 30, *UBADA), (11, 30, *UBADA))
    assert (second.basis, words(text, second), second.refers_to) == ("partial", "البكر يجلد", 100)


def test_closing_formula_makes_the_quoted_start_partial() -> None:
    text = (
        "حدثنا يحيى عن الحسن عن عبادة قال رسول الله ﷺ: خذوا عني، "
        "حدثنا عمرو عن الحسن عن عبادة قال: كان إذا نزل عليه الوحي ثم ذكر مثل حديث يحيى"
    )
    first, second = run(text, (10, *UBADA), (11, *UBADA))
    assert (second.basis, words(text, second), second.refers_to) == (
        "partial",
        "كان إذا نزل عليه الوحي",
        first.chain_id,
    )


def test_wording_attributed_to_one_teacher_makes_the_other_similar() -> None:
    text = (
        "حدثنا ابن المثنى وابن بشار واللفظ لابن المثنى قالا حدثنا شعبة عن الحسن عن عبادة "
        "قال رسول الله ﷺ: خذوا عني"
    )
    first, second = run(text, (12, 21, *UBADA), (13, 21, *UBADA))
    assert (first.basis, words(text, first)) == ("lafz", "خذوا عني")
    assert (second.basis, second.refers_to) == ("similar", first.chain_id)


def test_collectors_comment_ends_the_wording_and_its_chains_are_references() -> None:
    text = (
        "حدثنا يحيى عن الحسن عن عبادة قال رسول الله ﷺ: خذوا عني، "
        "قال أبو داود: روى وكيع هذا عن الحسن عن عبادة وهو خطأ"
    )
    first, second = run(text, (10, *UBADA), (60, *UBADA))
    assert words(text, first) == "خذوا عني"
    assert (second.basis, second.span, second.refers_to) == ("reference", None, first.chain_id)


def test_chain_missing_from_the_text_is_none() -> None:
    text = "حدثنا يحيى عن الحسن عن عبادة قال رسول الله ﷺ: خذوا عني"
    records = run(text, (10, *UBADA), (999,))
    assert records[1] == ChainWording(101, "none", None, None, "")


def test_story_naming_the_last_narrator_starts_the_wording() -> None:
    text = "حدثنا يحيى عن قتادة قال: كنت عند عبادة فمر رجل فقال عبادة: خذوا عني"
    (record,) = run(text, (10, 30, 50))
    assert words(text, record) == "كنت عند عبادة فمر رجل فقال عبادة: خذوا عني"


def test_a_short_descriptor_before_the_last_narrator_is_not_a_story() -> None:
    text = "حدثنا يحيى عن الحسن ابن أخي بني رقاش عن عبادة قال رسول الله ﷺ: خذوا عني"
    (record,) = run(text, (10, *UBADA))
    assert words(text, record) == "خذوا عني"


def test_one_joined_teachers_words_make_his_chain_partial() -> None:
    text = (
        "حدثنا ابن المثنى وابن بشار قالا حدثنا شعبة عن الحسن عن عبادة قال رسول الله ﷺ: "
        "خذوا عني، وقال ابن بشار في حديثه: خذوا مني"
    )
    first, second = run(text, (12, 21, *UBADA), (13, 21, *UBADA))
    assert (first.basis, words(text, first)) == ("shared", "خذوا عني")
    assert (second.basis, words(text, second), second.refers_to) == ("partial", "خذوا مني", 100)


def test_qala_with_a_story_character_is_not_a_difference() -> None:
    text = (
        "حدثنا يحيى وعمرو قالا حدثنا شعبة عن الحسن عن عبادة: أن عمرو سأل رسول الله ﷺ، "
        "قال عمرو: فسكت"
    )
    records = run(text, (10, 21, *UBADA), (11, 21, *UBADA))
    assert [r.basis for r in records] == ["shared", "shared"]
    assert words(text, records[0]) == "أن عمرو سأل رسول الله ﷺ، قال عمرو: فسكت"


def test_chain_followed_by_nothing_after_a_wording_is_a_reference() -> None:
    text = (
        "حدثنا يحيى عن الحسن عن عبادة قال رسول الله ﷺ: خذوا عني، "
        "قال يحيى: ثم لقيت هشيم فحدثنيه عن الحسن عن عبادة عن النبي ﷺ"
    )
    first, second = run(text, (10, *UBADA), (10, 20, *UBADA))
    assert (second.basis, second.refers_to) == ("reference", first.chain_id)


def test_opening_with_no_whole_wording_is_partial_without_a_target() -> None:
    text = "حدثنا يحيى وعمرو قالا حدثنا الحسن عن عبادة قال رسول الله ﷺ: خذوا عني وذكر الحديث"
    records = run(text, (10, *UBADA), (11, *UBADA))
    assert [(r.basis, words(text, r), r.refers_to) for r in records] == [
        ("partial", "خذوا عني", None),
        ("partial", "خذوا عني", None),
    ]


def test_mithlahu_followed_by_a_comment_quotes_nothing() -> None:
    text = (
        "حدثنا يحيى عن الحسن عن عبادة قال رسول الله ﷺ: خذوا عني، "
        "حدثنا عمرو عن الحسن بإسناده مثله، فهذا أصل الحديث"
    )
    _, second = run(text, (10, *UBADA), (11, *UBADA))
    assert (second.basis, second.span) == ("same", None)


def test_lafz_can_name_a_narrator_by_a_name_the_text_does_not_use() -> None:
    text = "حدثنا يحيى وعمرو قالا حدثنا الحسن عن عبادة قال رسول الله ﷺ: خذوا عني. لفظ الحماني"
    hadith, built = entry(text, (10, *UBADA), (11, *UBADA))
    first, second = extract_wordings(hadith, built, {10: ["يحيى بن عبد الحميد الحماني"]})
    assert (first.basis, second.basis, second.refers_to) == ("lafz", "similar", first.chain_id)
