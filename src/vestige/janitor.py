"""Background cleanup of expired snapshots."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from pathlib import Path

from .config import Settings
from .storage import Storage

log = logging.getLogger(__name__)


async def _sweep(storage: Storage, settings: Settings) -> int:
    paths = await storage.purge_older_than(settings.retention_days * 86400)
    for raw in paths:
        with contextlib.suppress(OSError):
            Path(raw).unlink(missing_ok=True)
    return len(paths)


async def run_janitor(storage: Storage, settings: Settings) -> None:
    """Drop snapshots older than the retention window, forever."""
    if settings.retention_days <= 0:
        log.info("retention disabled, janitor is not running")
        return

    interval = max(settings.cleanup_interval_minutes, 1) * 60
    while True:
        try:
            removed = await _sweep(storage, settings)
            if removed:
                log.info("janitor removed %s cached files", removed)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("janitor sweep failed")
        await asyncio.sleep(interval)
