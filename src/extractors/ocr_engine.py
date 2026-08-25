import logging
import io
from typing import Optional

logger = logging.getLogger(__name__)

class OCREngine:
    """
    Fallback OCR engine pro skenované dokumenty bez textové vrstvy.
    Používá pytesseract a pdf2image pokud jsou k dispozici v systému.
    """
    def __init__(self):
        self.available = False
        try:
            import pytesseract
            from pdf2image import convert_from_bytes
            self.pytesseract = pytesseract
            self.convert_from_bytes = convert_from_bytes
            self.available = True
        except ImportError:
            logger.warning("pytesseract or pdf2image not installed; OCR fallback disabled.")

    def ocr_pdf_bytes(self, data: bytes, max_pages: int = 5) -> str:
        if not self.available:
            return ""
            
        try:
            images = self.convert_from_bytes(data, first_page=1, last_page=max_pages)
            text_pages = []
            for img in images:
                txt = self.pytesseract.image_to_string(img, lang="ces+eng")
                if txt:
                    text_pages.append(txt)
            return "\n".join(text_pages).strip()
        except Exception as e:
            logger.warning(f"OCR processing failed: {e}")
            return ""
