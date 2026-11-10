# Modernizing a 2022-era FastAPI service

Baseline for this table: **FastAPI 0.141**, **Pydantic 2.13**, **SQLAlchemy 2.0.52**,
**Python 3.10+** (FastAPI 0.141 requires >= 3.10). A service pinned around
FastAPI 0.9x / Pydantic v1 needs the changes below. Ordering matters: Pydantic v2
first, because everything else assumes it.

## Contents
- [Order of operations](#order-of-operations)
- [Pydantic v1 to v2](#pydantic-v1-to-v2)
- [FastAPI API changes](#fastapi-api-changes)
- [SQLAlchemy 1.4 to 2.0](#sqlalchemy-14-to-20)
- [Patterns worth replacing while you are in there](#patterns-worth-replacing-while-you-are-in-there)
- [Newer capabilities you can now use](#newer-capabilities-you-can-now-use)

## Order of operations

1. Get onto Python 3.10+ and confirm the test suite passes unchanged.
2. Migrate Pydantic v1 → v2 (`bump-pydantic` handles most of the mechanical part).
   FastAPI emits a deprecation warning if you use `pydantic.v1` shims, so treat
   the shim as a staging area, not a destination.
3. Bump FastAPI. Most v1-era route code keeps working; the deprecations below are
   the ones that bite.
4. Migrate SQLAlchemy to 2.0 style.
5. Only then adopt the newer capabilities in the last section.

## Pydantic v1 to v2

| v1 | v2 |
|---|---|
| `class Config: orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` |
| `class Config: allow_population_by_field_name` | `model_config = ConfigDict(populate_by_name=True)` |
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `.parse_obj()` / `.from_orm()` | `.model_validate()` |
| `@validator` | `@field_validator` (add `@classmethod`) |
| `@root_validator` | `@model_validator(mode="before" \| "after")` |
| `Optional[int]` with no default | **now required** — write `int \| None = None` |
| `BaseSettings` from `pydantic` | `BaseSettings` from `pydantic-settings` (separate package) |
| `Field(..., regex=)` | `Field(..., pattern=)` |
| `parse_obj_as(T, v)` | `TypeAdapter(T).validate_python(v)` |

**The `Optional` change is the one that breaks silently.** In v1,
`total: Optional[int]` meant "optional, defaults to None". In v2 it means "may be
None, and you must supply it". A response model like

```python
class PaginatedResponse(BaseModel, Generic[T]):
    total: Optional[int]     # v1: optional. v2: REQUIRED.
    page: Optional[int]
```

starts raising `ValidationError` on every construction that omits a field. Audit
every `Optional[...]` that has no `= None`. Verified on Pydantic 2.13.4:
omitting them raises `ValidationError: 2 validation errors`.

**A generic response model parameterized by a TypeVar bound to your ORM Base
will not import at all.** This is the v1-era pagination envelope:

```python
ModelVar = TypeVar("ModelVar", bound=Base)      # Base = DeclarativeBase

class PaginatedResponse(BaseModel, Generic[ModelVar]):
    items: List[ModelVar]
```

Under v1 the TypeVar degraded to `Any` and this worked. Under v2, Pydantic
resolves the TypeVar to its bound while building the schema at **class definition
time**, cannot generate a schema for a SQLAlchemy class, and raises
`PydanticSchemaGenerationError: Unable to generate pydantic-core schema for
<class Base>`. Verified on Pydantic 2.13.4.

The failure is at import, so it takes down every module that imports the
repository base - which is usually all of them. It is loud, but it arrives the
moment you unpin, and `arbitrary_types_allowed=True` only silences it rather than
making the envelope work.

The fix is to stop parameterizing the envelope with ORM types. Have the data
layer return rows plus a total, and let the route name the response schema
(`Page[WidgetRead].of(result)`). See `assets/common/pagination.py`.

**Generic models**: `GenericModel` is gone. Inherit `BaseModel` and `Generic[T]`
directly.

**Serialization is stricter.** v2 warns (and can error) when a field's runtime
value does not match its declared type. Passing ORM objects into a field typed as
a TypeVar used to work loosely in v1 and now needs a real schema with
`from_attributes=True`. This is why the template converts ORM → schema explicitly
at the route boundary rather than parameterizing the response envelope with the
ORM class.

## FastAPI API changes

| Old | Current |
|---|---|
| `@app.on_event("startup"/"shutdown")` | `lifespan=` async context manager |
| `response_model=X` on the decorator | return annotation `-> X` (both still work) |
| `param: X = Depends(dep)` | `param: Annotated[X, Depends(dep)]` |
| `q: str = Query(None)` | `q: Annotated[str \| None, Query()] = None` |
| repeated `page`/`limit`/`search` params | one Pydantic model via `Annotated[Params, Query()]` (>= 0.115) |
| `status.HTTP_422_UNPROCESSABLE_ENTITY` | renamed to `..._UNPROCESSABLE_CONTENT`; old name deprecated in Starlette |
| `from fastapi.encoders import jsonable_encoder` into a model constructor | `.model_dump()` |

`on_event` still runs, but beyond being deprecated it has a practical flaw:
`on_event` handlers do **not** run when you enter the app as a context manager in
tests, while `lifespan` does. Migrating fixes a class of "works in prod, unset in
tests" bugs.

`Annotated` dependencies are not cosmetic. `db: AsyncSession = Depends(get_db)`
is a parameter with a default, so it must follow every parameter without one —
which is why old handlers have their path parameters shuffled around. With
`Annotated`, argument order is yours again, and the alias (`DbSession`) is
reusable and greppable.

## SQLAlchemy 1.4 to 2.0

| Old | Current |
|---|---|
| `declarative_base()` | `class Base(DeclarativeBase)` |
| `Column(String)` | `Mapped[str] = mapped_column(String)` |
| `sessionmaker(class_=AsyncSession)` | `async_sessionmaker(...)` (properly typed) |
| `db.query(Model).filter(...)` | `select(Model).where(...)` + `db.execute()` |
| `selectinload("*")` | explicit `selectinload(Model.rel)` |
| `Query.get(id)` | `db.get(Model, id)` |
| implicit autocommit | explicit transaction boundaries |

`db.query(...)` still works in 2.0 as legacy API but has no async equivalent —
async code must use `select()`.

## Patterns worth replacing while you are in there

These are not version-forced. They are things a 2022 codebase usually has that
are worth fixing on the same pass, because you are already touching the files.

**Swallowing exceptions in the data layer.**

```python
async def create(self, db, obj_in):
    try:
        ...
        return db_obj
    except Exception as e:
        logger.error(e)          # returns None
```

The caller then does `obj.id` on `None` and gets a 500 with a traceback pointing
at the wrong file, while the real error is a line in a log. Let it raise and map
exception types to status codes in one exception handler.

**Committing inside every repository method.** Makes multi-step handlers
non-atomic. Move the commit to the session dependency — see
[sqlalchemy.md](sqlalchemy.md#the-transaction-boundary).

**`getattr(model, user_supplied_string)` for sorting.** Caller-controlled
attribute lookup. Replace with an allowlist that 422s.

**f-string SQL.** `text(f"SET x='{user_id}'")` is injectable whenever the value
comes from a token claim or a header. Use bound parameters:
`text("SELECT set_config('app.user_id', :uid, true)")`.

**`SET SESSION` on a pooled connection.** Session-scoped settings survive the
request and leak to whoever borrows that connection next. `session.close()` does
not undo them - the ROLLBACK it issues leaves `SET SESSION` in place. Use
`SET LOCAL` inside a transaction. See [multitenancy.md](multitenancy.md).

**Order these two fixes together.** Switching `SET SESSION` to `SET LOCAL` while
the repository still commits inside every method makes things *worse*: the commit
ends the transaction, the LOCAL setting evaporates, and an RLS policy reading
`current_setting(...)` then matches nothing and returns **zero rows** instead of
raising. You get a silent empty list rather than an error. Move the commit to the
request boundary in the same change, or keep the context in an `after_begin`
event listener that re-applies it per transaction.

**`jsonable_encoder` before an INSERT.** Beyond turning datetimes into strings, it
converts `Decimal("19.99")` to the float `19.99` (verified) - silent precision
loss on money columns. Use `.model_dump()`.

**Search filters that never ran.** Watch for guards like
`if getattr(self.model, column).of_type(String)` in a list comprehension.
`of_type()` exists on relationship attributes, not column attributes, so this
raises `AttributeError` (verified: *"Neither 'AnnotatedColumn' object nor
'Comparator' object has an attribute 'of_type'"*) - meaning that search path has
been dead since it was written. Two near-identical paginate methods where only
one has the guard is the tell.

**`BaseHTTPMiddleware` that reads the response body.** Consuming
`response.body_iterator` to log the body breaks streaming responses and buffers
every response in memory. Log at the handler or use a pure ASGI middleware that
does not touch the body.

**Config classes that read `os.environ` in the class body.** Evaluated once at
import, so tests cannot override them, and a typo'd variable name becomes a
`None` that fails much later. `pydantic-settings` validates at startup.

**Dead framework code.** A `common/exceptions.py` still importing Flask and
werkzeug in a FastAPI service is not harmless — it registers nothing, so the app
has *no* global exception handling while appearing to have some. Delete it and
register real handlers.

## Newer capabilities you can now use

- **Query parameter models** (0.115+) — collapse repeated pagination params.
- **`app.frontend()`** (0.138+) — serve a built SPA from the same process with
  correct client-side-routing fallback; 0.139 added dependency support so the
  frontend routes can be authenticated. Removes the separate static host for
  small deployments.
- **`lifespan` state** — attach shared clients (httpx, Redis) to `app.state` in
  lifespan instead of module-level globals, so tests get clean instances.
- **`Annotated` dependency aliases** — `DbSession`, `CurrentUser` as named types.
- **Pydantic `computed_field`** — derived response fields that cannot drift.
- **`TypeAdapter`** — validate/serialize non-model types without a wrapper model.
