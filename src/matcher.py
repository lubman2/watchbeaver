import re
from typing import List, Optional, Tuple

class KeywordMatcher:
    """
    Vyhledává explicitní shody klíčových slov a generuje kontextové úryvky (snippety).
    """
    def __init__(self, patterns: List[str]):
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in patterns]

    def find_match(self, text: str, snippet_context: int = 150) -> Optional[Tuple[str, str]]:
        """
        Vrací (matched_keyword, snippet) nebo None, pokud žádné slovo nebylo nalezeno.
        """
        if not text:
            return None

        for pattern in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                start = max(0, match.start() - snippet_context)
                end = min(len(text), match.end() + snippet_context)
                snippet = text[start:end].replace("\n", " ").strip()
                return match.group(0), f"...{snippet}..."

        return None
