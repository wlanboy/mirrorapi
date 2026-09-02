"""Domain logic for matching and expiring saved mirror pairs."""

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mirror_db import WILDCARD, MirrorPair

DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60  # 1 week


def utcnow() -> datetime:
    """Naive UTC timestamp, kept tz-naive for consistent SQLite comparisons."""
    return datetime.now(UTC).replace(tzinfo=None)


def expires_at(ttl_seconds: int | None) -> datetime:
    """Resolves a pair's expiry timestamp from a requested TTL (or the default)."""
    return utcnow() + timedelta(seconds=ttl_seconds or DEFAULT_TTL_SECONDS)


def hash_request(request_data) -> str:
    """Generates a consistent hash from the request body."""
    if request_data is None:
        return "None"
    return json.dumps(request_data, sort_keys=True)


def method_key(method: str | None) -> str:
    """Normalizes a method for matching, or WILDCARD if unspecified (matches any method)."""
    return method.upper() if method else WILDCARD


def query_key(query_params: dict[str, str] | None) -> str:
    """Normalizes query parameters for matching, or WILDCARD if unspecified (matches any query)."""
    if not query_params:
        return WILDCARD
    return json.dumps(dict(query_params), sort_keys=True)


async def find_matching_pair(
    db: AsyncSession,
    request_data,
    method: str,
    query_params: dict[str, str]
) -> MirrorPair | None:
    """
    Finds the saved pair matching the request body, method and query params.

    A pair saved without a method/query constraint (WILDCARD) matches any
    actual method/query. Among several matches, the most specific one wins.
    """
    actual_method_key = method_key(method)
    actual_query_key = query_key(query_params)

    result = await db.execute(
        select(MirrorPair).where(
            MirrorPair.request_hash == hash_request(request_data),
            MirrorPair.method_key.in_([WILDCARD, actual_method_key]),
            MirrorPair.query_key.in_([WILDCARD, actual_query_key]),
            MirrorPair.expires_at > utcnow(),
        )
    )
    candidates = result.scalars().all()
    if not candidates:
        return None

    def specificity(pair: MirrorPair) -> int:
        return (pair.method_key != WILDCARD) + (pair.query_key != WILDCARD)

    return max(candidates, key=specificity)
