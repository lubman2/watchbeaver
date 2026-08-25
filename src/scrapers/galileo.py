import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List
from src.scrapers.base import BaseScraper, RawNotice, RawAttachment

logger = logging.getLogger(__name__)

class GalileoScraper(BaseScraper):
    """
    Scraper pro desky běžící na systému Galileo Corporation (velmi časté u menších obcí).
    """
    def fetch_notices(self) -> List[RawNotice]:
        try:
            resp = requests.get(self.url, timeout=30, headers={"User-Agent": "ZelenecBoardWatchdog/1.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")
        except Exception as e:
            logger.error(f"Error scraping Galileo board at {self.url}: {e}")
            return []

        notices = []
        # Vybereme položky
        items = soup.select(".deska-polozka, .board-item, .item-deska, .item, tr")
        if not items:
            items = [soup]

        for idx, item in enumerate(items):
            links = item.find_all("a")
            if not links:
                continue
                
            main_link = None
            pdf_links = []
            
            for a in links:
                href = a.get("href", "")
                if not href:
                    continue
                full_url = urljoin(self.url, href)
                if full_url.lower().endswith(".pdf") or "download" in full_url.lower():
                    pdf_links.append(RawAttachment(url=full_url, filename=a.get_text(strip=True)))
                elif not main_link and len(a.get_text(strip=True)) > 3:
                    main_link = a

            if not main_link and not pdf_links:
                continue
                
            title = main_link.get_text(strip=True) if main_link else (pdf_links[0].filename or f"Oznámení {idx}")
            notice_url = urljoin(self.url, main_link.get("href")) if main_link else pdf_links[0].url
            
            notices.append(RawNotice(
                external_id=notice_url,
                title=title,
                url=notice_url,
                description=item.get_text(" ", strip=True),
                attachments=pdf_links
            ))

        return notices
