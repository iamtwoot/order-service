import asyncio
import signal
from contextlib import suppress


def cancel_on_sigterm() -> None:
    task = asyncio.current_task()
    if task is None:
        raise RuntimeError("cancel_on_sigterm() must be called inside a task")
    with suppress(NotImplementedError):
        asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, task.cancel)
