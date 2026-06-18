import functools
import os
import socket
import time
from contextlib import contextmanager
from datetime import timedelta
from typing import Callable, Generator

from .core import send_message


def _build_message(name: str, success: bool, elapsed: float) -> str:
    host = socket.gethostname()
    duration = str(timedelta(seconds=int(elapsed)))
    icon = "✅" if success else "❌"
    status = "SUCCESS" if success else "FAILED"

    lines = [
        f"{icon} <b>Experiment {status}</b>",
        "",
        f"<b>Job:</b> {name}",
        f"<b>Host:</b> {host}",
        f"<b>Duration:</b> {duration}",
    ]

    slurm_id = os.environ.get("SLURM_JOB_ID", "")
    slurm_name = os.environ.get("SLURM_JOB_NAME", "")
    if slurm_id:
        lines.append(f"<b>SLURM ID:</b> {slurm_id}")
    if slurm_name and slurm_name != name:
        lines.append(f"<b>SLURM Name:</b> {slurm_name}")

    return "\n".join(lines)


@contextmanager
def notify(name: str = "experiment") -> Generator[None, None, None]:
    start = time.time()
    try:
        yield
        send_message(_build_message(name, True, time.time() - start))
    except Exception:
        send_message(_build_message(name, False, time.time() - start))
        raise


def notify_on_complete(name_or_func=None) -> Callable:
    """Decorator with optional name argument.

    Usage:
        @notify_on_complete
        def main(): ...

        @notify_on_complete("ResNet training")
        def main(): ...
    """
    if callable(name_or_func):
        func = name_or_func
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with notify(func.__name__):
                return func(*args, **kwargs)
        return wrapper

    label = name_or_func or "experiment"

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with notify(label):
                return func(*args, **kwargs)
        return wrapper

    return decorator
