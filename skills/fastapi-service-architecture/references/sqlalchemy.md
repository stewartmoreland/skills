# SQLAlchemy 2.0 with async FastAPI

## Contents
- [Engine and session lifecycle](#engine-and-session-lifecycle)
- [The transaction boundary](#the-transaction-boundary)
- [Async pitfalls that only appear under load](#async-pitfalls-that-only-appear-under-load)
- [Eager loading](#eager-loading)
- [Model conventions](#model-conventions)
- [Alembic migrations](#alembic-migrations)
- [Bulk operations](#bulk-operations)

## Engine and session lifecycle

One engine per process, created at import, disposed in `lifespan`. The engine
owns a connection pool; a second engine means a second pool, and the fastest way
to exhaust Postgres `max_connections` is to create engines per request or per
router.

Sizing: `pool_size + max_overflow` per replica, times replicas, must stay under
the database's limit with headroom for migrations and psql sessions. Cloud SQL
and PgBouncer both have their own ceilings that are usually lower than you think.

`pool_pre_ping=True` costs one trivial round trip per checkout and saves you from
`OperationalError: server closed the connection unexpectedly` after an idle
period behind a proxy. Keep it on.

Sessions are per request, never shared. `AsyncSession` is not concurrency-safe:
two `asyncio.gather`-ed queries on one session raise
`InvalidRequestError: This session is provisioning a new connection` or interleave
into corruption. If you need parallel queries, open a session per task.

## The transaction boundary

Repositories `flush()`. The session dependency `commit()`s once, after the
handler returns.

```python
async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()
```

The reason is atomicity. When every repository method commits, a handler that
writes a row, calls an external API, and updates a counter has already committed
step one by the time step two fails. There is no rollback available — you are
writing compensation logic instead. With the boundary at the request, that
handler is one transaction and the failure undoes all of it.

`flush()` still gives you server-generated values (ids, defaults) inside the
transaction, so `create()` can return a fully populated object.

Two consequences worth knowing:

- **A long handler holds a transaction open.** Do not call a slow third-party API
  in the middle of one. Fetch first, then write; or commit deliberately and treat
  the remainder as a separate unit.
- **Background work must not use the request session.** It is closed when the
  response is sent. `BackgroundTasks` and fire-and-forget jobs open their own.

## Async pitfalls that only appear under load

**`MissingGreenlet`.** Raised when SQLAlchemy needs IO from a context that cannot
await — almost always a lazy load. `expire_on_commit=False` prevents the most
common form (attribute access after commit); `lazy="raise"` on relationships
turns the rest into a loud error at development time instead of a 500 in
production. The fix is never to "add greenlet" — it is to load the data you need
up front.

**`expire_on_commit=True`** (the SQLAlchemy default) is wrong for this pattern.
It marks every attribute stale on commit, so serializing the returned object
after the commit re-queries. In async that is a `MissingGreenlet`. Set it False.

**Ordering of commit and serialization.** FastAPI serializes the response before
`yield`-dependency teardown runs, so the object is still live when the response
model reads it. Do not rely on that if a handler returns something exotic —
convert to a schema inside the handler (`WidgetRead.model_validate(obj)`) and the
question stops mattering.

**`asyncio.gather` over one session.** See above: session per task.

## Eager loading

`selectinload("*")` still works in SQLAlchemy 2.0 (verified on 2.0.52: it
compiles and runs with no warning). It is the *named string* form that was
removed - `selectinload("kids")` now raises `ArgumentError: Strings are not
accepted for attribute names in loader options`.

So replacing the wildcard is a judgement call, not a forced migration. Make it
anyway: the wildcard loads every relationship on every query, including ones you
never serialize, and it grows silently as the model gains relationships. A model
that picks up an `audit_events` collection next quarter starts dragging it into
every list response, and nothing tells you.

Name them:

```python
widget_repository = WidgetRepository(
    Widget,
    load_options=[selectinload(Widget.tags), selectinload(Widget.owner)],
)
```

- `selectinload` — one extra query per relationship, using `IN (...)`. The default
  choice for collections.
- `joinedload` — one query with a LEFT JOIN. Good for many-to-one scalars; on
  collections it multiplies rows and needs `.unique()` on the result.
- `raiseload` / `lazy="raise"` — no loading, raises instead. Use it to make the
  N+1 impossible rather than merely unlikely.

The N+1 signature in an async service is not slowness, it is `MissingGreenlet`.
That is a feature: it fails immediately and points at the missing option.

## Model conventions

- Every model inherits the **same** `Base`. Two declarative bases means two
  `MetaData` objects and Alembic autogenerate that drops half your tables.
- `Mapped[...]` / `mapped_column(...)` — the 2.0 typed style. `Mapped[str | None]`
  is what makes a column nullable; do not also pass `nullable=True` and let them
  disagree.
- Timestamps via `server_default=func.now()`, not a Python `default=`. Rows
  written by a migration, a psql session, or a replica with a skewed clock should
  still get consistent times.
- `DateTime(timezone=True)` always. A naive timestamp column is a bug scheduled
  for the next daylight-saving transition.
- Cross-schema models use `__table_args__ = {"schema": "app"}`, and every
  `ForeignKey` to them must include the schema: `ForeignKey("app.tenants.id")`.
- Put the composite index that serves your list endpoint on the model:
  `Index("ix_widgets_tenant_created", "tenant_id", "created_at")`.
- `ondelete="CASCADE"` on the FK is the database-level rule;
  `cascade="all, delete-orphan"` on the relationship is the ORM-level one. They
  are different mechanisms — decide which owns deletion and be consistent, or a
  bulk `DELETE` will behave differently from an ORM delete.

## Alembic migrations

The async `env.py` bridges to Alembic's synchronous machinery with
`connection.run_sync(do_run_migrations)`. See `assets/common/alembic_env.py`.

- `include_schemas=True` is required if any model sets a non-public schema.
  Without it autogenerate cannot see those tables and proposes creating them on
  every run.
- `compare_type=True` and `compare_server_default=True` catch column changes
  autogenerate otherwise ignores.
- Import the models package in `env.py`. If `Base.metadata` is empty, autogenerate
  writes a migration that drops every table — and it will do so without
  complaining.
- **Read every generated migration.** Autogenerate cannot see renames; it emits
  drop-plus-add, which is data loss. It also misses CHECK constraints, RLS
  policies, and most index option changes.
- Run migrations as a deploy step, not from application startup. Startup
  migrations race when several replicas boot at once.

## Bulk operations

Row-by-row ORM writes are fine up to a few hundred rows. Beyond that:

- `db.add_all(objs)` + one `flush()` batches the INSERTs.
- `insert(Model).values([...])` with `on_conflict_do_update` (Postgres) for upserts.
- `update(Model).where(...).values(...)` and `delete(Model).where(...)` issue one
  statement, but they **bypass ORM events and do not update objects already in
  the session's identity map**. Use them for large deletes; be aware that
  in-session objects are then stale.
