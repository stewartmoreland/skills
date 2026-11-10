# Testing this architecture

## Contents
- [Client setup](#client-setup)
- [Overriding dependencies](#overriding-dependencies)
- [Use real Postgres](#use-real-postgres)
- [What is worth testing](#what-is-worth-testing)

## Client setup

`httpx.ASGITransport` calls the app in-process — no server, no port, and real
async so `AsyncSession` behaves as it does in production. Enter the app as a
context manager so `lifespan` runs.

```python
import pytest
from httpx import ASGITransport, AsyncClient

@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
```

`TestClient` (sync) still works and is fine for simple cases, but it runs the app
in a worker thread, which hides some async ordering bugs.

## Overriding dependencies

`app.dependency_overrides` is the seam. It works regardless of module-level
globals, which is what makes the module-level engine acceptable:

```python
app.dependency_overrides[get_session] = override_session
app.dependency_overrides[get_principal] = lambda: Principal(
    user_id="u1", tenant_id="t1"
)
```

Override `get_principal` rather than minting real tokens — you are testing your
handlers, not your identity provider. Keep at least one test that exercises the
real dependency against a known-bad token, so an auth misconfiguration is not
invisible.

Clear overrides between tests (`app.dependency_overrides.clear()`) or they leak
across the session.

## Use real Postgres

SQLite is tempting and wrong for anything schema-shaped. It has no JSONB, no
`ILIKE` semantics you can trust, no RLS, no schemas, no `ON CONFLICT DO UPDATE`
with the same syntax, and different transaction behaviour. Tests pass; production
does not.

Run Postgres in CI — `testcontainers`, a docker-compose service, or a GitHub
Actions service container — and create the schema from your Alembic migrations,
not from `metadata.create_all()`. Running migrations in tests is also the only
cheap way to find out that a migration is broken before it runs against
production.

Fast isolation: wrap each test in a transaction and roll back at the end, rather
than truncating tables between tests.

The one exception is `scripts/verify_scaffold.py`, which uses in-memory SQLite
deliberately — it checks framework wiring (pagination arithmetic, validation,
error envelope), not your schema.

## Do not assert on `app.routes`

As of FastAPI 0.141, `include_router` stores an internal `_IncludedRouter` entry
rather than eagerly flattening the router's routes into `app.routes`. Iterating
`app.routes` after mounting shows the app's own routes plus opaque wrappers, so a
test like `assert "/api/v1/orders" in {r.path for r in app.routes}` now fails
against a perfectly working app.

Assert on behaviour or on the schema instead - both reflect the real routing table:

```python
assert "/api/v1/orders" in app.openapi()["paths"]
assert (await client.get("/api/v1/orders")).status_code == 401   # mounted, auth applied
```

Routes marked `include_in_schema=False` (such as `/health`) never appear in the
OpenAPI paths, so check those with a request.

## What is worth testing

Concentrate on the things this architecture makes easy to get subtly wrong:

- **Pagination arithmetic** at the boundaries: last page, empty result set,
  `limit` above the max, `page` beyond the end.
- **Sort allowlist**: a column not on the list returns 422, not 500.
- **`extra="forbid"`**: a misspelled query parameter is rejected.
- **PATCH semantics**: an omitted field is unchanged; a field explicitly sent as
  `null` becomes null. This is what `exclude_unset` buys and it is easy to
  regress.
- **Tenant isolation**: tenant A cannot read, update, or delete tenant B's row,
  and gets 404 rather than 403. If you use RLS, also test that two sequential
  sessions on the same pooled connection do not leak.
- **Transaction rollback**: a handler that writes twice and then raises leaves
  the database unchanged. This verifies the commit boundary actually holds.
- **Response schema**: the Read schema does not expose columns you did not
  intend. A snapshot of the OpenAPI schema in CI catches accidental additions.
