import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List
from src.scrapers.base import BaseScraper, RawNotice, RawAttachment

logger = logging.getLogger(__name__)

class GenericHTMLScraper(BaseScraper):
    """
    Obecný robustní HTML scraper pro úřední desky (Praha 20, Gordic infodesky a další).
    """
    def fetch_notices(self) -> List[RawNotice]:
        try:
            resp = requests.get(self.url, timeout=30, headers={"User-Agent": "ZelenecBoardWatchdog/1.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")
        except Exception as e:
            logger.error(f"Error scraping HTML board at {self.url}: {e}")
            return []

        notices = []
        # Hledáme všechny články, bloky nebo řádky
        blocks = soup.select("article, .post, .item, .record, tr, .entry, .notice")
        if not blocks:
            blocks = [soup]

        seen_urls = set()
        for idx, block in enumerate(blocks):
            links = block.find_all("a")
            for a in links:
                href = a.get("href", "")
                text = a.get_text(strip=True)
                if not href or len(text) < 4:
                    continue
                
                full_url = urljoin(self.url, href)
                if full_url in seen_urls:
                    continue
                
                # Ignorujeme navigaci, stránkování a obecné patičky
                if any(x in href.lower() for x in ["facebook", "twitter", "instagram", "login", "kontakt", "cookies", "mapa-stranek"]):
                    continue
                
                seen_urls.add(full_url)
                
                attachments = []
                if full_url.lower().endswith(".pdf"):
                    attachments.append(RawAttachment(url=full_url, filename=text))
                
                notices.append(RawNotice(
                    external_id=full_url,
                    title=text,
                    url=full_url,
                    attachments=attachments
                ))

        return notices
