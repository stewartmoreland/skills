# Repository layout

## Contents
- [Pick the layout from the deployable count](#pick-the-layout-from-the-deployable-count)
- [Single service](#single-service)
- [uv workspace monorepo](#uv-workspace-monorepo)
- [How uv workspaces actually work](#how-uv-workspaces-actually-work)
- [When a workspace is the wrong tool](#when-a-workspace-is-the-wrong-tool)
- [Naming](#naming)
- [Promoting a single service into a workspace](#promoting-a-single-service-into-a-workspace)

## Pick the layout from the deployable count

The layering (routes → access → schemas) is the same either way. What changes is
how many packages it is spread across, and that follows from one question: **how
many processes ship from this repo?**

| Deployables | Layout | Shared code lives in |
|---|---|---|
| One | Single service | `src/common/` |
| More than one | uv workspace | `packages/common/` |

Do not add the per-service package level "in case we split later". In a
single-service repo it produces paths like `src/orders/routes/orders.py`, where
the name appears twice and carries no information. Promoting later is a directory
move, and because `common` keeps its import path in both layouts, it does not
touch a single shared-layer import.

## Single service

```
repo/
├── pyproject.toml          [tool.uv] package = false
└── src/
    ├── common/             app.py settings.py database/ deps.py
    │                       repository.py pagination.py errors.py security.py
    ├── routes/             orders.py       - HTTP only
    ├── access/             orders.py       - SQL only
    ├── schemas/            orders.py       - Pydantic
    ├── modules/            domain logic, external clients
    └── main.py             builds the app, mounts routers
```

```bash
python scripts/scaffold.py --layout single --app myapi --resource order
uv sync
uv run uvicorn main:app --app-dir src --reload
```

`[tool.uv] package = false` marks this an application rather than a library: uv
resolves and installs dependencies but builds nothing. That is what lets `src/`
hold several sibling packages instead of forcing everything under one package
directory. `src` reaches the import path through `--app-dir src` for uvicorn and
`pythonpath = ["src"]` for pytest.

## uv workspace monorepo

```
repo/
├── pyproject.toml                      [tool.uv.workspace] members
├── uv.lock                             one lockfile for everything
├── packages/
│   └── common/
│       ├── pyproject.toml
│       └── src/common/                 the shared library
└── services/
    ├── billing/
    │   ├── pyproject.toml              depends on common
    │   └── src/billing/                routes/ access/ schemas/ modules/ main.py
    └── catalog/
        └── ...
```

```bash
python scripts/scaffold.py --layout workspace --service billing --resource invoice
uv sync --package billing
uv run --package billing uvicorn billing.main:app --reload
```

Run it again with a different `--service` to add the next deployable; it leaves
`packages/common/` alone.

## How uv workspaces actually work

The root declares members and owns the lockfile. It needs no `[project]` table of
its own — a root that builds nothing is the normal shape for a service monorepo:

```toml
# repo/pyproject.toml
[tool.uv.workspace]
members = ["packages/*", "services/*"]
exclude = ["packages/scratch"]
```

Each member depends on the shared library through `[tool.uv.sources]`, which tells
uv to resolve it from the workspace instead of PyPI:

```toml
# repo/services/billing/pyproject.toml
[project]
name = "billing"
dependencies = ["common", "uvicorn[standard]>=0.32"]

[tool.uv.sources]
common = { workspace = true }
```

What this buys you:

- **One lockfile, one virtualenv.** Every service resolves against the same
  dependency set, so "works in billing, breaks in catalog" stops being possible.
- **Editable member dependencies.** An edit in `packages/common` is live in every
  service immediately — no reinstall, no `pip install -e` dance.
- **`--package` scoping.** `uv sync --package billing` and
  `uv run --package billing ...` work from anywhere in the repo.
- **Per-service dependency lists.** `uvicorn` belongs to services, not to
  `common`. Keeping `common` free of service-specific dependencies is what stops
  it from becoming the place where everything accumulates.

Sources declared in the root's `[tool.uv.sources]` are inherited by every member
unless a member overrides them.

## When a workspace is the wrong tool

A workspace enforces **one `requires-python` intersection across all members and
one virtual environment**. That is exactly wrong when:

- two services need conflicting versions of the same dependency, or
- a service must pin an older Python than the rest.

In those cases use path dependencies instead, which keep per-package
environments:

```toml
[tool.uv.sources]
common = { path = "packages/common" }
```

The trade is that `uv run --package` is no longer available; commands run from
the package directory. Reach for this only when you actually hit the conflict —
the shared lockfile is most of the value.

## Naming

Name a service for its **domain**, not for its first resource. `--service orders
--resource order` yields `services/orders/src/orders/routes/orders.py`, which
says "orders" three times and has to be renamed the moment a second resource
arrives. `billing` holding `invoices.py` and `payments.py` reads correctly on day
one and on day two hundred. The scaffold refuses the duplicated form.

## Promoting a single service into a workspace

The move is mechanical because `common` is `common` in both layouts:

1. `mkdir -p packages/common services/<name>`
2. `git mv src/common packages/common/src/common`
3. `git mv src/{routes,access,schemas,modules,main.py} services/<name>/src/<name>/`
4. Add `packages/common/pyproject.toml` and `services/<name>/pyproject.toml`
   (templates in `assets/pyproject/`), and replace the root `pyproject.toml`
   with the workspace root form.
5. `uv lock && uv sync --package <name>`

Import churn is limited to the service's own modules gaining their package
prefix — `from routes import ...` becomes `from <name>.routes import ...`. Every
`from common.…` import is untouched, which is the majority of the imports and the
whole reason to keep the name stable.
