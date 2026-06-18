import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


def _load_env() -> None:
    explicit = os.environ.get("NOTIFIER_ENV_FILE")
    if explicit:
        load_dotenv(explicit, override=False)
        return

    for candidate in [Path.home() / ".notifier.env", Path.cwd() / ".env"]:
        if candidate.exists():
            load_dotenv(candidate, override=False)
            return


def get_config() -> tuple[str, str]:
    _load_env()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are not set.\n"
            "Create ~/.notifier.env with:\n"
            "  TELEGRAM_BOT_TOKEN=your_token\n"
            "  TELEGRAM_CHAT_ID=your_chat_id\n"
            "Or set NOTIFIER_ENV_FILE to point to your .env file."
        )
    return token, chat_id


def send_message(text: str) -> bool:
    try:
        token, chat_id = get_config()
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:
        print(f"[notifier] Failed to send message: {exc}", file=sys.stderr)
        return False
