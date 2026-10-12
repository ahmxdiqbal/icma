import json
from datetime import UTC, datetime
from pathlib import Path

from kg_fixture import build

from icma.cli import bundle_of, load_corrected
from icma.export import SCHEMA_VERSION, PackageMeta, package_json

CORRECTION = {
    "chain_id": 1001,
    "op": "replace",
    "from_narrator_id": 3,
    "to_narrator_id": 5,
    "reason": "r",
    "evidence": "e",
    "author": "a",
    "date": "2026-10-11",
}


def records(value: object) -> list[dict[str, object]]:
    assert isinstance(value, list)
    return [item for item in value if isinstance(item, dict)]


def section(package: dict[str, object], name: str) -> dict[str, object]:
    value = package[name]
    assert isinstance(value, dict)
    return value


def export(tmp_path: Path, corrections: list[dict[str, object]] | None = None) -> dict[str, object]:
    db = build(tmp_path / "kg.db")
    path = None
    if corrections is not None:
        path = tmp_path / "c.json"
        path.write_text(json.dumps({"corrections": corrections}), encoding="utf-8")
    tradition, applied = load_corrected(db, 730, (1,), path)
    meta = PackageMeta("t", "T", 730, (1,))
    at = datetime(2026, 10, 11, tzinfo=UTC)
    return package_json(meta, tradition, bundle_of(tradition), applied, at)


def test_package_is_json_serializable_with_expected_sections(tmp_path: Path) -> None:
    package = export(tmp_path)
    assert json.loads(json.dumps(package, ensure_ascii=False)) == package
    assert package["schema_version"] == SCHEMA_VERSION
    assert package["generated_at"] == "2026-10-11T00:00:00+00:00"
    assert set(package) >= {"books", "narrators", "hadiths", "chains", "bundle", "source"}


def test_chain_links_and_gap_nodes(tmp_path: Path) -> None:
    package = export(tmp_path)
    chains = {c["id"]: c for c in records(package["chains"])}
    assert records(chains[1001]["links"])[1] == {"kind": "gap", "gap": "inqita"}
    kinds = {n["key"]: n["kind"] for n in records(section(package, "bundle")["nodes"])}
    assert kinds["prophet"] == "prophet"
    assert kinds["g:inqita:1001:1"] == "gap"
    assert kinds["n:2"] == "narrator"


def test_correction_pulls_in_new_narrator(tmp_path: Path) -> None:
    package = export(tmp_path, [CORRECTION])
    assert 5 in {n["id"] for n in records(package["narrators"])}
    assert records(package["corrections_applied"])[0]["chain_id"] == 1001
