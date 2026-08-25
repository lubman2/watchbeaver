import os
from pathlib import Path
import pytest
from src.config import load_config, Config
from src.db import Database

def test_load_config():
    cfg_path = Path(__file__).parent.parent / "config.yaml"
    cfg = load_config(str(cfg_path))
    assert isinstance(cfg, Config)
    assert len(cfg.keywords) > 0
    assert "792756" in cfg.keywords
    assert cfg.notifications.email.recipient == "romanxdolezal@seznam.cz"
    assert len(cfg.sources) >= 10

def test_load_config_includes_celakovice():
    cfg_path = Path(__file__).parent.parent / "config.yaml"
    cfg = load_config(str(cfg_path))
    ids = [s.id for s in cfg.sources]
    assert "celakovice" in ids
    celakovice = next(s for s in cfg.sources if s.id == "celakovice")
    assert celakovice.name == "Město Čelákovice"
    assert celakovice.type == "generic_html"
    assert celakovice.url == "https://www.celakovice.cz/cs/samosprava/uredni-deska/"
    assert celakovice.category == "neighbor"

def test_db_initialization(tmp_path):
    db_path = tmp_path / "test_watchdog.db"
    db = Database(str(db_path))
    db.init_schema()
    
    # Test adding source and notice
    db.upsert_source("test_src", "Test Source", "ofn", "http://example.com")
    
    notice_id = db.insert_notice(
        source_id="test_src",
        external_id="notice-123",
        title="Oznámení záměru Zeleneč",
        url="http://example.com/doc/123",
        posted_at="2026-08-25T10:00:00",
        hash_val="hash123"
    )
    assert notice_id is not None
    
    # Test checking if seen
    assert db.is_notice_seen("test_src", "notice-123") is True
    assert db.is_notice_seen("test_src", "unknown-999") is False
    
    # Test attachment insert
    att_id = db.insert_attachment(
        notice_id=notice_id,
        url="http://example.com/doc/123.pdf",
        filename="123.pdf",
        file_hash="pdfhash123"
    )
    assert att_id is not None
    assert db.is_attachment_seen("pdfhash123") is True
    
    # Test match recording
    match_id = db.insert_match(
        notice_id=notice_id,
        keyword="zeleneč",
        snippet="...projednání v obci Zeleneč na parcele...",
        source_context="attachment"
    )
    assert match_id is not None
    unnotified = db.get_unnotified_matches()
    assert len(unnotified) == 1
    assert unnotified[0]["notice_id"] == notice_id
    
    # Mark as notified
    db.mark_match_notified(match_id, channel="telegram")
    db.mark_match_notified(match_id, channel="email")
    assert len(db.get_unnotified_matches()) == 0
