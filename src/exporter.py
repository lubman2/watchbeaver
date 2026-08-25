import json
import sqlite3
from pathlib import Path

def export_db_to_json(db_path: str, output_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # 1. Sources
    cur = conn.execute("SELECT * FROM sources")
    sources = [dict(row) for row in cur.fetchall()]
    
    # 2. Matches with notice & source details
    cur = conn.execute("""
        SELECT m.id, m.keyword, m.snippet, m.source_context, m.created_at,
               m.notified_telegram, m.notified_email,
               n.id as notice_id, n.title as notice_title, n.url as notice_url, n.posted_at,
               s.id as source_id, s.name as source_name, s.category as source_category,
               a.filename as attachment_filename, a.url as attachment_url, a.ocr_applied
        FROM matches m
        JOIN notices n ON m.notice_id = n.id
        JOIN sources s ON n.source_id = s.id
        LEFT JOIN attachments a ON m.attachment_id = a.id
        ORDER BY m.id DESC
    """)
    matches = [dict(row) for row in cur.fetchall()]
    
    # 3. Stats
    total_notices = conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
    total_attachments = conn.execute("SELECT COUNT(*) FROM attachments").fetchone()[0]
    
    data = {
        "updated_at": sqlite3.datetime.datetime.utcnow().isoformat(),
        "stats": {
            "total_sources": len(sources),
            "total_notices": total_notices,
            "total_attachments": total_attachments,
            "total_matches": len(matches)
        },
        "sources": sources,
        "matches": matches
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    conn.close()

if __name__ == "__main__":
    import datetime
    sqlite3.datetime = datetime
    export_db_to_json(
        "/Users/lubman/Projects/zelenec-board-watchdog/data/watchdog.db",
        "/Users/lubman/Projects/zelenec-board-watchdog/web/public/data.json"
    )
