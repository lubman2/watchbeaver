import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

class EmailNotifier:
    """
    Odesílá detailní notifikaci s přílohami Romanu Doležalovi a Osičkovým od Kláry.
    Odesílatel: Klára virtuální asistentka Luboše S. <klara.superzelva@gmail.com>
    Příjemci: romanxdolezal@seznam.cz, osickoviht@seznam.cz
    Kopie: lubos.soustruznik@myflow.cz
    """
    def __init__(
        self,
        sender_name: str = "Klára virtuální asistentka Luboše S.",
        sender_email: str = "klara.superzelva@gmail.com",
        recipients: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None
    ):
        self.sender_name = sender_name
        self.sender_email = sender_email
        self.recipients = recipients or ["romanxdolezal@seznam.cz"]
        self.cc = cc or ["lubos.soustruznik@myflow.cz"]
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", smtp_port))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER") or os.getenv("GMAIL_USER", sender_email)
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")

        if not self.smtp_password:
            # Check ~/.osobni-agenda/.env fallback
            agenda_env = os.path.expanduser("~/.osobni-agenda/.env")
            if os.path.exists(agenda_env):
                with open(agenda_env, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("GMAIL_APP_PASSWORD="):
                            self.smtp_password = line.split("=", 1)[1].strip().strip('"').strip("'")
                        elif line.startswith("GMAIL_USER="):
                            self.smtp_user = line.split("=", 1)[1].strip().strip('"').strip("'")

    def build_message(
        self,
        source_name: str,
        notice_title: str,
        notice_url: str,
        keyword: str,
        snippet: str,
        attachments: Optional[List[Tuple[str, bytes]]] = None # List of (filename, bytes)
    ) -> MIMEMultipart:
        msg = MIMEMultipart()
        msg["From"] = f"{self.sender_name} <{self.sender_email}>"
        msg["To"] = ", ".join(self.recipients)
        if self.cc:
            msg["Cc"] = ", ".join(self.cc)
        msg["Subject"] = f"🦫 WatchBeaver ({source_name}): Zmínka k.ú. Zeleneč — {notice_title[:60]}"

        body = (
            f"Dobrý den,\n\n"
            f"automatický systém WatchBeaver pro monitoring úředních desek zaznamenal nový dokument, který zmiňuje katastrální území či obec Zeleneč / Mstětice.\n\n"
            f"--------------------------------------------------\n"
            f"Úřad / Zdroj: {source_name}\n"
            f"Název oznámení: {notice_title}\n"
            f"Detekované klíčové slovo: {keyword}\n"
            f"Odkaz na desku: {notice_url}\n\n"
            f"Úryvek textu s kontextem:\n"
            f"\"{snippet}\"\n"
            f"--------------------------------------------------\n\n"
            f"V příloze tohoto e-mailu zasíláme stažené podklady a relevantní PDF dokumenty k tomuto řízení.\n\n"
            f"S pozdravem,\n\n"
            f"Klára\n"
            f"virtuální asistentka Luboše Soustružníka (AI asistentka)\n"
            f"klara.superzelva@gmail.com\n"
        )
        msg.attach(MIMEText(body, "plain", "utf-8"))

        if attachments:
            for fname, data in attachments:
                part = MIMEApplication(data, Name=fname)
                part["Content-Disposition"] = f'attachment; filename="{fname}"'
                msg.attach(part)

        return msg

    def send_notification(
        self,
        source_name: str,
        notice_title: str,
        notice_url: str,
        keyword: str,
        snippet: str,
        attachments: Optional[List[Tuple[str, bytes]]] = None
    ) -> bool:
        if not self.smtp_password:
            logger.warning("SMTP_PASSWORD not set; email dispatch skipped (simulated/dry-run).")
            return False

        msg = self.build_message(source_name, notice_title, notice_url, keyword, snippet, attachments)
        recipients = self.recipients + self.cc

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.sender_email, recipients, msg.as_string())
            logger.info(f"Notification email successfully sent to {recipients}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return False
