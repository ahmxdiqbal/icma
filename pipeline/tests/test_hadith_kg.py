from pathlib import Path

import pytest
from kg_fixture import build

from icma.models import GapKind, GapLink, HadithType, NarratorLink, Span
from icma.sources.hadith_kg import HadithKgReader


@pytest.fixture
def reader(tmp_path: Path) -> HadithKgReader:
    return HadithKgReader(build(tmp_path / "kg.db"))


def test_selects_group_chains_through_anchors(reader: HadithKgReader) -> None:
    # Chain 1001 skips al-Hasan (id 2), so only the companion anchor selects both.
    assert [c.id for c in reader.load_tradition(730, [2]).chains] == [1000]
    tradition = reader.load_tradition(730, [1])
    assert [c.id for c in tradition.chains] == [1000, 1001]
    assert [h.id for h in tradition.hadiths] == [100]
    assert [b.id for b in tradition.books] == [9]


def test_chains_run_from_earliest_authority_to_collector(reader: HadithKgReader) -> None:
    chain = reader.load_tradition(730, [2]).chains[0]
    assert chain.links == (NarratorLink(1), NarratorLink(2), NarratorLink(3), NarratorLink(4))


def test_gap_pseudo_narrators_become_gap_links(reader: HadithKgReader) -> None:
    tradition = reader.load_tradition(730, [1])
    gapped = next(c for c in tradition.chains if c.id == 1001)
    assert gapped.links[1] == GapLink(GapKind.INQITA)
    assert 30000 not in {n.id for n in tradition.narrators}


def test_hadith_fields_and_mentions(reader: HadithKgReader) -> None:
    hadith = reader.load_tradition(730, [2]).hadiths[0]
    assert hadith.type is HadithType.MARFU
    assert hadith.matn_span == Span(33, len(hadith.text_ar))
    # Mention 999 has no narrator record and is kept as an unresolved span.
    assert [m.narrator_id for m in hadith.mentions] == [4, 3, None]


def test_optional_text_is_none_when_empty(reader: HadithKgReader) -> None:
    tradition = reader.load_tradition(730, [2])
    assert tradition.books[0].publisher_ar is None
    assert tradition.books[0].printing_ar == "الأولى"


def test_unknown_group_returns_empty_tradition(reader: HadithKgReader) -> None:
    tradition = reader.load_tradition(999, [2])
    assert (tradition.chains, tradition.hadiths, tradition.books) == ((), (), ())


def test_requires_an_anchor(reader: HadithKgReader) -> None:
    with pytest.raises(ValueError, match="anchor"):
        reader.load_tradition(730, [])


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        HadithKgReader(tmp_path / "nope.db")
