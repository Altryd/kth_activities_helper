import asyncio
import os

import pytest
from sqlalchemy import text

from backend.db_engine import create_db_engine

pytestmark = pytest.mark.asyncio


async def test_first_query_recovers_closed_idle_connection(tmp_path):
    engine = create_db_engine(f"sqlite+aiosqlite:///{tmp_path / 'pool.db'}")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("CREATE TABLE counter (value INTEGER)"))
            await conn.execute(text("INSERT INTO counter VALUES (7)"))
            await conn.commit()
            raw = await conn.get_raw_connection()
            old_driver = raw.driver_connection
        # Simulate the server closing an idle, pooled connection.
        await old_driver.close()
        async with engine.connect() as conn:
            assert (await conn.execute(text("SELECT value FROM counter"))).scalar_one() == 7
            assert (await conn.get_raw_connection()).driver_connection is not old_driver
    finally:
        await engine.dispose()


async def test_mysql_idle_timeout_when_test_database_is_available():
    url = os.getenv("TEST_MYSQL_URL")
    if not url:
        pytest.skip("Set TEST_MYSQL_URL to an isolated mysql+asyncmy test database")
    engine = create_db_engine(url, recycle_seconds=3600)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SET SESSION wait_timeout = 1"))
            old_id = (await conn.execute(text("SELECT CONNECTION_ID()"))).scalar_one()
        await asyncio.sleep(2)
        async with engine.connect() as conn:
            assert (await conn.execute(text("SELECT 1"))).scalar_one() == 1
            assert (await conn.execute(text("SELECT CONNECTION_ID()"))).scalar_one() != old_id
    finally:
        await engine.dispose()
