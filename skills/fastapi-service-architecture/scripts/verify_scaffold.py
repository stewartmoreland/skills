"""Self-check for the scaffolded common/ layer.

Run it from the repo root after scaffolding, with src/ on the path:

    python .../scripts/verify_scaffold.py

It stands up an in-memory SQLite database, a throwaway Widget model, and a small
app wired exactly the way the templates intend, then asserts the behaviour that
is easy to break: page arithmetic, the sort allowlist, `extra="forbid"` on query
params, PATCH semantics, the error envelope, and computed fields reaching the
OpenAPI schema. 27 checks, no network, no Postgres.

SQLite is fine *here* because this exercises the framework wiring, not your
schema. Test your own repositories against real Postgres - see references/testing.md.
"""
import asyncio, os, sys
os.environ["DATABASE_URL"] = "postgresql+asyncpg://u:p@localhost:5432/db"
sys.path.insert(0, "src")

from datetime import datetime
from typing import Annotated
from uuid import uuid4

import httpx
from fastapi import Depends, FastAPI, Query
from sqlalchemy import JSON, DateTime, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, ConfigDict, Field

from common.database import Base
from common.pagination import Page, PageParams, PageResult
from common.repository import Repository
from common.errors import NotFoundError, register_exception_handlers
from common.deps import get_session


class Widget(Base):
    __tablename__ = "widgets"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WidgetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str | None = None
    config: dict = Field(default_factory=dict)

class WidgetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    description: str | None = None

class WidgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tenant_id: str
    name: str
    description: str | None = None
    created_at: datetime

class WidgetSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str


repo = Repository[Widget, WidgetCreate, WidgetUpdate](
    Widget,
    searchable_columns=["name", "description"],
    sortable_columns=["name", "created_at"],
    default_order_by="created_at",
)

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
TestSession = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def override_session():
    async with TestSession() as s:
        try:
            yield s
        except Exception:
            await s.rollback(); raise
        else:
            await s.commit()


app = FastAPI()
register_exception_handlers(app)
Db = Annotated[AsyncSession, Depends(get_session)]

@app.get("/widgets")
async def list_widgets(db: Db, params: Annotated[PageParams, Query()]) -> Page[WidgetSummary]:
    return Page[WidgetSummary].of(await repo.list(db, params, where=[Widget.tenant_id == "t1"]))

@app.post("/widgets", status_code=201)
async def create_widget(db: Db, payload: WidgetCreate) -> WidgetRead:
    return WidgetRead.model_validate(await repo.create(db, payload, tenant_id="t1"))

@app.get("/widgets/{wid}")
async def get_widget(db: Db, wid: str) -> WidgetRead:
    return WidgetRead.model_validate(await repo.get_or_404(db, wid))

@app.patch("/widgets/{wid}")
async def patch_widget(db: Db, wid: str, payload: WidgetUpdate) -> WidgetRead:
    obj = await repo.get_or_404(db, wid)
    return WidgetRead.model_validate(await repo.update(db, obj, payload))

@app.delete("/widgets/{wid}", status_code=204)
async def delete_widget(db: Db, wid: str) -> None:
    await repo.delete(db, wid)

app.dependency_overrides[get_session] = override_session

FAILS = []
def check(label, cond, extra=""):
    print(("PASS  " if cond else "FAIL  ") + label + (f"  [{extra}]" if extra and not cond else ""))
    if not cond: FAILS.append(label)


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        # seed 25 widgets
        for i in range(25):
            r = await c.post("/widgets", json={"name": f"widget-{i:02d}", "description": "alpha" if i % 2 else "beta"})
            assert r.status_code == 201, r.text
        first_id = (await c.get("/widgets?limit=1&order_by=name&order_desc=false")).json()["items"][0]["id"]

        r = await c.get("/widgets?page=1&limit=10")
        b = r.json()
        check("list returns 200", r.status_code == 200, r.text)
        check("page has 10 items", len(b["items"]) == 10, len(b["items"]))
        check("total is 25", b["total"] == 25, b["total"])
        check("computed pages == 3", b["pages"] == 3, b["pages"])
        check("has_next true on p1", b["has_next"] is True)
        check("has_previous false on p1", b["has_previous"] is False)
        check("summary schema trims fields", set(b["items"][0]) == {"id", "name"}, set(b["items"][0]))

        b3 = (await c.get("/widgets?page=3&limit=10")).json()
        check("last page has 5 items", len(b3["items"]) == 5, len(b3["items"]))
        check("has_next false on last page", b3["has_next"] is False)
        check("has_previous true on last page", b3["has_previous"] is True)

        b = (await c.get("/widgets?search=alpha")).json()
        check("search filters total", b["total"] == 12, b["total"])

        asc = (await c.get("/widgets?order_by=name&order_desc=false&limit=3")).json()
        desc = (await c.get("/widgets?order_by=name&order_desc=true&limit=3")).json()
        check("asc sort correct", [i["name"] for i in asc["items"]] == ["widget-00","widget-01","widget-02"], [i["name"] for i in asc["items"]])
        check("desc sort correct", [i["name"] for i in desc["items"]] == ["widget-24","widget-23","widget-22"], [i["name"] for i in desc["items"]])

        r = await c.get("/widgets?order_by=id_or_something_evil")
        check("non-allowlisted sort -> 422", r.status_code == 422, f"{r.status_code} {r.text}")
        check("422 names allowed columns", "allowed" in r.json().get("error", {}), r.text)

        r = await c.get("/widgets?limitt=5")
        check("unknown query param -> 422 (extra=forbid)", r.status_code == 422, r.status_code)
        r = await c.get("/widgets?limit=9999")
        check("limit over max -> 422", r.status_code == 422, r.status_code)
        r = await c.get("/widgets?page=0")
        check("page 0 -> 422", r.status_code == 422, r.status_code)

        r = await c.get("/widgets/does-not-exist")
        check("missing row -> 404", r.status_code == 404, r.status_code)
        check("404 uses error envelope", r.json().get("error", {}).get("code") == "not_found", r.text)

        r = await c.patch(f"/widgets/{first_id}", json={"name": "renamed"})
        check("patch 200", r.status_code == 200, r.text)
        check("patch changed name", r.json()["name"] == "renamed", r.text)
        check("patch left description intact (exclude_unset)", r.json()["description"] in ("alpha","beta"), r.json()["description"])
        r = await c.patch(f"/widgets/{first_id}", json={"bogus": 1})
        check("patch unknown field -> 422", r.status_code == 422, r.status_code)

        r = await c.delete(f"/widgets/{first_id}")
        check("delete 204", r.status_code == 204, r.status_code)
        check("total drops after delete", (await c.get("/widgets")).json()["total"] == 24)

        schema = app.openapi()
        props = schema["components"]["schemas"]["Page_WidgetSummary_"]["properties"]
        check("computed fields appear in OpenAPI", {"pages","has_next","has_previous"} <= set(props), set(props))

    await engine.dispose()
    print("\n" + ("ALL SMOKE TESTS PASSED" if not FAILS else f"{len(FAILS)} FAILURES: {FAILS}"))
    return 1 if FAILS else 0

sys.exit(asyncio.run(main()))
