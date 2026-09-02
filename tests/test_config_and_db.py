import os
from pathlib import Path
import pytest
from src.config import load_config, Config
from src.db import Database
from src.pipeline import web_json_path_for_db

def test_load_config():
    cfg_path = Path(__file__).parent.parent / "config.yaml"
    cfg = load_config(str(cfg_path))
    assert isinstance(cfg, Config)
    assert len(cfg.keywords) > 0
    assert "792756" in cfg.keywords
    assert cfg.notifications.email.recipients == ["romanxdolezal@seznam.cz", "osickoviht@seznam.cz"]
    assert len(cfg.sources) >= 17
    assert {"celakovice", "lazne_tousen", "praha14"} <= {s.id for s in cfg.sources}

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

def test_load_config_includes_lazne_tousen():
    cfg_path = Path(__file__).parent.parent / "config.yaml"
    cfg = load_config(str(cfg_path))
    ids = [s.id for s in cfg.sources]
    assert "lazne_tousen" in ids
    lazne_tousen = next(s for s in cfg.sources if s.id == "lazne_tousen")
    assert lazne_tousen.name == "Městys Lázně Toušeň"
    assert lazne_tousen.type == "galileo"
    assert lazne_tousen.url == "https://www.laznetousen.cz/obecni-urad/uredni-deska/"
    assert lazne_tousen.category == "neighbor"

def test_load_config_includes_praha14():
    cfg_path = Path(__file__).parent.parent / "config.yaml"
    cfg = load_config(str(cfg_path))
    ids = [s.id for s in cfg.sources]
    assert "praha14" in ids
    praha14 = next(s for s in cfg.sources if s.id == "praha14")
    assert praha14.name == "MČ Praha 14"
    assert praha14.type == "generic_html"
    assert praha14.url == "https://www.praha14.cz/uredni-deska/"
    assert praha14.category == "praha"

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


def test_web_json_path_is_relative_to_repository_database(tmp_path):
    db_path = tmp_path / "data" / "watchdog.db"

    assert web_json_path_for_db(str(db_path)) == tmp_path / "web" / "public" / "data.json"
