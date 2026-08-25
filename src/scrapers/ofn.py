import json
import logging
import requests
from typing import List
from src.scrapers.base import BaseScraper, RawNotice, RawAttachment

logger = logging.getLogger(__name__)

class OFNScraper(BaseScraper):
    """
    Scraper for Open Formal Data (Otevřená formální data - OFN) úředních desek.
    Docs: https://ofn.gov.cz/úřední-desky/
    """
    def fetch_notices(self) -> List[RawNotice]:
        ofn_url = self.options.get("ofn_url") or self.url
        try:
            resp = requests.get(ofn_url, timeout=30, headers={"User-Agent": "ZelenecBoardWatchdog/1.0"})
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"Error fetching OFN data from {ofn_url}: {e}")
            return []

        notices = []
        # OFN defines "informace" array
        items = data.get("informace", [])
        if not items and "položky" in data:
            items = data.get("položky", [])

        for item in items:
            ext_id = str(item.get("id") or item.get("identifikátor") or item.get("iri") or item.get("url", ""))
            
            # Title
            title = ""
            name_obj = item.get("název") or item.get("jméno") or item.get("title")
            if isinstance(name_obj, dict):
                title = name_obj.get("cs", "") or list(name_obj.values())[0]
            elif isinstance(name_obj, str):
                title = name_obj
                
            notice_url = item.get("url") or item.get("iri") or self.url
            
            # Dates
            posted_at = None
            if "vyvěšení" in item:
                vyv = item["vyvěšení"]
                if isinstance(vyv, dict):
                    posted_at = vyv.get("datum") or vyv.get("datum_a_čas")
                elif isinstance(vyv, str):
                    posted_at = vyv
            elif "datum_vyvěšení" in item:
                posted_at = item["datum_vyvěšení"]
                
            taken_down_at = None
            if "relevantní_do" in item:
                taken_down_at = item["relevantní_do"]
            elif "datum_sejmoutí" in item:
                taken_down_at = item["datum_sejmoutí"]

            # Attachments
            raw_attachments = []
            att_list = item.get("přílohy") or item.get("dokumenty") or []
            for att in att_list:
                att_url = att.get("url") or att.get("iri") or att.get("odkaz")
                if not att_url:
                    continue
                att_name = ""
                n_obj = att.get("název") or att.get("jméno")
                if isinstance(n_obj, dict):
                    att_name = n_obj.get("cs", "")
                elif isinstance(n_obj, str):
                    att_name = n_obj
                raw_attachments.append(RawAttachment(url=att_url, filename=att_name))

            if ext_id and title:
                notices.append(RawNotice(
                    external_id=ext_id,
                    title=title,
                    url=notice_url,
                    posted_at=posted_at,
                    taken_down_at=taken_down_at,
                    attachments=raw_attachments
                ))

        return notices
