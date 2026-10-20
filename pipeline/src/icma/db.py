"""Postgres access for review data: schema migrations and publishing analyses as judgements."""

import base64
import hashlib
import json
import secrets
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from icma.analysis.schemas import IcmaAnalysis, MatnInventory

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "db" / "migrations"


def migrate(conn: psycopg.Connection, migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply unapplied migrations in filename order, each in its own transaction."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
    )
    conn.commit()
    applied = {row[0] for row in conn.execute("SELECT name FROM schema_migrations")}
    ran: list[str] = []
    for path in sorted(migrations_dir.glob("*.sql")):
        if path.name in applied:
            continue
        with conn.transaction():
            conn.execute(path.read_text(encoding="utf-8").encode())
            conn.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (path.name,))
        ran.append(path.name)
    return ran


@dataclass(frozen=True, slots=True)
class Judgement:
    kind: str
    item_key: str
    model_output: dict[str, object]


def _synthesis_judgements(s: IcmaAnalysis) -> Iterator[Judgement]:
    yield Judgement(
        "convergence_point", s.convergence_point.node_key, s.convergence_point.model_dump()
    )
    for c in s.common_links:
        yield Judgement("common_link", c.node_key, c.model_dump())
    for p in s.partial_common_links:
        yield Judgement("partial_common_link", p.node_key, p.model_dump())
    for d in s.dives:
        yield Judgement("dive", str(d.chain_id), d.model_dump())
    for m in s.matn_clusters:
        yield Judgement("matn_cluster", m.label, m.model_dump())
    yield Judgement("correlation", "", s.correlation.model_dump())
    for r in s.reconstructions:
        yield Judgement("reconstruction", r.node_key, r.model_dump())
    yield Judgement("dating", "", s.dating.model_dump())
    yield Judgement("upper_isnad", "", {"assessment": s.upper_isnad})


def _matn_judgements(payload: dict[str, object], inventory: MatnInventory) -> Iterator[Judgement]:
    chain_texts = payload.get("chain_texts")
    if isinstance(chain_texts, list):
        for t in chain_texts:
            if isinstance(t, dict) and t.get("source") in ("extracted", "inherited"):
                yield Judgement("chain_matn", str(t["chain_id"]), t)
    for e in inventory.elements:
        yield Judgement("matn_element", e.id, e.model_dump())
    for v in inventory.variants:
        yield Judgement("variant_reading", v.variant_id, v.model_dump())


def judgements_of(payload: dict[str, object]) -> list[Judgement]:
    """Every reviewable unit in an analysis, in display order. Keys are unique per kind."""
    synthesis = IcmaAnalysis.model_validate(payload["synthesis"])
    inventory = MatnInventory.model_validate(payload["inventory"])
    found = [*_synthesis_judgements(synthesis), *_matn_judgements(payload, inventory)]
    counts = Counter((j.kind, j.item_key) for j in found)
    duplicates = sorted(k for k, n in counts.items() if n > 1)
    if duplicates:
        raise ValueError(f"analysis repeats judgements: {duplicates}")
    return found


def publish(conn: psycopg.Connection, payload: dict[str, object]) -> tuple[int, bool]:
    """Store an analysis and its judgements; idempotent by content.

    Returns the analysis id and whether it was newly created.
    """
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    existing = conn.execute(
        "SELECT id FROM analyses WHERE content_sha256 = %s", (digest,)
    ).fetchone()
    if existing is not None:
        return int(existing[0]), False
    judgements = judgements_of(payload)
    with conn.transaction():
        row = conn.execute(
            "INSERT INTO analyses (package_id, prompt_version, model, content_sha256, payload) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (
                payload["package_id"],
                payload["prompt_version"],
                str(payload.get("model", "unknown")),
                digest,
                Jsonb(payload),
            ),
        ).fetchone()
        if row is None:
            raise RuntimeError("insert into analyses returned no id")
        analysis_id = int(row[0])
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO judgements (analysis_id, kind, item_key, position, model_output) "
                "VALUES (%s, %s, %s, %s, %s)",
                [
                    (analysis_id, j.kind, j.item_key, i, Jsonb(j.model_output))
                    for i, j in enumerate(judgements)
                ],
            )
    return analysis_id, True


REVIEWER_ROLES = ("admin", "reviewer")


def set_reviewer(conn: psycopg.Connection, email: str, role: str, added_by: str) -> None:
    """Grant or change access for one email address."""
    if role not in REVIEWER_ROLES:
        raise ValueError(f"role must be one of {REVIEWER_ROLES}")
    with conn.transaction():
        conn.execute(
            "INSERT INTO reviewers (email, role, added_by) VALUES (%s, %s, %s) "
            "ON CONFLICT (email) DO UPDATE SET role = EXCLUDED.role",
            (email.strip().lower(), role, added_by),
        )


def remove_reviewer(conn: psycopg.Connection, email: str) -> bool:
    with conn.transaction():
        cur = conn.execute("DELETE FROM reviewers WHERE email = %s", (email.strip().lower(),))
    return cur.rowcount == 1


def list_reviewers(conn: psycopg.Connection) -> list[tuple[str, str]]:
    return [
        (str(e), str(r)) for e, r in conn.execute("SELECT email, role FROM reviewers ORDER BY 1")
    ]


# scrypt parameters; the web app verifies hashes in this exact format.
SCRYPT_N, SCRYPT_R, SCRYPT_P, SCRYPT_LEN = 16384, 8, 1, 32


def hash_passcode(passcode: str, salt: bytes | None = None) -> str:
    """Format: scrypt$N$r$p$<salt b64>$<hash b64>."""
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(
        passcode.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=SCRYPT_LEN
    )
    b64 = base64.b64encode
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${b64(salt).decode()}${b64(digest).decode()}"


def new_passcode() -> str:
    """Five groups of four characters from an unambiguous alphabet: about 100 bits of entropy."""
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    return "-".join("".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(5))


def issue_passcode(conn: psycopg.Connection, email: str) -> str:
    """Replace a reviewer's passcode and return the new one; it is shown once and never stored."""
    passcode = new_passcode()
    with conn.transaction():
        cur = conn.execute(
            "UPDATE reviewers SET passcode_hash = %s WHERE email = %s",
            (hash_passcode(passcode), email.strip().lower()),
        )
    if cur.rowcount != 1:
        raise ValueError(f"{email} is not a reviewer")
    return passcode
