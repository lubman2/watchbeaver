import pytest
import json
from unittest.mock import patch, MagicMock
from src.scrapers.ofn import OFNScraper
from src.scrapers.galileo import GalileoScraper

def test_ofn_scraper_parsing():
    mock_ofn_data = {
        "informace": [
            {
                "id": "notice-001",
                "název": {"cs": "Územní řízení - přeložka silnice II/101"},
                "url": "https://edeska.stredoceskykraj.cz/doc/1",
                "vyvěšení": {"datum": "2026-08-25"},
                "přílohy": [
                    {
                        "url": "https://edeska.stredoceskykraj.cz/doc/1.pdf",
                        "název": {"cs": "Vyhláška.pdf"}
                    }
                ]
            }
        ]
    }
    
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_ofn_data
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp
        
        scraper = OFNScraper("kusk", "KÚSK", "https://edeska.stredoceskykraj.cz", ofn_url="https://edeska.stredoceskykraj.cz/deska.json")
        notices = scraper.fetch_notices()
        
        assert len(notices) == 1
        n = notices[0]
        assert n.external_id == "notice-001"
        assert n.title == "Územní řízení - přeložka silnice II/101"
        assert len(n.attachments) == 1
        assert n.attachments[0].url == "https://edeska.stredoceskykraj.cz/doc/1.pdf"

def test_galileo_scraper_parsing():
    html_content = """
    <html>
        <body>
            <div class="deska-polozka">
                <a href="/detail/123">Oznámení záměru stavby vodovodu</a>
                <a href="/files/priloha.pdf">Příloha záměru PDF</a>
            </div>
        </body>
    </html>
    """
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.content = html_content.encode("utf-8")
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp
        
        scraper = GalileoScraper("jirny", "Obec Jirny", "https://www.jirny.cz/uredni-deska/")
        notices = scraper.fetch_notices()
        assert len(notices) >= 1
        assert "Oznámení záměru" in notices[0].title
        assert len(notices[0].attachments) >= 1
