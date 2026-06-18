import os
import socket
import subprocess
import sys
import time
from datetime import timedelta

import click

from .core import send_message
from .hooks import _build_message


@click.group()
def cli():
    """Telegram notifications for ML experiments."""


@cli.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("command", nargs=-1, required=True, type=click.UNPROCESSED)
@click.option("--name", "-n", default=None, help="Label shown in notification (default: first arg)")
def run(command: tuple, name: str | None) -> None:
    """Run COMMAND and notify on completion (success or failure)."""
    label = name or command[0]
    host = socket.gethostname()
    slurm_id = os.environ.get("SLURM_JOB_ID", "")

    click.echo(f"[notifier] {host} | job: {label}" + (f" | slurm: {slurm_id}" if slurm_id else ""))

    start = time.time()
    result = subprocess.run(list(command))
    elapsed = time.time() - start

    msg = _build_message(label, result.returncode == 0, elapsed)
    send_message(msg)

    sys.exit(result.returncode)


@cli.command()
@click.argument("message")
def send(message: str) -> None:
    """Send a custom Telegram message."""
    ok = send_message(message)
    if ok:
        click.echo("[notifier] Message sent.")
    else:
        sys.exit(1)


@cli.command()
def test() -> None:
    """Send a test message to verify credentials and connectivity."""
    host = socket.gethostname()
    ok = send_message(f"✅ <b>Notifier is working!</b>\n\n<b>Host:</b> {host}")
    if ok:
        click.echo("[notifier] Test message sent successfully.")
    else:
        click.echo("[notifier] Failed — check your credentials in ~/.notifier.env", err=True)
        sys.exit(1)
