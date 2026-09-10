from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio

from vestige.storage import Connection, Storage


@pytest_asyncio.fixture
async def storage(tmp_path: Path) -> AsyncIterator[Storage]:
    store = Storage(tmp_path / "test.db")
    await store.connect()
    try:
        yield store
    finally:
        await store.close()


@pytest.fixture
def connection() -> Connection:
    return Connection(
        connection_id="conn-1",
        owner_id=42,
        owner_chat_id=42,
        is_enabled=True,
        can_read=True,
    )
