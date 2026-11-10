"""HTTP layer for one resource.

Handlers stay thin on purpose: authorize, delegate, shape the response. No SQL,
no commits, no business rules. When a handler starts growing branches, that logic
belongs in `modules/` (domain services) or in the repository - the route is not
where it becomes hard to test.
"""

from typing import Annotated

from fastapi import APIRouter, Query, status

from common.deps import CurrentUser, DbSession
from common.errors import NotFoundError
from common.pagination import Page, PageParams
from service.access import widget_repository
from service.schemas import WidgetCreate, WidgetRead, WidgetSummary, WidgetUpdate

# Version lives in the prefix so v2 can be mounted alongside v1 later. Tags group
# the resource in the OpenAPI docs.
router = APIRouter(prefix="/api/v1/widgets", tags=["Widgets"])


@router.get("")
async def list_widgets(
    db: DbSession,
    user: CurrentUser,
    # One Pydantic model instead of five separate Query(...) parameters. Since
    # FastAPI 0.115 this documents and validates identically, and `extra="forbid"`
    # on PageParams rejects misspelled query keys instead of ignoring them.
    params: Annotated[PageParams, Query()],
) -> Page[WidgetSummary]:
    result = await widget_repository.list_for_tenant(db, user.tenant_id, params)
    return Page[WidgetSummary].of(result)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_widget(
    db: DbSession,
    user: CurrentUser,
    payload: WidgetCreate,
) -> WidgetRead:
    # tenant_id is injected from the token, never read from the payload.
    widget = await widget_repository.create(db, payload, tenant_id=user.tenant_id)
    return WidgetRead.model_validate(widget)


@router.get("/{widget_id}")
async def get_widget(
    db: DbSession,
    user: CurrentUser,
    widget_id: str,
) -> WidgetRead:
    widget = await widget_repository.get_for_tenant(db, widget_id, user.tenant_id)
    if widget is None:
        # Same 404 whether the row is missing or belongs to another tenant.
        # A 403 here would confirm the id exists, which is an enumeration oracle.
        raise NotFoundError(f"Widget {widget_id!r} not found.")
    return WidgetRead.model_validate(widget)


@router.patch("/{widget_id}")
async def update_widget(
    db: DbSession,
    user: CurrentUser,
    widget_id: str,
    payload: WidgetUpdate,
) -> WidgetRead:
    widget = await widget_repository.get_for_tenant(db, widget_id, user.tenant_id)
    if widget is None:
        raise NotFoundError(f"Widget {widget_id!r} not found.")
    updated = await widget_repository.update(db, widget, payload)
    return WidgetRead.model_validate(updated)


@router.delete("/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    db: DbSession,
    user: CurrentUser,
    widget_id: str,
) -> None:
    widget = await widget_repository.get_for_tenant(db, widget_id, user.tenant_id)
    if widget is None:
        raise NotFoundError(f"Widget {widget_id!r} not found.")
    await widget_repository.delete(db, widget.id)
