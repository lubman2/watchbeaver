from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

@dataclass
class RawAttachment:
    url: str
    filename: Optional[str] = None

@dataclass
class RawNotice:
    external_id: str
    title: str
    url: str
    posted_at: Optional[str] = None
    taken_down_at: Optional[str] = None
    description: Optional[str] = None
    attachments: List[RawAttachment] = field(default_factory=list)

class BaseScraper(ABC):
    def __init__(self, source_id: str, name: str, url: str, **kwargs):
        self.source_id = source_id
        self.name = name
        self.url = url
        self.options = kwargs

    @abstractmethod
    def fetch_notices(self) -> List[RawNotice]:
        """Fetch and return list of notices currently published on board."""
        pass
