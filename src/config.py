from dataclasses import dataclass, field
from typing import List, Optional
import yaml
from pathlib import Path

@dataclass
class TelegramConfig:
    enabled: bool = True
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None

@dataclass
class EmailConfig:
    enabled: bool = True
    recipients: List[str] = field(default_factory=lambda: ["romanxdolezal@seznam.cz"])
    cc: List[str] = field(default_factory=lambda: ["lubos.soustruznik@myflow.cz"])
    sender_name: str = "Klára virtuální asistentka Luboše S."
    sender_email: str = "klara.superzelva@gmail.com"

@dataclass
class NotificationsConfig:
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    email: EmailConfig = field(default_factory=EmailConfig)

@dataclass
class SourceConfig:
    id: str
    name: str
    type: str
    url: str
    ofn_url: Optional[str] = None
    category: str = "other"

@dataclass
class Config:
    keywords: List[str]
    notifications: NotificationsConfig
    sources: List[SourceConfig]

def load_config(path: str) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    tg_data = data.get("notifications", {}).get("telegram", {})
    email_data = data.get("notifications", {}).get("email", {})
    
    notifications = NotificationsConfig(
        telegram=TelegramConfig(**tg_data),
        email=EmailConfig(
            **{**{"recipients": ["romanxdolezal@seznam.cz"]}, **email_data}
        )
    )
    
    sources = [SourceConfig(**s) for s in data.get("sources", [])]
    
    return Config(
        keywords=data.get("keywords", []),
        notifications=notifications,
        sources=sources
    )
