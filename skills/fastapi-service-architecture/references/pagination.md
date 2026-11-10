# Pagination

## Contents
- [Offset pagination (the default)](#offset-pagination-the-default)
- [Making the count cheap](#making-the-count-cheap)
- [Stable ordering](#stable-ordering)
- [Search](#search)
- [Keyset / cursor pagination](#keyset--cursor-pagination)
- [Choosing between them](#choosing-between-them)
- [Response shape](#response-shape)

## Offset pagination (the default)

`?page=2&limit=50` maps to `OFFSET 50 LIMIT 50` plus a `COUNT(*)` over the same
filters. Use it by default. It is what page-number UIs, "showing 51-100 of 1,204"
labels, and most client SDKs already expect, and every alternative costs you one
of those.

The whole query-string contract is one Pydantic model:

```python
async def list_widgets(
    db: DbSession,
    params: Annotated[PageParams, Query()],
) -> Page[WidgetSummary]:
    return Page[WidgetSummary].of(await repo.list_for_tenant(db, tenant_id, params))
```

`Annotated[Model, Query()]` needs FastAPI >= 0.115. Before that you had to repeat
`page: int = Query(1, ge=1)` and friends in every signature, which is how the
limits drift apart between endpoints.

`PageParams` sets `extra="forbid"`, so `?limitt=5` is a 422 rather than a silently
ignored parameter that makes a caller think they got 5 rows back.

## Making the count cheap

The count is usually the expensive half of the request, because `LIMIT 50` stops
early while `COUNT(*)` reads the whole filtered set.

Things that matter, roughly in order:

1. **Strip the ORDER BY before counting.** `stmt.order_by(None)` — sorting rows
   you only intend to count is pure waste, and some databases reject `ORDER BY`
   inside an uncorrelated subquery. The template does this.
2. **Count before adding eager-load options and OFFSET/LIMIT.** Counting a
   statement that carries `selectinload` triggers the secondary loader queries
   for nothing.
3. **Index the filter and the sort together.** A tenant-scoped list sorted by
   `created_at` wants `INDEX (tenant_id, created_at)`. Two separate single-column
   indexes let the planner use one and sort the rest.
4. **Consider dropping `total`.** If the UI only renders next/prev, ask for
   `limit + 1` rows, return `limit` of them, and let the extra row tell you
   whether a next page exists. That removes the count query entirely.
5. **Approximate for very large tables.** For an unfiltered count over millions
   of rows, `SELECT reltuples::bigint FROM pg_class WHERE relname = 'widgets'` is
   instant and close enough for "about 4.2M". Never mix approximate totals with
   exact page arithmetic in the same response without saying so.

## Stable ordering

`ORDER BY created_at DESC LIMIT 50 OFFSET 50` with ties on `created_at` is
non-deterministic: the database may return tied rows in a different order per
query, so a row can appear on both page 1 and page 2, or on neither. Bulk imports
that stamp hundreds of rows with the same timestamp make this routine, not rare.

Always append a unique tiebreaker — the primary key. The template's `_apply_order`
does it automatically, in the same direction as the primary sort.

## Search

`ILIKE '%term%'` across a few columns is the right starting point: no extra
infrastructure, and it is what `searchable_columns` gives you. Know its limits.

- A **leading** wildcard cannot use a B-tree index, so it is a sequential scan.
  Fine at 10k rows, not at 10M.
- For JSON/JSONB columns, `json_search_fields` searches a fixed key:
  `config['label'].astext.cast(String).ilike(...)`. Searching arbitrary keys means
  scanning every document — index the specific paths you actually query.
- When ILIKE stops scaling, the next step is Postgres full-text search
  (`tsvector` column + GIN index) or trigram matching (`pg_trgm` + GIN), which
  *does* index leading wildcards. Reach for a separate search service only after
  those.

Sorting is an **allowlist**, not a `getattr`. `order_by` is caller-controlled:
resolving it directly against the model lets someone probe your column names,
turn a typo into a 500, and sort by an unindexed column that table-scans on every
call. The repository raises 422 with the allowed set instead.

## Keyset / cursor pagination

Instead of "skip 5,000 rows", keyset says "give me rows after this one":

```sql
WHERE (created_at, id) < (:last_created_at, :last_id)
ORDER BY created_at DESC, id DESC
LIMIT 50
```

The cost is constant no matter how deep the caller has scrolled, because the
index seeks straight to the position. `OFFSET 5000` makes the database read and
discard 5,000 rows first, so page 100 costs a hundred times page 1.

Keyset also has no drift: with offset pagination, rows inserted while a user
pages through shift everything down, so they see a row twice and miss another.

The cursor must encode every column in the ORDER BY. Encode it opaquely
(base64 of a small JSON payload) so callers cannot construct one by hand and
you can change the encoding later. It is not a security boundary — always
re-apply tenant filters on the decoded values.

```python
class CursorPage(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None
```

## Choosing between them

| Signal | Use |
|---|---|
| UI shows page numbers or a total | Offset |
| Table under ~100k rows | Offset |
| Infinite scroll / "load more" | Keyset |
| Deep pages are actually requested (logs, feeds, events) | Keyset |
| Rows are inserted constantly at the top | Keyset |
| Export / cursor over the whole table | Keyset |

Both can coexist: offer offset on the resource's main list endpoint and keyset on
the high-volume child collection. Do not migrate a working offset endpoint to
keyset without a measurement showing deep pages are the problem.

## Response shape

`pages`, `has_next`, and `has_previous` are `computed_field` properties on
`Page[T]`, not stored fields. Derived values that each repository recomputes are
values that eventually disagree with `total` — computing them in one place makes
that impossible. They still appear in the serialized body and in the OpenAPI
schema exactly as if they were fields.

`Page.of()` is the conversion point: the repository returns ORM rows in a
`PageResult` dataclass, and the route names the schema it wants
(`Page[WidgetSummary].of(result)`). That is why list endpoints can return a
slimmer projection than detail endpoints without a second repository method.
