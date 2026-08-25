import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List
from src.scrapers.base import BaseScraper, RawNotice, RawAttachment

logger = logging.getLogger(__name__)

class EIAScraper(BaseScraper):
    """
    Scraper pro informační systém EIA/SEA (CENIA / MŽP).
    Sleduje záměry ve Středočeském kraji a Praze.
    """
    def fetch_notices(self) -> List[RawNotice]:
        # CENIA přehled záměrů ve Středočeském kraji (kód kraje STC / PHA)
        search_url = "https://portal.cenia.cz/eiasea/view/eia100_cr"
        try:
            resp = requests.get(search_url, timeout=30, headers={"User-Agent": "ZelenecBoardWatchdog/1.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")
        except Exception as e:
            logger.error(f"Error scraping EIA system: {e}")
            return []

        notices = []
        rows = soup.select("table.seznam tr, table tr")
        for idx, row in enumerate(rows):
            links = row.find_all("a")
            if not links:
                continue
            
            main_link = links[0]
            href = main_link.get("href", "")
            title = row.get_text(" ", strip=True)
            if not href or len(title) < 5:
                continue

            full_url = urljoin(search_url, href)
            notices.append(RawNotice(
                external_id=full_url,
                title=title,
                url=full_url,
                description=title
            ))

        return notices
