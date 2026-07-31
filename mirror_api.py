import json
import os
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import Text, UniqueConstraint, delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from schemas import MirrorSaveRequest

DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60  # 1 week

DATABASE_DIR = os.environ.get("DATABASE_DIR", "/data")
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(DATABASE_DIR, 'mirror_data.db')}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


WILDCARD = "*"


class MirrorPair(Base):
    __tablename__ = 'mirror_pairs'
    __table_args__ = (
        UniqueConstraint('request_hash', 'method_key', 'query_key', name='uq_mirror_pair_match'),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_hash: Mapped[str] = mapped_column(nullable=False)
    method_key: Mapped[str] = mapped_column(nullable=False, default=WILDCARD)
    query_key: Mapped[str] = mapped_column(nullable=False, default=WILDCARD)
    request_data: Mapped[str] = mapped_column(Text, nullable=False)
    response_data: Mapped[str] = mapped_column(Text, nullable=False)
    response_status: Mapped[int] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False, index=True)


def utcnow() -> datetime:
    """Naive UTC timestamp, kept tz-naive for consistent SQLite comparisons."""
    return datetime.now(UTC).replace(tzinfo=None)


async def init_db():
    """Initialize the database and create tables."""
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for getting database session."""
    async with async_session() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]


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


mirror_router = APIRouter(prefix="/mirror", tags=["mirror"])


@mirror_router.post("/save", status_code=201)
async def mirror_save(
    data: MirrorSaveRequest,
    db: DbSession
):
    """
    Save a request/response pair for later retrieval.

    By default the pair matches a request with the same body regardless of
    HTTP method or query parameters. Set `request.method` and/or
    `request.query_params` to only match requests with those values, which
    allows saving distinct pairs for the same body (e.g. one per method).

    Expires after `request.ttl_seconds` (default 1 week) and is then ignored
    by lookups; use `POST /mirror/cleanup` to purge expired pairs.
    """
    request_data = data.request.request_data
    response_data = data.response.response_data
    response_status = data.response.response_status

    ttl_seconds = data.request.ttl_seconds
    if ttl_seconds is not None and ttl_seconds <= 0:
        return JSONResponse(
            content={"error": "ttl_seconds must be a positive integer."},
            status_code=400
        )

    try:
        pair = MirrorPair(
            request_hash=hash_request(request_data),
            method_key=method_key(data.request.method),
            query_key=query_key(data.request.query_params),
            request_data=json.dumps(request_data),
            response_data=json.dumps(response_data),
            response_status=response_status,
            expires_at=utcnow() + timedelta(seconds=ttl_seconds or DEFAULT_TTL_SECONDS)
        )
        db.add(pair)
        await db.commit()
        return {"message": "Request/Response pair saved."}
    except SQLAlchemyError as e:
        await db.rollback()
        if 'UNIQUE constraint' in str(e):
            return JSONResponse(
                content={"error": "A pair with this request, method and query already exists."},
                status_code=409
            )
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


@mirror_router.post("/delete")
async def mirror_delete(
    request: Request,
    db: DbSession
):
    """
    Delete all saved pairs for a request body.

    Removes every pair saved for this body, regardless of the method/query
    constraint it was saved with (there may be several, e.g. one per method).
    """
    try:
        request_data = await request.json()
        if request_data is None:
            return JSONResponse(
                content={"error": "Request body cannot be empty."},
                status_code=400
            )
    except json.JSONDecodeError:
        return JSONResponse(
            content={"error": "Invalid JSON in request body."},
            status_code=400
        )

    result = await db.execute(
        select(MirrorPair).where(MirrorPair.request_hash == hash_request(request_data))
    )
    pairs = result.scalars().all()

    if not pairs:
        return JSONResponse(
            content={"error": "No matching pair found to delete."},
            status_code=404
        )

    for pair in pairs:
        await db.delete(pair)
    await db.commit()
    return {"message": "Pair deleted successfully."}


@mirror_router.get("/list")
async def mirror_list(db: DbSession):
    """List all saved, non-expired request/response pairs."""
    result = await db.execute(
        select(MirrorPair)
        .where(MirrorPair.expires_at > utcnow())
        .order_by(MirrorPair.id)
    )
    pairs = result.scalars().all()
    return [
        {
            "id": pair.id,
            "method": None if pair.method_key == WILDCARD else pair.method_key,
            "query_params": None if pair.query_key == WILDCARD else json.loads(pair.query_key),
            "request_data": json.loads(pair.request_data),
            "response_data": json.loads(pair.response_data),
            "response_status": pair.response_status,
            "expires_at": pair.expires_at.isoformat() + "Z",
        }
        for pair in pairs
    ]


@mirror_router.post("/cleanup")
async def mirror_cleanup(db: DbSession):
    """Delete all expired pairs and report how many were removed."""
    result = await db.execute(select(MirrorPair.id).where(MirrorPair.expires_at <= utcnow()))
    expired_ids = result.scalars().all()
    if expired_ids:
        await db.execute(delete(MirrorPair).where(MirrorPair.id.in_(expired_ids)))
        await db.commit()
    return {"deleted": len(expired_ids)}


@mirror_router.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def mirror_lookup(
    request: Request,
    db: DbSession
):
    """
    Look up and return a saved response for a matching request.

    Matches on body, HTTP method and query parameters. A pair saved without
    a method/query constraint matches any method/query for that body; among
    several matches, the most specific one wins.
    """
    try:
        request_data = await request.json()
    except json.JSONDecodeError:
        body_bytes = await request.body()
        request_data = body_bytes.decode("utf-8") if body_bytes else ""

    pair = await find_matching_pair(db, request_data, request.method, dict(request.query_params))

    if not pair:
        return JSONResponse(
            content={"error": "No mirrored response found for this request."},
            status_code=404
        )

    response_data = json.loads(pair.response_data)
    return JSONResponse(content=response_data, status_code=pair.response_status)
