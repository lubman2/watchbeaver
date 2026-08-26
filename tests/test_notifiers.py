import pytest
from src.notifiers.mailer import EmailNotifier

def test_email_message_structure():
    mailer = EmailNotifier(
        recipients=["romanxdolezal@seznam.cz", "osickoviht@seznam.cz"],
        cc=["lubos.soustruznik@myflow.cz"]
    )
    
    msg = mailer.build_message(
        source_name="MěÚ Brandýs nad Labem",
        notice_title="Stavební řízení propojky",
        notice_url="https://infodeska.brandysko.cz/doc/1",
        keyword="Zeleneč",
        snippet="...v katastrálním území Zeleneč...",
        attachments=[("rozhodnuti.pdf", b"%PDF-dummy")]
    )
    
    assert msg["To"] == "romanxdolezal@seznam.cz, osickoviht@seznam.cz"
    assert "lubos.soustruznik@myflow.cz" in msg["Cc"]
    assert "Klára" in msg["From"]
    assert "Zeleneč" in msg["Subject"]
    assert len(msg.get_payload()) == 2 # text part + attachment part
