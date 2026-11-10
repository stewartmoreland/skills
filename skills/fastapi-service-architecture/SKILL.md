---
name: fastapi-service-architecture
description: Layered async FastAPI architecture for database-backed REST services - repo layout (single service vs uv workspace monorepo), app factory, generic SQLAlchemy 2.0 repository, offset and cursor pagination, request-scoped sessions and transactions, router-level auth, optional Postgres RLS multi-tenancy, on FastAPI 0.141+ / Pydantic v2 / SQLAlchemy 2.0. Use whenever the work involves building a FastAPI service or adding endpoints to one; writing CRUD or list endpoints; paginating, sorting, or searching database results; wiring async SQLAlchemy sessions into FastAPI; structuring a Python API repo, monorepo, or uv workspace, or splitting one into services; or modernizing an older FastAPI/Pydantic v1 codebase. Reach for it even when the request sounds small - "add a list endpoint", "why is this query slow", "make this multi-tenant" - because the failure modes here (MissingGreenlet, non-atomic writes, unstable page ordering, cross-tenant leaks) come from architecture, not the endpoint.
---

# FastAPI service architecture

A layered structure for async, database-backed FastAPI services. It is designed
so one source tree can ship as a single API today and as several independently
deployed services later without the routes changing.

Everything here is verified against **FastAPI 0.141**, **Pydantic 2.13**,
**SQLAlchemy 2.0.52**, **Python 3.10+**.

## First: pick the layout

The layering is the same everywhere; how many packages it spans is not. Decide
from one question — **how many processes ship from this repo?**

**One deployable.** Shared infrastructure in `src/common/`, resources beside it:

```
repo/
├── pyproject.toml          [tool.uv] package = false
└── src/
    ├── common/             app.py settings.py database/ deps.py repository.py
    │                       pagination.py errors.py security.py
    ├── routes/orders.py    HTTP only
    ├── access/orders.py    SQL only
    ├── schemas/orders.py   Pydantic
    ├── modules/            domain logic, external clients
    └── main.py             builds the app, mounts routers
```

**More than one deployable.** A uv workspace: one lockfile, one virtualenv, a
shared library, and a package per service:

```
repo/
├── pyproject.toml                  [tool.uv.workspace] members = ["packages/*", "services/*"]
├── uv.lock
├── packages/common/src/common/     the shared library
└── services/
    ├── billing/src/billing/        routes/ access/ schemas/ modules/ main.py
    └── catalog/src/catalog/
```

Do **not** add the per-service level speculatively. In a single-service repo it
produces `src/orders/routes/orders.py` — the name twice, carrying no information.
Promotion later is a directory move, and since `common` keeps its import path in
both layouts, no shared-layer import changes. `references/repo-layout.md` has the
uv mechanics, the constraints, and the exact migration steps.

**The rule that makes either work:** a request flows `route → access → database`
and never skips or reverses. Routes contain no SQL. Repositories contain no HTTP.
Schemas cross both. When that holds, tenant filters, eager-loading decisions, and
sort allowlists each live in exactly one auditable place — the whole return on
the indirection.

**`main.py` is the only file that decides which routers a process serves.** That
is what makes splitting later cheap: a `main.py` mounting everything is a
monolith, three mounting subsets are three services, and no route, repository, or
schema moves.

## Getting started

```bash
# one deployable
python <skill>/scripts/scaffold.py --layout single --app myapi --resource order
uv sync && uv run uvicorn main:app --app-dir src --reload

# several deployables (run again per service; leaves packages/common alone)
python <skill>/scripts/scaffold.py --layout workspace --service billing --resource invoice
uv sync --package billing
uv run --package billing uvicorn billing.main:app --reload
```

Both emit a working app: `/health` responds, the resource's CRUD + list routes are
mounted behind auth, and the model exists. Everything it writes is meant to be
edited — it removes the typing, not the thinking.

**Check the wiring before building on it:**

```bash
python <skill>/scripts/verify_scaffold.py
```

27 checks against in-memory SQLite: page arithmetic, sort allowlist, query-param
validation, PATCH semantics, error envelope, OpenAPI output. Run it after
scaffolding and after changing anything in `common/`.

**Existing repo:** do not scaffold over it. Read the templates in `assets/`, adopt
what fits, and match the surrounding conventions — one consistent pattern beats
two good ones.

## The core moves

Read the code in `assets/` for the full versions; these are the shapes.

