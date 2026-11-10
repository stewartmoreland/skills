# Multi-tenancy (optional)

Skip this file entirely if the service is single-tenant. If it is not, pick one
of the two enforcement points below and apply it consistently — the failure mode
of "mostly filtered" is one endpoint that returns another customer's rows.

## Contents
- [Layer 1: repository filters](#layer-1-repository-filters)
- [Layer 2: Postgres row-level security](#layer-2-postgres-row-level-security)
- [The connection-pool leak](#the-connection-pool-leak)
- [Tenant id comes from the token](#tenant-id-comes-from-the-token)
- [404 versus 403](#404-versus-403)

## Layer 1: repository filters

The default, and enough for most services. Every query that touches a
tenant-scoped table filters on `tenant_id`, and the filter lives in the
repository so a new endpoint cannot forget it:

```python
class WidgetRepository(Repository[Widget, WidgetCreate, WidgetUpdate]):
    async def list_for_tenant(self, db, tenant_id: str, params: PageParams):
        return await self.list(db, params, where=[Widget.tenant_id == tenant_id])
```

The property you want is that a route cannot express an unscoped query without
obviously doing so. Routes calling `repo.list(db, params)` directly on a
tenant-scoped model should stand out in review. If that discipline is hard to
hold, move to RLS.

## Layer 2: Postgres row-level security

RLS moves enforcement into the database, so a missing filter returns zero rows
instead of everyone's rows. Application bugs stop being data breaches.

```sql
CREATE ROLE tenant_user NOLOGIN;
GRANT USAGE ON SCHEMA app TO tenant_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO tenant_user;

ALTER TABLE app.widgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.widgets FORCE ROW LEVEL SECURITY;   -- also applies to the owner

CREATE POLICY tenant_isolation ON app.widgets
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
```

`USING` governs which rows are visible; `WITH CHECK` governs which rows may be
written. Omitting `WITH CHECK` lets a tenant insert a row attributed to someone
else and then lose sight of it. `FORCE ROW LEVEL SECURITY` matters because
policies are bypassed for the table owner by default — and your migration user is
usually the owner.

The application sets the variables per request; see `assets/common/deps.py`.

Keep both layers. RLS is the guarantee, the repository filter is documentation
plus a correct query plan — the planner uses your explicit `WHERE` better than a
policy predicate alone.

## The connection-pool leak

This is the detail that turns RLS from a control into a liability if you get it
wrong.

```python
# WRONG - these persist on the pooled connection after the request ends
await db.execute(text("SET SESSION ROLE tenant_user"))
await db.execute(text(f"SET jwt.claims.user_id='{user_id}'"))
```

Two independent bugs:

1. **`SET SESSION` outlives the request.** The session closes and returns the
   connection to the pool with the role and claims still set. The next request to
   borrow that connection inherits them. A code path that skips the setup — an
   admin session, a health check, a background job — silently runs as the
   previous tenant. Nothing errors; the rows are simply wrong.
2. **The f-string is injectable.** `user_id` comes from a JWT claim. An attacker
   who controls that claim controls the SQL statement.

```python
# RIGHT - transaction-scoped, parameterized
async with SessionFactory() as session:
    async with session.begin():
        await session.execute(text("SET LOCAL ROLE tenant_user"))
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tid, true)"),
            {"tid": principal.tenant_id},
        )
        yield session
```

`SET LOCAL` and `set_config(..., is_local => true)` both reset when the
transaction ends, so nothing survives into the next borrower of that connection.
They need an explicit transaction — outside one, `SET LOCAL` warns and does
nothing, which looks like it worked.

**This depends on the commit boundary being the request.** If repository methods
still commit individually, the first commit ends the transaction and takes the
LOCAL settings with it. Every query after that runs with no tenant context, so
the RLS policy matches nothing and returns **zero rows** - a silent empty list,
not an error, which is the hardest version of this bug to notice. The two changes
are really one change: move the commit to the session dependency at the same
time. If you cannot, re-apply the context per transaction with a SQLAlchemy
`after_begin` event listener instead.

**Verify it rather than assuming.** A test that opens two sessions in sequence
for different tenants and asserts the second cannot see the first's rows is worth
more than any amount of code review here.

**Transaction-pooling proxies.** Under PgBouncer in transaction mode, a
connection is reassigned between transactions. Transaction-scoped settings are
correct there; session-scoped ones are actively broken.

## Tenant id comes from the token

Never accept `tenant_id` in a request body or query string. It belongs in
`Principal`, derived from a verified token, and is passed to the repository as a
server-owned field:

```python
widget = await repo.create(db, payload, tenant_id=user.tenant_id)
```

Leaving `tenant_id` off the Create schema makes "a client cannot write into
another tenant" a property of the type rather than of a code review. The same
applies to `owner_id`, `created_by`, and anything else that names who did it.

## 404 versus 403

When a row exists but belongs to another tenant, return **404**, not 403. A 403
confirms the id is real, which turns the endpoint into an existence oracle
someone can enumerate. Handlers should look up the row *with* the tenant filter
applied and treat "not found" and "not yours" identically.
