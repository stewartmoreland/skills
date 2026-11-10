"""Pagination primitives shared by every list endpoint.

Two things live here:

* `PageParams` - the query-string contract. Declaring it as a Pydantic model and
  accepting it with `Annotated[PageParams, Query()]` (FastAPI >= 0.115) means the
  page/limit/search/order block is written once instead of copy-pasted into every
  route signature, and `extra="forbid"` turns a typo like `?limitt=5` into a 422
  instead of a silently ignored parameter.
* `Page[T]` - the response envelope. Derived values are `computed_field`
  properties rather than stored fields, so `pages`/`has_next` cannot drift out of
  sync with `total` the way they can when each repository recomputes them.

For cursor/keyset pagination on large or hot tables, see `CursorParams` /
`CursorPage` below and `references/pagination.md` for when to reach for them.
"""

from dataclasses import dataclass
from math import ceil
from typing import Generic, Sequence, TypeVar

from pydantic import BaseModel, ConfigDict, Field, computed_field

T = TypeVar("T")
ItemT = TypeVar("ItemT")

MAX_PAGE_SIZE = 200


class PageParams(BaseModel):
    """Offset pagination query parameters.

    Accept it in a route as:  params: Annotated[PageParams, Query()]
    """

    model_config = ConfigDict(extra="forbid")

    page: int = Field(1, ge=1, description="1-based page number.")
    limit: int = Field(50, ge=1, le=MAX_PAGE_SIZE, description="Items per page.")
    search: str | None = Field(None, max_length=200)
    order_by: str | None = Field(
        None,
        description="Column to sort by. Must be in the repository's sortable allowlist.",
    )
    order_desc: bool = False

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


@dataclass(slots=True)
class PageResult(Generic[ItemT]):
    """What a repository returns: ORM rows plus the total, nothing serialized yet.

    Keeping this a plain dataclass rather than a Pydantic model is deliberate.
    The repository deals in ORM objects; converting them to a response schema is
    the route's job, because only the route knows which schema the caller asked
    for (a list, a summary, an admin view).
    """

    items: Sequence[ItemT]
    total: int
    page: int
    limit: int


class Page(BaseModel, Generic[T]):
    """Response envelope. Build it in the route: Page[WidgetRead].of(result)."""

    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    limit: int = Field(ge=1)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pages(self) -> int:
        return ceil(self.total / self.limit) if self.limit else 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_previous(self) -> bool:
        return self.page > 1

    @classmethod
    def of(cls, result: PageResult) -> "Page[T]":
        """Validate a repository result into this concrete Page.

        Call on the parametrized class so the item type is known at runtime:

            return Page[WidgetRead].of(result)

        `from_attributes` lets Pydantic read the dataclass fields and convert
        each ORM row into the item schema in one pass.
        """
        return cls.model_validate(result)


# --- Cursor / keyset pagination -------------------------------------------------


class CursorParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cursor: str | None = Field(None, description="Opaque cursor from the previous page.")
    limit: int = Field(50, ge=1, le=MAX_PAGE_SIZE)


class CursorPage(BaseModel, Generic[T]):
    """Keyset page. No `total` and no page numbers - that is the trade.

    You get a query whose cost does not grow with how deep the caller has scrolled,
    at the price of not being able to render "page 47 of 200".
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    next_cursor: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_next(self) -> bool:
        return self.next_cursor is not None
