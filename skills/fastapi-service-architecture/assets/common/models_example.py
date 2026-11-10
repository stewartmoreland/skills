"""Model conventions (SQLAlchemy 2.0 declarative).

Models live in `common/database/models/` and are shared by every service in the
repo, because the schema is one schema no matter how many processes serve it.
Each module re-exports through `models/__init__.py` so Alembic sees the full
MetaData in one import.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Table, Column, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.database import Base

if TYPE_CHECKING:  # avoids a circular import while keeping the annotation real
    from common.database.models.tags import Tag


class TimestampMixin:
    """`server_default=func.now()` puts the clock in the database.

    A Python-side `default=` means rows written by a migration, a psql session,
    or a second service with a skewed clock get inconsistent timestamps.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


widget_tag_table = Table(
    "widget_tag",
    Base.metadata,
    Column("widget_id", String(64), ForeignKey("widgets.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(64), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Widget(TimestampMixin, Base):
    __tablename__ = "widgets"
    __table_args__ = (
        # Every tenant-scoped list query filters on tenant_id and sorts by
        # created_at. A composite index in that order serves both the filter and
        # the sort; two single-column indexes serve neither well.
        Index("ix_widgets_tenant_created", "tenant_id", "created_at"),
        {"schema": "app"},
    )

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: str(uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("app.tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(String(1000))
    config: Mapped[dict] = mapped_column(JSONB, default=dict)

    tags: Mapped[list["Tag"]] = relationship(
        secondary=widget_tag_table,
        back_populates="widgets",
        # Under asyncio a lazy load during response serialization raises
        # MissingGreenlet, not a stray query. "raise" surfaces the missing
        # eager-load at development time; the repository's load_options supply it.
        lazy="raise",
    )
