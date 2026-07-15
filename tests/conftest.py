import os
import tempfile

# The DB path is read from the env at import time by mirror_api, so this must
# happen before any application module is imported.
os.environ["DATABASE_DIR"] = tempfile.mkdtemp(prefix="mirrorapi-test-")

import asyncio  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402

from main import app  # noqa: E402
from mirror_api import engine  # noqa: E402


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
