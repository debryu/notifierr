import json
import os
import sys
import time
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


def _queue_path() -> Path | None:
    """Returns the queue file path when inside a SLURM job, else None."""
    job_id = os.environ.get("SLURM_JOB_ID")
    if not job_id:
        return None
    queue_dir = Path(os.environ.get("NOTIFIER_QUEUE_DIR", Path.home() / ".notifier_queue"))
    queue_dir.mkdir(parents=True, exist_ok=True)
    return queue_dir / f"{job_id}.jsonl"


def _queue_message(text: str) -> None:
    """Append a message to the SLURM job's queue file for the login-node watcher."""
    path = _queue_path()
    if path is None:
        return
    with open(path, "a") as f:
        f.write(json.dumps({"ts": time.time(), "text": text}) + "\n")


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
        path = _queue_path()
        if path is not None:
            _queue_message(text)
            print(f"[notifier] No internet (SLURM job) — queued to {path}", file=sys.stderr)
        else:
            print(f"[notifier] Failed to send message: {exc}", file=sys.stderr)
        return False