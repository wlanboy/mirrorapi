from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Text, select
import json
import os

from schemas import MirrorSaveRequest, MessageResponse, ErrorResponse

DATABASE_DIR = os.environ.get("DATABASE_DIR", "/data")
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(DATABASE_DIR, 'mirror_data.db')}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class MirrorPair(Base):
    __tablename__ = 'mirror_pairs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_hash = Column(String, unique=True, nullable=False)
    request_data = Column(Text, nullable=False)
    response_data = Column(Text, nullable=False)
    response_status = Column(Integer, nullable=False)


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


def hash_request(request_data) -> str:
    """Generates a consistent hash from the request body."""
    if request_data is None:
        return "None"
    return json.dumps(request_data, sort_keys=True)


mirror_router = APIRouter(prefix="/mirror", tags=["mirror"])


@mirror_router.post("/save", status_code=201)
async def mirror_save(
    data: MirrorSaveRequest,
    db: AsyncSession = Depends(get_db)
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
    except Exception as e:
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
    db: AsyncSession = Depends(get_db)
):
    """Delete a saved request/response pair."""
    try:
        request_data = await request.json()
        if request_data is None:
            return JSONResponse(
                content={"error": "Request body cannot be empty."},
                status_code=400
            )
    except Exception:
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
    db: AsyncSession = Depends(get_db)
):
    """Look up and return a saved response for a matching request."""
    try:
        request_data = await request.json()
        if request_data is None:
            body_bytes = await request.body()
            request_data = body_bytes.decode("utf-8") if body_bytes else ""
    except Exception:
        body_bytes = await request.body()
        request_data = body_bytes.decode("utf-8") if body_bytes else ""

    if not request_data:
        request_data = ""

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
