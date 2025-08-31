import os
import aiofiles.os as async_os
import fnmatch
import signal
import asyncio
import subprocess
import logging

from typing import Any


logger = logging.getLogger(__name__)


async def iter_glob(path, pattern):
    dirs = await async_os.scandir(path)
    for entry in dirs:
        if fnmatch.fnmatch(entry.name, pattern):
            yield entry


async def kill_process(system_typ: str, process_id: Any) -> None:
    try:
        if system_typ == "nt":
            # Kill entire process tree on Windows
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process_id)],
                capture_output=True,
            )
        else:
            # First try graceful termination
            pgid = os.getpgid(process_id)
            os.kill(pgid, signal.SIGTERM)
            await asyncio.sleep(5)  # Give it 5 seconds

            # Then force kill if still running
            try:
                os.kill(pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass  # Already terminated
    except ProcessLookupError:
        logger.info(f"Failed to kill process group with PID: {process_id}")
