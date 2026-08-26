import logging
import requests
from typing import Optional, List
from src.config import Config
from src.db import Database
from src.matcher import KeywordMatcher
from src.extractors.pdf_extractor import PDFExtractor
from src.extractors.ocr_engine import OCREngine
from src.notifiers.telegram import TelegramNotifier
from src.notifiers.mailer import EmailNotifier
from src.scrapers.base import BaseScraper
from src.scrapers.ofn import OFNScraper
from src.scrapers.galileo import GalileoScraper
from src.scrapers.generic_html import GenericHTMLScraper
from src.scrapers.eia import EIAScraper

logger = logging.getLogger(__name__)

class WatchdogPipeline:
    def __init__(self, config: Config, db: Database, dry_run: bool = False):
        self.config = config
        self.db = db
        self.dry_run = dry_run
        self.matcher = KeywordMatcher(config.keywords)
        self.pdf_extractor = PDFExtractor()
        self.ocr_engine = OCREngine()
        self.telegram = TelegramNotifier(
            bot_token=config.notifications.telegram.bot_token,
            chat_id=config.notifications.telegram.chat_id
        )
        self.mailer = EmailNotifier(
            sender_name=config.notifications.email.sender_name,
            sender_email=config.notifications.email.sender_email,
            recipients=config.notifications.email.recipients,
            cc=config.notifications.email.cc
        )

    def _get_scraper(self, source) -> BaseScraper:
        stype = source.type.lower()
        if stype == "ofn":
            return OFNScraper(source.id, source.name, source.url, ofn_url=source.ofn_url)
        elif stype == "galileo":
            return GalileoScraper(source.id, source.name, source.url)
        elif stype == "eia":
            return EIAScraper(source.id, source.name, source.url)
        else:
            return GenericHTMLScraper(source.id, source.name, source.url)

    def run_cycle(self):
        logger.info("Starting Watchdog scan cycle...")
        
        # 1. Init sources in DB
        for src in self.config.sources:
            self.db.upsert_source(src.id, src.name, src.type, src.url, src.ofn_url, src.category)

        total_new_notices = 0
        total_matches = 0

        # 2. Iterate through sources
        for src in self.config.sources:
            logger.info(f"Scanning source: {src.name} ({src.id})")
            scraper = self._get_scraper(src)
            try:
                notices = scraper.fetch_notices()
            except Exception as e:
                logger.error(f"Error fetching from {src.name}: {e}")
                continue

            for notice in notices:
                # Check if notice already seen
                if self.db.is_notice_seen(src.id, notice.external_id):
                    continue

                total_new_notices += 1
                logger.info(f"-> Found new notice: [{src.id}] {notice.title}")
                
                notice_id = self.db.insert_notice(
                    source_id=src.id,
                    external_id=notice.external_id,
                    title=notice.title,
                    url=notice.url,
                    posted_at=notice.posted_at
                )

                # Check notice title & description
                text_to_check = f"{notice.title} {notice.description or ''}"
                match = self.matcher.find_match(text_to_check)
                if match:
                    kw, snippet = match
                    logger.info(f"!!! MATCH in title/desc: '{kw}' on {src.name}")
                    match_id = self.db.insert_match(
                        notice_id=notice_id,
                        keyword=kw,
                        snippet=snippet,
                        source_context="notice_title"
                    )
                    total_matches += 1

                # Download & check attachments
                downloaded_attachments = []
                for att in notice.attachments:
                    try:
                        resp = requests.get(att.url, timeout=30, headers={"User-Agent": "ZelenecBoardWatchdog/1.0"})
                        if resp.status_code != 200:
                            continue
                        data = resp.content
                    except Exception as e:
                        logger.warning(f"Could not download attachment {att.url}: {e}")
                        continue

                    fhash = self.pdf_extractor.compute_hash(data)
                    if self.db.is_attachment_seen(fhash):
                        continue

                    # Extract text
                    extracted_text, ocr_needed = self.pdf_extractor.extract_text_from_bytes(data)
                    ocr_applied = 0
                    if ocr_needed:
                        ocr_text = self.ocr_engine.ocr_pdf_bytes(data)
                        if ocr_text:
                            extracted_text = f"{extracted_text}\n{ocr_text}".strip()
                            ocr_applied = 1

                    fname = att.filename or att.url.split("/")[-1] or "dokument.pdf"
                    if not fname.lower().endswith(".pdf"):
                        fname += ".pdf"

                    att_id = self.db.insert_attachment(
                        notice_id=notice_id,
                        url=att.url,
                        filename=fname,
                        file_hash=fhash,
                        extracted_text=extracted_text,
                        ocr_applied=ocr_applied
                    )

                    downloaded_attachments.append((fname, data))

                    # Match keyword in attachment text
                    att_match = self.matcher.find_match(extracted_text)
                    if att_match:
                        kw, snippet = att_match
                        logger.info(f"!!! MATCH in attachment {fname}: '{kw}' on {src.name}")
                        self.db.insert_match(
                            notice_id=notice_id,
                            attachment_id=att_id,
                            keyword=kw,
                            snippet=snippet,
                            source_context="attachment"
                        )
                        total_matches += 1

            self.db.update_source_checked(src.id)

        # 3. Dispatch notifications for unnotified matches
        self.dispatch_notifications()
        logger.info(f"Scan cycle finished. New notices: {total_new_notices}, Matches: {total_matches}")

        # 4. Export JSON for Web UI
        try:
            from src.exporter import export_db_to_json
            import datetime
            import sqlite3
            sqlite3.datetime = datetime
            web_json_path = str(self.config_path.parent / "web" / "public" / "data.json") if hasattr(self, "config_path") else "/Users/lubman/Projects/zelenec-board-watchdog/web/public/data.json"
            export_db_to_json(self.db.db_path, web_json_path)
            logger.info(f"Exported web data to {web_json_path}")
        except Exception as e:
            logger.warning(f"Failed to export web data JSON: {e}")

    def dispatch_notifications(self):
        unnotified = self.db.get_unnotified_matches()
        if not unnotified:
            return

        logger.info(f"Dispatching notifications for {len(unnotified)} matches...")
        for m in unnotified:
            match_id = m["id"]
            src_name = m["source_name"]
            n_title = m["notice_title"]
            n_url = m["notice_url"]
            kw = m["keyword"]
            snippet = m["snippet"]
            att_url = m.get("attachment_url")

            if self.dry_run:
                logger.info(f"[DRY-RUN] Would notify: {src_name} - {n_title} ({kw})")
                self.db.mark_match_notified(match_id, "telegram")
                self.db.mark_match_notified(match_id, "email")
                continue

            # Telegram
            if self.config.notifications.telegram.enabled:
                if self.telegram.send_notification(src_name, n_title, n_url, kw, snippet, att_url):
                    self.db.mark_match_notified(match_id, "telegram")

            # Email
            if self.config.notifications.email.enabled:
                if self.mailer.send_notification(src_name, n_title, n_url, kw, snippet):
                    self.db.mark_match_notified(match_id, "email")
