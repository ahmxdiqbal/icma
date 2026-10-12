import json
from pathlib import Path

import pytest

from icma.corrections import CorrectionError, apply_corrections, load_corrections
from icma.models import Chain, GapKind, GapLink, NarratorLink

BASE = {"reason": "r", "evidence": "e", "author": "a", "date": "2026-10-11"}


def write(tmp_path: Path, *entries: dict[str, object]) -> Path:
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"corrections": list(entries)}), encoding="utf-8")
    return path


def chain(chain_id: int, *ids: int) -> Chain:
    return Chain(chain_id, 1, "", tuple(NarratorLink(i) for i in ids))


def test_replace_swaps_the_narrator(tmp_path: Path) -> None:
    path = write(tmp_path, {**BASE, "chain_id": 7, "op": "replace", "from_narrator_id": 3,
                            "to_narrator_id": 9})  # fmt: skip
    chains, applied = apply_corrections([chain(7, 1, 3, 4), chain(8, 1, 3)], load_corrections(path))
    assert [c.links for c in chains] == [
        (NarratorLink(1), NarratorLink(9), NarratorLink(4)),
        (NarratorLink(1), NarratorLink(3)),
    ]
    assert [c.chain_id for c in applied] == [7]


def test_set_links_rewrites_the_whole_chain(tmp_path: Path) -> None:
    links = [{"narrator_id": 1}, {"gap": "inqita"}, {"narrator_id": 4}]
    path = write(tmp_path, {**BASE, "chain_id": 7, "op": "set_links", "links": links})
    chains, _ = apply_corrections([chain(7, 1, 3, 4)], load_corrections(path))
    assert chains[0].links == (NarratorLink(1), GapLink(GapKind.INQITA), NarratorLink(4))


def test_exclude_drops_the_chain(tmp_path: Path) -> None:
    path = write(tmp_path, {**BASE, "chain_id": 7, "op": "exclude"})
    chains, applied = apply_corrections([chain(7, 1, 2), chain(8, 1, 2)], load_corrections(path))
    assert [c.id for c in chains] == [8]
    assert applied[0].op == "exclude"


def test_stale_replace_is_an_error(tmp_path: Path) -> None:
    path = write(tmp_path, {**BASE, "chain_id": 7, "op": "replace", "from_narrator_id": 5,
                            "to_narrator_id": 9})  # fmt: skip
    with pytest.raises(CorrectionError, match="stale"):
        apply_corrections([chain(7, 1, 3)], load_corrections(path))


@pytest.mark.parametrize(
    "entry",
    [
        {**BASE, "chain_id": 7, "op": "rename"},
        {**BASE, "chain_id": "7", "op": "exclude"},
        {**BASE, "chain_id": 7, "op": "exclude", "evidence": ""},
        {**BASE, "chain_id": 7, "op": "replace", "from_narrator_id": 3},
        {**BASE, "chain_id": 7, "op": "set_links", "links": [{"narrator_id": 1}]},
        {**BASE, "chain_id": 7, "op": "set_links", "links": [{"narrator_id": 1}, {"gap": "x"}]},
    ],
)
def test_invalid_entries_are_rejected(tmp_path: Path, entry: dict[str, object]) -> None:
    with pytest.raises(CorrectionError):
        load_corrections(write(tmp_path, entry))


def test_duplicate_chain_ids_are_rejected(tmp_path: Path) -> None:
    path = write(tmp_path, {**BASE, "chain_id": 7, "op": "exclude"},
                 {**BASE, "chain_id": 7, "op": "exclude"})  # fmt: skip
    with pytest.raises(CorrectionError, match="same chain"):
        load_corrections(path)
