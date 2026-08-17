"""SQLite 스키마 정의 및 연결 헬퍼.

1단계 범위: 스키마 생성만 포함. 저장/조회 CRUD 함수는 2단계에서 추가한다.
"""
import sqlite3
from pathlib import Path

from core.config import DB_PATH

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    page_count INTEGER,
    added_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS clauses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES clauses(id) ON DELETE CASCADE,
    clause_number TEXT,
    title TEXT,
    body_text TEXT,
    page_number INTEGER NOT NULL,
    sort_order INTEGER,
    level INTEGER
);

CREATE INDEX IF NOT EXISTS idx_clauses_document ON clauses(document_id);
CREATE INDEX IF NOT EXISTS idx_clauses_parent ON clauses(parent_id);

CREATE VIRTUAL TABLE IF NOT EXISTS clauses_fts USING fts5(
    clause_number, title, body_text, content='clauses', content_rowid='id'
);
"""


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"DB 스키마 생성 완료: {DB_PATH}")
