import imaplib
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import List, Tuple

import yagmail

from ..config import settings


def send_email(
    to_address: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
    attachments: List[Path] | None = None,
) -> None:
    """
    Send email via Gmail using yagmail.
    """
    if not settings.gmail_address or not settings.gmail_app_password:
        raise RuntimeError("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set")

    yag = yagmail.SMTP(settings.gmail_address, settings.gmail_app_password)
    contents: List[str | Path] = []
    if body_html:
        contents.append(body_html)
    else:
        contents.append(body_text)
    if attachments:
        contents.extend(attachments)

    yag.send(to=to_address, subject=subject, contents=contents)


def poll_inbox(max_messages: int = 10) -> List[Tuple[str, str]]:
    """
    Minimal IMAP polling to fetch recent messages.
    Returns list of (from_address, subject).
    """
    if not settings.gmail_address or not settings.gmail_app_password:
        return []

    mail = imaplib.IMAP4_SSL(settings.gmail_imap_host, settings.gmail_imap_port)
    mail.login(settings.gmail_address, settings.gmail_app_password)
    mail.select("inbox")
    result, data = mail.search(None, "ALL")
    if result != "OK":
        return []

    msg_ids = data[0].split()[-max_messages:]
    results: List[Tuple[str, str]] = []

    for msg_id in msg_ids:
        res, msg_data = mail.fetch(msg_id, "(BODY[HEADER.FIELDS (FROM SUBJECT)])")
        if res != "OK":
            continue
        raw = msg_data[0][1].decode("utf-8", errors="ignore")
        from_line = ""
        subject_line = ""
        for line in raw.splitlines():
            if line.lower().startswith("from:"):
                from_line = line[5:].strip()
            if line.lower().startswith("subject:"):
                subject_line = line[8:].strip()
        if from_line or subject_line:
            results.append((from_line, subject_line))

    mail.logout()
    return results

