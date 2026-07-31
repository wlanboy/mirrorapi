import json
import os
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import Text, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from schemas import MirrorSaveRequest

DATABASE_DIR = os.environ.get("DATABASE_DIR", "/data")
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(DATABASE_DIR, 'mirror_data.db')}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class MirrorPair(Base):
    __tablename__ = 'mirror_pairs'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_hash: Mapped[str] = mapped_column(unique=True, nullable=False)
    request_data: Mapped[str] = mapped_column(Text, nullable=False)
    response_data: Mapped[str] = mapped_column(Text, nullable=False)
    response_status: Mapped[int] = mapped_column(nullable=False)


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


mirror_router = APIRouter(prefix="/mirror", tags=["mirror"])


@mirror_router.post("/save", status_code=201)
async def mirror_save(
    data: MirrorSaveRequest,
    db: DbSession
):
    """Save a request/response pair for later retrieval."""
    request_data = data.request.request_data
    response_data = data.response.response_data
    response_status = data.response.response_status
    request_hash = hash_request(request_data)

    try:
        pair = MirrorPair(
            request_hash=request_hash,
            request_data=json.dumps(request_data),
            response_data=json.dumps(response_data),
            response_status=response_status
        )
        db.add(pair)
        await db.commit()
        return {"message": "Request/Response pair saved."}
    except SQLAlchemyError as e:
        await db.rollback()
        if 'UNIQUE constraint' in str(e):
            return JSONResponse(
                content={"error": "A pair with this request already exists."},
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
    """Delete a saved request/response pair."""
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

    request_hash = hash_request(request_data)

    result = await db.execute(
        select(MirrorPair).where(MirrorPair.request_hash == request_hash)
    )
    pair = result.scalar_one_or_none()

    if not pair:
        return JSONResponse(
            content={"error": "No matching pair found to delete."},
            status_code=404
        )

    await db.delete(pair)
    await db.commit()
    return {"message": "Pair deleted successfully."}


@mirror_router.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def mirror_lookup(
    request: Request,
    db: DbSession
):
    """Look up and return a saved response for a matching request."""
    try:
        request_data = await request.json()
    except json.JSONDecodeError:
        body_bytes = await request.body()
        request_data = body_bytes.decode("utf-8") if body_bytes else ""

    request_hash = hash_request(request_data)

    result = await db.execute(
        select(MirrorPair).where(MirrorPair.request_hash == request_hash)
    )
    pair = result.scalar_one_or_none()

    if not pair:
        return JSONResponse(
            content={"error": "No mirrored response found for this request."},
            status_code=404
        )

    response_data = json.loads(pair.response_data)
    return JSONResponse(content=response_data, status_code=pair.response_status)
