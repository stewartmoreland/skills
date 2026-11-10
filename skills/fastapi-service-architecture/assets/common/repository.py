"""Generic async repository (the data-access layer).

One subclass per aggregate root, instantiated once as a module-level singleton.
Routes never build SQL; they call repository methods. That boundary is what keeps
tenant filters, eager-loading choices, and sort allowlists in one auditable place
instead of scattered across forty handlers.

Transaction policy: these methods `flush()`, never `commit()`. The request-scoped
session dependency commits once, at the end, if the handler returned normally.
So a route that creates a row, uploads a file, and updates a counter either
commits all three or rolls back all three - which a repository that commits on
every call cannot give you.
"""

# Annotations are postponed, so `-> list[ModelT]` inside this class still means
# the builtin and not the `list()` method defined below it.
from __future__ import annotations

import logging
from typing import Any, Generic, Iterable, Sequence, TypeVar

from pydantic import BaseModel
from sqlalchemy import ColumnElement, Select, String, delete, func, inspect, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import strategy_options

from common.database import Base
from common.errors import NotFoundError, UnprocessableError
from common.pagination import PageParams, PageResult

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=Base)
CreateT = TypeVar("CreateT", bound=BaseModel)
UpdateT = TypeVar("UpdateT", bound=BaseModel)

LoadOption = strategy_options._AbstractLoad


class JsonSearchField(BaseModel):
    """Search inside a JSON/JSONB column at a fixed key, e.g. config -> 'title'."""

    column: str
    key: str