**A list endpoint** — one Pydantic model carries the whole query-string contract
(FastAPI 0.115+), and the route names the response schema it wants:

```python
@router.get("")
async def list_widgets(
    db: DbSession,
    user: CurrentUser,
    params: Annotated[PageParams, Query()],
) -> Page[WidgetSummary]:
    return Page[WidgetSummary].of(await widget_repo.list_for_tenant(db, user.tenant_id, params))
```

**A repository** — filters the generic base cannot know about live here, so a new
endpoint cannot forget them:

```python
class WidgetRepository(Repository[Widget, WidgetCreate, WidgetUpdate]):
    async def list_for_tenant(self, db, tenant_id, params) -> PageResult[Widget]:
        return await self.list(db, params, where=[Widget.tenant_id == tenant_id])

widget_repo = WidgetRepository(
    Widget,
    searchable_columns=["name", "description"],
    sortable_columns=["name", "created_at"],   # allowlist, not getattr
    default_order_by="created_at",
    load_options=[selectinload(Widget.tags)],  # never selectinload("*")
)
```

**Auth at mount time**, not per handler — one line covers every current and future
route on the router, so a new endpoint is authenticated by default:

```python
app.include_router(widgets_router, dependencies=[Depends(get_principal)])
```

## Decisions that carry weight

These are the ones that are expensive to reverse, and each is a place where the
obvious approach is wrong in a way that surfaces late.

**The transaction boundary is the request, not the repository method.**
Repositories `flush()`; the session dependency commits once, after the handler
returns. When every repository method commits instead, a handler that writes a
row, calls an external API, and updates a counter has already committed step one
when step two fails — and you are writing compensation logic rather than relying
on a rollback.

**`expire_on_commit=False` on the session factory.** The SQLAlchemy default marks
attributes stale at commit, so reading them afterward re-queries. Under asyncio
that is `MissingGreenlet`, not a stray query.

**Eager-load explicitly.** `selectinload("*")` still works, but it loads every
relationship on every query - including the one somebody adds next quarter. Name them in `load_options`; set `lazy="raise"` on
relationships so a missing one fails loudly in development instead of at 3am.

**Sorting is an allowlist.** `order_by` is a caller-supplied string.
`getattr(Model, order_by)` lets someone probe your schema, turn a typo into a
500, and sort by an unindexed column on every call.

**Never annotate a route with an ORM model.** A separate Read schema is what
stops a `password_hash` column from being published the moment someone adds it to
the table. List endpoints should return a narrower schema than detail endpoints —
list responses multiply everything by `limit`.

**Server-owned fields never appear in a Create schema.** `tenant_id`, `owner_id`,
and `created_by` come from the verified token and are passed as
`repo.create(db, payload, tenant_id=user.tenant_id)`. That makes "a client cannot
write into another tenant" a property of the type rather than of a code review.

**Order by a unique tiebreaker.** `ORDER BY created_at DESC` with ties is
non-deterministic across queries, so a row can appear on two pages or none. The
repository appends the primary key automatically.

**Return 404, not 403, for another tenant's row.** A 403 confirms the id exists,
which is an enumeration oracle.

## Where to read next

Load the file that matches the task; do not read them all.

| File | When |
|---|---|
| `references/repo-layout.md` | Single service vs uv workspace, uv mechanics, naming, promoting one into the other |
| `references/pagination.md` | List endpoints, slow counts, deep pages, search, choosing offset vs cursor |
| `references/sqlalchemy.md` | Sessions, transactions, `MissingGreenlet`, N+1, models, Alembic, bulk writes |
| `references/multitenancy.md` | Tenant scoping, Postgres RLS, the connection-pool leak |
| `references/modernizing.md` | Upgrading an older service - Pydantic v1→v2, FastAPI/SQLAlchemy deltas, patterns to retire |
| `references/testing.md` | Test client setup, dependency overrides, what to actually assert |

Templates in `assets/common/` and `assets/service/` are runnable and commented
with the reasoning; read them rather than reconstructing the patterns from memory.

## If the codebase is older than FastAPI 0.100

Go to `references/modernizing.md` first. Migration order matters — Pydantic v2
before the FastAPI bump — and one change breaks silently rather than loudly:
Pydantic v2 makes `Optional[int]` with no default a **required** field, so
v1-era response models start raising `ValidationError` on construction. Audit
every `Optional[...]` that lacks `= None` before anything else.
