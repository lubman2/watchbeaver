import io
import hashlib
import logging
from typing import Tuple, Optional
import pypdf

logger = logging.getLogger(__name__)

class PDFExtractor:
    """
    Extrahuje text z PDF streamu nebo souboru.
    Pokud je text prázdný (naskenované PDF), vrací prázdný řetězec a ocr_needed=True.
    """
    def extract_text_from_bytes(self, data: bytes) -> Tuple[str, bool]:
        if not data:
            return "", False
            
        text_parts = []
        try:
            reader = pypdf.PdfReader(io.BytesIO(data))
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        except Exception as e:
            logger.warning(f"Error reading PDF text: {e}")
            return "", True

        full_text = "\n".join(text_parts).strip()
        ocr_needed = len(full_text) < 20 and len(reader.pages) > 0
        return full_text, ocr_needed

    @staticmethod
    def compute_hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
