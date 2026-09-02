"""Database engine, session and ORM model for saved mirror pairs."""

import os
from datetime import datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Text, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DATABASE_DIR = os.environ.get("DATABASE_DIR", "/data")
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(DATABASE_DIR, 'mirror_data.db')}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

WILDCARD = "*"


class Base(DeclarativeBase):
    pass


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
