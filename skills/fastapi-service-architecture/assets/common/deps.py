"""Request-scoped dependencies, exported as Annotated aliases.

Aliases (`DbSession`, `CurrentUser`) exist so route signatures read as types
rather than as a wall of `= Depends(...)` defaults. They also mean the day you
change how sessions are built, you change it here and nowhere else.
"""

from typing import Annotated, AsyncIterator

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import SessionFactory
from common.security import Principal, get_principal


async def get_session() -> AsyncIterator[AsyncSession]:
    """One session and one transaction per request.

    The handler runs inside the transaction; returning normally commits, and any
    exception - including one raised by an exception handler's own dependency -
    rolls back. Repositories therefore only `flush()`, and a multi-step handler
    is atomic without anyone writing explicit transaction code.
    """
    async with SessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


DbSession = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[Principal, Depends(get_principal)]


async def get_tenant_session(
    principal: CurrentUser,
) -> AsyncIterator[AsyncSession]:
    """Session whose connection is scoped to the caller for Postgres RLS.

    Two details carry the security weight:

    1. `set_config(..., is_local => true)` and `SET LOCAL ROLE` reset when the
       transaction ends. Plain `SET SESSION ROLE` / `SET x = y` persist on the
       pooled connection after the request closes it, so the next request to
       borrow that connection inherits the previous caller's role and claims.
       That is a cross-tenant read waiting to happen.
    2. The user id is passed as a bound parameter. Interpolating it into the SQL
       string means an attacker who controls a JWT claim controls your SQL.

    Requires an explicit transaction so LOCAL has something to be local to.
    """
    async with SessionFactory() as session:
        async with session.begin():
            await session.execute(text("SET LOCAL ROLE tenant_user"))
            await session.execute(
                text("SELECT set_config('app.user_id', :user_id, true)"),
                {"user_id": principal.user_id},
            )
            if principal.tenant_id:
                await session.execute(
                    text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                    {"tenant_id": principal.tenant_id},
                )
            yield session
        # session.begin() commits on clean exit and rolls back on exception.


TenantDbSession = Annotated[AsyncSession, Depends(get_tenant_session)]
