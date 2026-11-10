"""Engine, session factory, and declarative base.

One engine per process. The engine owns a connection pool; creating a second one
per request silently doubles your database connection count and is the most
common way an async FastAPI service exhausts Postgres `max_connections`.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from common.settings import get_settings


class Base(DeclarativeBase):
    """Declarative base for every model in the service.

    Every model must import *this* Base. Two Bases means two MetaData objects,
    which means Alembic autogenerate silently drops half your tables.
    """


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"{type(obj)!r} is not JSON serializable")


def _dumps(value: Any) -> str:
    return json.dumps(value, default=_json_default)


def create_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        str(settings.database_url),
        echo=settings.db_echo,
        json_serializer=_dumps,
        # Recycles connections a proxy or Cloud SQL may have already dropped;
        # without it the first query after an idle period raises OperationalError.
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle_seconds,
    )


engine: AsyncEngine = create_engine()

SessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    # Critical under asyncio: with expire_on_commit=True (the default), touching
    # any attribute after commit triggers a lazy refresh. In async that raises
    # MissingGreenlet instead of quietly emitting SQL. Keep this False and
    # return objects that are still readable after the request commits.
    expire_on_commit=False,
)
