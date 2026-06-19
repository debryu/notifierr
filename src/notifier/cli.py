import json
import os
import socket
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

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


@cli.command()
@click.option("--job-id", required=True, help="SLURM job ID to watch")
@click.option("--queue-dir", default=str(Path.home() / ".notifier_queue"),
              show_default=True, help="Directory containing queue files")
@click.option("--interval", default=30, show_default=True, help="Poll interval in seconds")
def watch(job_id: str, queue_dir: str, interval: int) -> None:
    """Watch a SLURM job and forward its queued notifications in real time.

    Designed for GPU nodes that have no internet access: the job writes
    messages to a queue file (~/.notifier_queue/<JOB_ID>.jsonl) and this
    command, running on the login node, drains the file and sends them to
    Telegram as they arrive. Sends a final success/failure message when the
    job ends.
    """
    queue_file = Path(queue_dir) / f"{job_id}.jsonl"
    seen = 0

    click.echo(f"[notifier] Watching job {job_id} (queue: {queue_file}, interval: {interval}s)")

    while True:
        # Drain any new lines from the queue file
        if queue_file.exists():
            lines = queue_file.read_text().splitlines()
            for line in lines[seen:]:
                try:
                    data = json.loads(line)
                    send_message(data["text"])
                    click.echo(f"[notifier] Forwarded queued message.")
                except Exception as e:
                    click.echo(f"[notifier] Failed to forward message: {e}", err=True)
            seen = len(lines)

        # Check if the job is still in the queue
        result = subprocess.run(
            ["squeue", "-j", job_id, "--noheader"],
            capture_output=True, text=True,
        )
        if job_id not in result.stdout:
            # Job is gone — do a final drain, then report status via sacct
            if queue_file.exists():
                lines = queue_file.read_text().splitlines()
                for line in lines[seen:]:
                    try:
                        data = json.loads(line)
                        send_message(data["text"])
                        click.echo(f"[notifier] Forwarded queued message.")
                    except Exception as e:
                        click.echo(f"[notifier] Failed to forward message: {e}", err=True)

            time.sleep(5)  # give sacct a moment to register the job
            sacct = subprocess.run(
                ["sacct", "-j", job_id, "--format=State", "--noheader", "-P"],
                capture_output=True, text=True,
            )
            state_lines = [
                l.strip() for l in sacct.stdout.splitlines()
                if l.strip() and "." not in l
            ]
            state = state_lines[0] if state_lines else "UNKNOWN"
            success = state == "COMPLETED"
            icon = "✅" if success else "❌"
            send_message(f"{icon} <b>SLURM job {job_id} {state.lower()}</b>")
            click.echo(f"[notifier] Job {job_id} finished ({state}). Exiting.")
            break

        time.sleep(interval)
