"""
Pluggable email service.

Behaviour
---------
* If ``SENDGRID_API_KEY`` is set in the environment, the email is sent via
  the SendGrid v3 Web API using the ``sendgrid`` Python SDK.
* Otherwise, a formatted log block is printed to the console and a dict
  ``{'sent': False, 'logged': True}`` is returned.

Swapping to async
-----------------
Replace the synchronous ``SendGridAPIClient.send()`` call with an
``httpx.AsyncClient`` POST to ``https://api.sendgrid.com/v3/mail/send``
and change the function signature to ``async def send_email(...)``.
Update callers with ``await send_email(...)``.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the backend directory
_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env")

logger = logging.getLogger(__name__)


def send_email(recipient: str, subject: str, body: str) -> dict:
    """Send an email or log it to the console.

    Returns
    -------
    dict
        ``{'sent': True}`` on successful delivery, or
        ``{'sent': False, 'logged': True}`` when falling back to console.
    """
    api_key = os.getenv("SENDGRID_API_KEY", "").strip()
    from_email = os.getenv("EMAIL_FROM", "noreply@zipsheet.app").strip()

    if not api_key:
        # ── Console fallback ──────────────────────────
        print()
        print("=" * 50)
        print("=== EMAIL LOG (SendGrid not configured) ===")
        print("=" * 50)
        print(f"  To:      {recipient}")
        print(f"  From:    {from_email}")
        print(f"  Subject: {subject}")
        print("-" * 50)
        print(body)
        print("=" * 50)
        print()
        logger.info("Email logged to console (SENDGRID_API_KEY not set)")
        return {"sent": False, "logged": True}

    # ── SendGrid path ─────────────────────────────────
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=from_email,
            to_emails=recipient,
            subject=subject,
            plain_text_content=body,
        )
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)

        if response.status_code >= 400:
            raise RuntimeError(
                f"SendGrid returned {response.status_code}: {response.body}"
            )

        logger.info("Email sent to %s (status %s)", recipient, response.status_code)
        return {"sent": True}

    except Exception as exc:
        logger.exception("Failed to send email via SendGrid")
        raise RuntimeError(f"Email delivery failed: {exc}") from exc
