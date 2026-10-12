"""Integration tests against a real Postgres. Set ICMA_TEST_DATABASE_URL to run them, e.g.
postgresql://icma:icma@localhost:54329/icma (each test gets its own throwaway database)."""

import os
import uuid
from collections.abc import Iterator

import psycopg
import pytest
from test_analysis_runner import INVENTORY, SYNTHESIS

from icma.db import judgements_of, migrate, publish

ADMIN_URL = os.environ.get("ICMA_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(ADMIN_URL is None, reason="ICMA_TEST_DATABASE_URL not set")

PAYLOAD: dict[str, object] = {
    "schema_version": 1,
    "package_id": "t",
    "prompt_version": "p1",
    "status": "unreviewed",
    "chain_texts": [
        {"chain_id": 1000, "hadith_id": 100, "text_ar": "خذوا عني", "source": "span"},
        {"chain_id": 1001, "hadith_id": 100, "text_ar": "خذوا عني", "source": "extracted"},
    ],
    "variants": [],
    "inventory": INVENTORY,
    "correlations": [],
    "synthesis": SYNTHESIS,
    "warnings": [],
}


@pytest.fixture
def conn() -> Iterator[psycopg.Connection]:
    assert ADMIN_URL is not None
    name = f"icma_test_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(ADMIN_URL, autocommit=True) as admin:
        admin.execute(f'CREATE DATABASE "{name}"'.encode())
    url = psycopg.conninfo.make_conninfo(ADMIN_URL, dbname=name)
    try:
        with psycopg.connect(url) as c:
            migrate(c)
            yield c
    finally:
        with psycopg.connect(ADMIN_URL, autocommit=True) as admin:
            admin.execute(f'DROP DATABASE "{name}" WITH (FORCE)'.encode())


def test_migrate_is_idempotent(conn: psycopg.Connection) -> None:
    assert migrate(conn) == []
    names = [r[0] for r in conn.execute("SELECT name FROM schema_migrations")]
    assert names == ["0001_review.sql"]


def test_publish_stores_every_judgement_once(conn: psycopg.Connection) -> None:
    analysis_id, created = publish(conn, PAYLOAD)
    assert created
    rows = conn.execute(
        "SELECT kind, item_key FROM judgements WHERE analysis_id = %s ORDER BY position",
        (analysis_id,),
    ).fetchall()
    expected = [(j.kind, j.item_key) for j in judgements_of(PAYLOAD)]
    assert rows == expected
    assert ("chain_matn", "1001") in rows
    assert ("chain_matn", "1000") not in rows  # dataset spans are not model output


def test_publish_is_idempotent_by_content(conn: psycopg.Connection) -> None:
    first, _ = publish(conn, PAYLOAD)
    second, created = publish(conn, PAYLOAD)
    assert (second, created) == (first, False)
    assert conn.execute("SELECT count(*) FROM analyses").fetchone() == (1,)


def test_reviews_are_append_only_history_with_current_view(conn: psycopg.Connection) -> None:
    analysis_id, _ = publish(conn, PAYLOAD)
    row = conn.execute(
        "SELECT id FROM judgements WHERE analysis_id = %s AND kind = 'convergence_point'",
        (analysis_id,),
    ).fetchone()
    assert row is not None
    jid = row[0]
    conn.execute(
        "INSERT INTO reviews (judgement_id, reviewer, decision) VALUES (%s, 'a', 'accept')", (jid,)
    )
    conn.execute(
        "INSERT INTO reviews (judgement_id, reviewer, decision, revised_output) "
        "VALUES (%s, 'a', 'revise', '{\"verdict\": \"rejected\"}')",
        (jid,),
    )
    current = conn.execute(
        "SELECT decision FROM current_reviews WHERE judgement_id = %s", (jid,)
    ).fetchall()
    assert current == [("revise",)]
    assert conn.execute("SELECT count(*) FROM reviews").fetchone() == (2,)


def test_revise_requires_revised_output(conn: psycopg.Connection) -> None:
    analysis_id, _ = publish(conn, PAYLOAD)
    row = conn.execute("SELECT min(id) FROM judgements WHERE analysis_id = %s", (analysis_id,))
    jid = row.fetchone()
    assert jid is not None
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            "INSERT INTO reviews (judgement_id, reviewer, decision) VALUES (%s, 'a', 'revise')",
            (jid[0],),
        )


def test_duplicate_judgements_are_rejected() -> None:
    synthesis = dict(SYNTHESIS)
    dive = {"chain_id": 7, "interpretation": "undecidable", "reasoning": ""}
    synthesis["dives"] = [dive, dive]
    with pytest.raises(ValueError, match="repeats"):
        judgements_of({**PAYLOAD, "synthesis": synthesis})
