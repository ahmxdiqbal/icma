"""Builds a tiny SQLite file with the hadith-kg schema subset the reader uses."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE books (id INTEGER PRIMARY KEY, name TEXT, author_no INTEGER, author_name TEXT,
  author_death_year INTEGER, city TEXT, dar TEXT, tabaa TEXT, tasnif_no INTEGER, tasnif TEXT,
  hadith_qty INTEGER);
CREATE TABLE rawis (id INTEGER PRIMARY KEY, name TEXT, nickname TEXT, rank_no INTEGER, rank TEXT,
  tabaka INTEGER, is_bukhari INTEGER, is_muslim INTEGER, has_ikhtilat INTEGER, has_tadlis INTEGER,
  riwaya_qty INTEGER, birth_year INTEGER, birth_year_raw TEXT, death_year INTEGER,
  death_year_raw TEXT, age_raw TEXT, profession TEXT, nasab TEXT, iqama TEXT, death_place TEXT,
  is_stub INTEGER);
CREATE TABLE hadiths (id INTEGER PRIMARY KEY, book_id INTEGER, no_inbook INTEGER, page_no INTEGER,
  type_no INTEGER, type TEXT, matn_no INTEGER, matn TEXT, group_id INTEGER, takhrij INTEGER,
  taraf_nass TEXT, nass TEXT, matn_start INTEGER, matn_end INTEGER);
CREATE TABLE hadith_rawis (hadith_id INTEGER, seq INTEGER, rawi_id INTEGER, start INTEGER,
  end INTEGER);
CREATE TABLE sanads (id INTEGER PRIMARY KEY, hadith_id INTEGER, matn_no INTEGER, matn TEXT,
  hukum TEXT, group_id INTEGER, takhrij INTEGER, max_rank INTEGER, length INTEGER);
CREATE TABLE sanad_rawis (sanad_id INTEGER, pos INTEGER, rawi_id INTEGER);
"""

TEXT = "حدثنا أحمد عن قتادة عن الحسن قال خذوا عني"


def _rawi(rid: int, name: str, rank_no: int = 3) -> tuple[object, ...]:
    return (rid, name, name, rank_no, "ثقة", 3, 0, 0, 0, 0, 1, None, None, 110, "110", None,
            None, None, "البصرة", None, 0)  # fmt: skip


def build(path: Path) -> Path:
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    db.executemany(
        "INSERT INTO books VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [(9, "مسند أحمد", 1, "أحمد بن حنبل", 241, "بيروت", "", "الأولى", 2, "مسانيد", 1)],
    )
    db.executemany(
        f"INSERT INTO rawis VALUES ({','.join('?' * 21)})",
        [
            _rawi(1, "عبادة", 1),
            _rawi(2, "الحسن"),
            _rawi(3, "قتادة"),
            _rawi(4, "أحمد"),
            _rawi(30000, "موضع انقطاع", 12),
            _rawi(5, "غير متصل"),  # in group 731 only
        ],
    )
    db.executemany(
        f"INSERT INTO hadiths VALUES ({','.join('?' * 14)})",
        [
            (100, 9, 1, 5, 1, "مرفوع", 0, "صحيح", 730, 1, "", TEXT, 33, len(TEXT)),
            (101, 9, 2, 5, 1, "مرفوع", 0, "صحيح", 731, 1, "", TEXT, None, None),
        ],
    )
    db.executemany(
        "INSERT INTO hadith_rawis VALUES (?,?,?,?,?)",
        [(100, 0, 4, 6, 10), (100, 1, 3, 14, 19), (100, 2, 999, 23, 28)],
    )
    db.executemany(
        "INSERT INTO sanads VALUES (?,?,?,?,?,?,?,?,?)",
        [
            (1000, 100, 0, "صحيح", "إسناده صحيح", 730, 1, 3, 4),
            (1001, 100, 0, "صحيح", "إسناده منقطع", 730, 1, 12, 4),
            (1002, 101, 0, "صحيح", "", 731, 1, 3, 2),
        ],
    )
    # pos 0 = collector; the reader must return chains earliest-authority first.
    db.executemany(
        "INSERT INTO sanad_rawis VALUES (?,?,?)",
        [
            (1000, 0, 4), (1000, 1, 3), (1000, 2, 2), (1000, 3, 1),
            (1001, 0, 4), (1001, 1, 3), (1001, 2, 30000), (1001, 3, 1),
            (1002, 0, 4), (1002, 1, 5),
        ],
    )  # fmt: skip
    db.commit()
    db.close()
    return path
