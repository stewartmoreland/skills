"""Pydantic schemas for one resource.

Four-class shape, and each class earns its place:

* `WidgetBase`   - fields shared by input and output.
* `WidgetCreate` - what a client may set on POST.
* `WidgetUpdate` - every field optional, so PATCH means "change only these".
* `WidgetRead`   - what goes on the wire, including server-owned fields.

Never annotate a route with the ORM model. A separate Read schema is what stops
a `password_hash` or `internal_notes` column from being published the moment
someone adds it to the table.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WidgetBase(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str | None = Field(None, max_length=1000)
    config: dict = Field(default_factory=dict)


class WidgetCreate(WidgetBase):
    # tenant_id is intentionally absent: it comes from the caller's token, not
    # from the request body. Accepting it here would let anyone write into any
    # tenant by editing the payload.
    pass


class WidgetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, min_length=1, max_length=64)
    description: str | None = Field(None, max_length=1000)
    config: dict | None = None


class WidgetRead(WidgetBase):
    # from_attributes replaces Pydantic v1's `orm_mode`. It is what lets
    # WidgetRead be built straight from a SQLAlchemy row.
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime | None = None


class WidgetSummary(BaseModel):
    """Slim projection for list endpoints.

    List responses multiply everything by `limit`. Returning a narrower schema
    from the list route than from the detail route is usually the cheapest
    performance win available.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    created_at: datetime
