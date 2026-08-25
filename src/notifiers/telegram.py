import logging
import os
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """
    Odesílá okamžité notifikace na Telegram.
    Token a chat_id bere primárně z parametrů, případně z ENV (TG_BOT_TOKEN / TG_CHAT_ID).
    """
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TG_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TG_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.bot_token else None

    def send_notification(self, source_name: str, notice_title: str, notice_url: str, keyword: str, snippet: str, doc_url: Optional[str] = None) -> bool:
        # Load from kravobot.env if not set
        if not self.bot_token or not self.chat_id:
            env_file = os.path.expanduser("~/.claude/kravobot.env")
            if os.path.exists(env_file):
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("TELEGRAM_BOT_TOKEN="):
                            self.bot_token = line.split("=", 1)[1].strip().strip('"').strip("'")
                        elif line.startswith("TELEGRAM_CHAT_ID="):
                            self.chat_id = line.split("=", 1)[1].strip().strip('"').strip("'")
                if self.bot_token:
                    self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram notifier: bot_token or chat_id missing, skipping send.")
            return False

        text = (
            f"🦫 **WatchBeaver — ZELENEČ**\n\n"
            f"🏛 **Úřad:** {source_name}\n"
            f"📄 **Záměr / Oznámení:** {notice_title}\n"
            f"🎯 **Klíčové slovo:** `{keyword}`\n\n"
            f"💬 **Kontext:**\n_{snippet}_\n\n"
            f"🔗 [Odkaz na oznámení]({notice_url})"
        )
        if doc_url and doc_url != notice_url:
            text += f"\n📎 [Příloha / Dokument]({doc_url})"

        try:
            resp = requests.post(self.api_url, json={
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False
            }, timeout=15)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False
