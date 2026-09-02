import os
import tempfile

# The DB path is read from the env at import time by mirror_api, so this must
# happen before any application module is imported.
os.environ["DATABASE_DIR"] = tempfile.mkdtemp(prefix="mirrorapi-test-")

import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from main import app
from mirror_db import engine


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client

    async def _clean():
        try:
            async with engine.begin() as conn:
                await conn.execute(text("DELETE FROM mirror_pairs"))
        except OperationalError:
            pass

    asyncio.run(_clean())
