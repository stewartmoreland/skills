"""Model for one resource.

Lives in common/database/models/ because the schema is one schema no matter how
many processes serve it. See models_example.py for relationships, association
tables, and eager-loading conventions.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base


class Widget(Base):
    __tablename__ = "widgets"
    __table_args__ = (
        # Tenant-scoped list queries filter on tenant_id and sort by created_at.
        # One composite index in that order serves both; two single-column indexes
        # serve neither well.
        Index("ix_widgets_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: str(uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(String(1000))
    config: Mapped[dict] = mapped_column(JSONB, default=dict)

    # server_default puts the clock in the database, so rows written by a
    # migration or a psql session get consistent timestamps.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