class Repository(Generic[ModelT, CreateT, UpdateT]):
    def __init__(
        self,
        model: type[ModelT],
        *,
        searchable_columns: Sequence[str] = (),
        json_search_fields: Sequence[JsonSearchField] = (),
        sortable_columns: Sequence[str] = (),
        default_order_by: str | None = None,
        default_order_desc: bool = True,
        load_options: Sequence[LoadOption] = (),
    ) -> None:
        """
        `sortable_columns` is an allowlist, and it is not optional hygiene.
        `order_by` arrives as an arbitrary caller-supplied string; resolving it
        with a bare `getattr(model, order_by)` lets a caller probe your schema
        and turn a typo into a 500. Anything outside the list is rejected as 422.

        `load_options` are the relationships this repository eagerly loads (e.g.
        `selectinload(Widget.tags)`). Name them explicitly: the wildcard
        `selectinload("*")` still works in 2.0, but it pulls every relationship on
        every query - including whichever one someone adds to the model next.

        Column names are checked against the mapper here, at import time, so a
        rename that breaks the search config fails on boot rather than on the
        first request that happens to pass `?search=`.
        """
        self.model = model
        self.searchable_columns = tuple(searchable_columns)
        self.json_search_fields = tuple(json_search_fields)
        self.sortable_columns = tuple(sortable_columns)
        self.default_order_by = default_order_by
        self.default_order_desc = default_order_desc
        self.load_options = tuple(load_options)

        mapped = set(inspect(model).columns.keys())
        configured = (
            set(self.searchable_columns)
            | set(self.sortable_columns)
            | {f.column for f in self.json_search_fields}
            | ({default_order_by} if default_order_by else set())
        )
        unknown = sorted(configured - mapped)
        if unknown:
            raise ValueError(
                f"{model.__name__} repository references unmapped columns: {unknown}"
            )

    # -- query building -----------------------------------------------------

    def _base_select(self, *where: ColumnElement[bool]) -> Select[tuple[ModelT]]:
        stmt = select(self.model)
        if where:
            stmt = stmt.where(*where)
        return stmt

    def _apply_search(
        self, stmt: Select[tuple[ModelT]], search: str
    ) -> Select[tuple[ModelT]]:
        term = f"%{search}%"
        clauses: list[ColumnElement[bool]] = [
            getattr(self.model, name).ilike(term) for name in self.searchable_columns
        ]
        clauses += [
            getattr(self.model, field.column)[field.key].astext.cast(String).ilike(term)
            for field in self.json_search_fields
        ]
        return stmt.where(or_(*clauses)) if clauses else stmt

    def _apply_order(
        self, stmt: Select[tuple[ModelT]], params: PageParams
    ) -> Select[tuple[ModelT]]:
        name = params.order_by or self.default_order_by
        if name is None:
            return stmt
        if name not in self.sortable_columns:
            raise UnprocessableError(
                f"Cannot sort by {name!r}.",
                context={"allowed": list(self.sortable_columns)},
            )
        desc = params.order_desc if params.order_by else self.default_order_desc
        column = getattr(self.model, name)
        stmt = stmt.order_by(column.desc() if desc else column.asc())
        # Ties on the sort column would otherwise let a row appear on two pages
        # (or on none) as the caller walks through them. Break ties on the PK.
        pk = inspect(self.model).primary_key[0]
        return stmt.order_by(pk.desc() if desc else pk.asc())

    async def _count(self, db: AsyncSession, stmt: Select[tuple[ModelT]]) -> int:
        # order_by(None) strips the ORDER BY: sorting rows you are only going to
        # count is wasted work, and some databases reject it inside a subquery.
        # Counting over a subquery stays correct even when a subclass hands us a
        # statement with joins or DISTINCT, which a bare count(*) would not.
        counted = select(func.count()).select_from(stmt.order_by(None).subquery())
        return await db.scalar(counted) or 0

    # -- reads --------------------------------------------------------------

    async def get(self, db: AsyncSession, obj_id: Any) -> ModelT | None:
        return await db.get(
            self.model, obj_id, options=list(self.load_options) or None
        )

    async def get_or_404(self, db: AsyncSession, obj_id: Any) -> ModelT:
        obj = await self.get(db, obj_id)
        if obj is None:
            raise NotFoundError(f"{self.model.__name__} {obj_id!r} not found.")
        return obj

    async def list(
        self,
        db: AsyncSession,
        params: PageParams,
        *,
        where: Iterable[ColumnElement[bool]] = (),
        load_options: Sequence[LoadOption] | None = None,
    ) -> PageResult[ModelT]:
        """Offset-paginate. Subclasses pass `where=` to add tenant/owner filters."""
        stmt = self._base_select(*where)
        if params.search:
            stmt = self._apply_search(stmt, params.search)

        # Count the filtered set *before* ordering and slicing.
        total = await self._count(db, stmt)

        stmt = self._apply_order(stmt, params)
        options = self.load_options if load_options is None else tuple(load_options)
        if options:
            stmt = stmt.options(*options)
        stmt = stmt.offset(params.offset).limit(params.limit)

        rows = await db.execute(stmt)
        return PageResult(
            items=rows.scalars().unique().all(),
            total=total,
            page=params.page,
            limit=params.limit,
        )

    # -- writes -------------------------------------------------------------

    async def create(self, db: AsyncSession, data: CreateT, **server_fields: Any) -> ModelT:
        """`server_fields` carries values the client must not supply - tenant_id,
        owner_id, created_by. Keeping them out of the Create schema and passing
        them here is what makes "client cannot write into another tenant" a
        property of the type, not of a code review."""
        # model_dump, not jsonable_encoder: the encoder turns datetimes and UUIDs
        # into strings on the way into a column that wanted the real type.
        obj = self.model(**data.model_dump(exclude_unset=True), **server_fields)
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def create_many(self, db: AsyncSession, data: Sequence[CreateT]) -> list[ModelT]:
        objs = [self.model(**item.model_dump(exclude_unset=True)) for item in data]
        db.add_all(objs)
        await db.flush()
        return objs

    async def update(
        self, db: AsyncSession, obj: ModelT, data: UpdateT | dict[str, Any]
    ) -> ModelT:
        # exclude_unset is what makes PATCH work: a field the caller omitted stays
        # untouched, while a field explicitly sent as null is set to null.
        changes = (
            data if isinstance(data, dict) else data.model_dump(exclude_unset=True)
        )
        for field, value in changes.items():
            setattr(obj, field, value)
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def delete(self, db: AsyncSession, obj_id: Any) -> None:
        obj = await self.get_or_404(db, obj_id)
        await db.delete(obj)
        await db.flush()

    async def delete_many(self, db: AsyncSession, ids: Sequence[Any]) -> int:
        if not ids:
            return 0
        pk = inspect(self.model).primary_key[0]
        result = await db.execute(delete(self.model).where(pk.in_(ids)))
        await db.flush()
        return result.rowcount or 0
