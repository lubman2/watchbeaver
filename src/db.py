import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.executescript("""
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                url TEXT NOT NULL,
                ofn_url TEXT,
                category TEXT,
                last_checked_at TEXT
            );

            CREATE TABLE IF NOT EXISTS notices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                external_id TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                posted_at TEXT,
                taken_down_at TEXT,
                hash_val TEXT,
                first_seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_id, external_id),
                FOREIGN KEY(source_id) REFERENCES sources(id)
            );

            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notice_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                filename TEXT,
                file_hash TEXT UNIQUE,
                extracted_text TEXT,
                ocr_applied INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(notice_id) REFERENCES notices(id)
            );

            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notice_id INTEGER NOT NULL,
                attachment_id INTEGER,
                keyword TEXT NOT NULL,
                snippet TEXT NOT NULL,
                source_context TEXT,
                notified_telegram INTEGER DEFAULT 0,
                notified_email INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(notice_id) REFERENCES notices(id),
                FOREIGN KEY(attachment_id) REFERENCES attachments(id)
            );
            """)
            conn.commit()

    def upsert_source(self, source_id: str, name: str, source_type: str, url: str, ofn_url: Optional[str] = None, category: str = "other"):
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO sources (id, name, type, url, ofn_url, category)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    type=excluded.type,
                    url=excluded.url,
                    ofn_url=excluded.ofn_url,
                    category=excluded.category
            """, (source_id, name, source_type, url, ofn_url, category))
            conn.commit()

    def update_source_checked(self, source_id: str):
        with self._get_conn() as conn:
            conn.execute("UPDATE sources SET last_checked_at = ? WHERE id = ?", (datetime.utcnow().isoformat(), source_id))
            conn.commit()

    def is_notice_seen(self, source_id: str, external_id: str) -> bool:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT 1 FROM notices WHERE source_id = ? AND external_id = ?", (source_id, external_id))
            return cur.fetchone() is not None

    def insert_notice(self, source_id: str, external_id: str, title: str, url: str, posted_at: Optional[str] = None, hash_val: Optional[str] = None) -> int:
        with self._get_conn() as conn:
            cur = conn.execute("""
                INSERT INTO notices (source_id, external_id, title, url, posted_at, hash_val)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (source_id, external_id, title, url, posted_at, hash_val))
            conn.commit()
            return cur.lastrowid

    def is_attachment_seen(self, file_hash: str) -> bool:
        if not file_hash:
            return False
        with self._get_conn() as conn:
            cur = conn.execute("SELECT 1 FROM attachments WHERE file_hash = ?", (file_hash,))
            return cur.fetchone() is not None

    def insert_attachment(self, notice_id: int, url: str, filename: Optional[str] = None, file_hash: Optional[str] = None, extracted_text: Optional[str] = None, ocr_applied: int = 0) -> int:
        with self._get_conn() as conn:
            cur = conn.execute("""
                INSERT INTO attachments (notice_id, url, filename, file_hash, extracted_text, ocr_applied)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (notice_id, url, filename, file_hash, extracted_text, ocr_applied))
            conn.commit()
            return cur.lastrowid

    def insert_match(self, notice_id: int, keyword: str, snippet: str, attachment_id: Optional[int] = None, source_context: str = "notice") -> int:
        with self._get_conn() as conn:
            cur = conn.execute("""
                INSERT INTO matches (notice_id, attachment_id, keyword, snippet, source_context)
                VALUES (?, ?, ?, ?, ?)
            """, (notice_id, attachment_id, keyword, snippet, source_context))
            conn.commit()
            return cur.lastrowid

    def get_unnotified_matches(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.execute("""
                SELECT m.*, n.title as notice_title, n.url as notice_url, n.posted_at, s.name as source_name, s.url as source_url,
                       a.filename as attachment_filename, a.url as attachment_url
                FROM matches m
                JOIN notices n ON m.notice_id = n.id
                JOIN sources s ON n.source_id = s.id
                LEFT JOIN attachments a ON m.attachment_id = a.id
                WHERE m.notified_telegram = 0 OR m.notified_email = 0
            """)
            return [dict(row) for row in cur.fetchall()]

    def mark_match_notified(self, match_id: int, channel: str):
        col = "notified_telegram" if channel == "telegram" else "notified_email"
        with self._get_conn() as conn:
            conn.execute(f"UPDATE matches SET {col} = 1 WHERE id = ?", (match_id,))
            conn.commit()
