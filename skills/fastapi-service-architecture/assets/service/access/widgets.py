"""Data access for one resource.

Subclass `Repository` when the resource needs filters the generic base cannot
know about - tenancy, ownership, status. Instantiate once at module level: the
repository is stateless with respect to requests, and the session is always
passed in.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.models import Widget
from common.pagination import PageParams, PageResult
from common.repository import JsonSearchField, Repository
from service.schemas import WidgetCreate, WidgetUpdate


class WidgetRepository(Repository[Widget, WidgetCreate, WidgetUpdate]):
    async def list_for_tenant(
        self, db: AsyncSession, tenant_id: str, params: PageParams
    ) -> PageResult[Widget]:
        """Tenant scoping lives here, not in the route.

        Putting it in the repository means a new endpoint cannot forget it, and a
        reviewer auditing tenant isolation has one file to read instead of every
        handler. If you also run Postgres RLS, this is defense in depth: the
        filter documents intent, the policy enforces it.
        """
        return await self.list(db, params, where=[Widget.tenant_id == tenant_id])

    async def get_for_tenant(
        self, db: AsyncSession, widget_id: str, tenant_id: str
    ) -> Widget | None:
        stmt = select(Widget).where(
            Widget.id == widget_id, Widget.tenant_id == tenant_id
        )
        # Add .options(selectinload(Widget.some_relationship)) here once the model
        # has relationships - under asyncio a lazy load during serialization
        # raises MissingGreenlet rather than quietly emitting a query.
        return await db.scalar(stmt)


widget_repository = WidgetRepository(
    Widget,
    searchable_columns=["name", "description"],
    json_search_fields=[JsonSearchField(column="config", key="label")],
    sortable_columns=["name", "created_at", "updated_at"],
    default_order_by="created_at",
    default_order_desc=True,
    # Name each relationship this repository should eagerly load, e.g.
    # load_options=[selectinload(Widget.tags)]. Never selectinload("*").
    load_options=[],
)
