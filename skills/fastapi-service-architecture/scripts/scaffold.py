#!/usr/bin/env python3
"""Scaffold the layered FastAPI structure in whichever layout the repo calls for.

Single service - one app, one deployable:

    python scaffold.py --layout single --app myapi --resource order

    src/
    ├── common/          shared infrastructure
    ├── routes/          orders.py
    ├── access/          orders.py
    ├── schemas/         orders.py
    ├── modules/
    └── main.py

uv workspace - several deployables sharing one library and one lockfile:

    python scaffold.py --layout workspace --service billing --resource invoice

    pyproject.toml                  [tool.uv.workspace] members
    packages/common/src/common/     shared library
    services/billing/src/billing/   routes/ access/ schemas/ modules/ main.py

The `common.*` import path is identical in both layouts, so promoting a single
service into a workspace never rewrites a shared-layer import. Run it again with
a new --service to add the second deployable.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


def _camel(name: str) -> str:
    return "".join(p.capitalize() for p in re.split(r"[_\-\s]+", name) if p)


def _plural(name: str) -> str:
    if name.endswith(("s", "x", "z", "ch", "sh")):
        return name + "es"
    if name.endswith("y") and name[-2:-1] not in "aeiou":
        return name[:-1] + "ies"
    return name + "s"


def _subs(resource: str, service_pkg: str | None, app_name: str = "service") -> list[tuple[str, str]]:
    """Longest patterns first so 'widgets' is never half-rewritten by 'widget'."""
    rp = _plural(resource)
    # In a single-service layout there is no service package, so `service.x` -> `x`.
    prefix = f"{service_pkg}." if service_pkg else ""
    return [
        ("widget_repository", f"{resource}_repository"),
        ("WidgetRepository", f"{_camel(resource)}Repository"),
        ("widgets_router", f"{rp}_router"),
        ("WidgetSummary", f"{_camel(resource)}Summary"),
        ("WidgetCreate", f"{_camel(resource)}Create"),
        ("WidgetUpdate", f"{_camel(resource)}Update"),
        ("WidgetRead", f"{_camel(resource)}Read"),
        ("WidgetBase", f"{_camel(resource)}Base"),
        ("widget_tag_table", f"{resource}_tag_table"),
        ("widgets", rp),
        ("Widgets", _camel(rp)),
        ("Widget", _camel(resource)),
        ("widget", resource),
        ("from service.", f"from {prefix}"),
        ('"service.main:app"', f'"{prefix}main:app"'),
        ('title="service"', f'title="{app_name}"'),
        ('description="Service API."', f'description="{_camel(app_name)} API."'),
        ('distribution="my-distribution-name"', f'distribution="{app_name}"'),
    ]


def _render(text: str, subs: list[tuple[str, str]]) -> str:
    for old, new in subs:
        text = text.replace(old, new)
    return text


def _write(path: Path, content: str, force: bool) -> bool:
    if path.exists() and not force:
        print(f"  skip (exists): {path}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"  wrote: {path}")
    return True


def _common_layer(target: Path, force: bool) -> None:
    """Write common/ - identical content in both layouts."""
    for src in sorted((ASSETS / "common").glob("*.py")):
        if src.name in ("models_example.py", "alembic_env.py"):
            continue
        dst = (
            target / "database" / "__init__.py"
            if src.name == "database.py"
            else target / src.name
        )
        _write(dst, src.read_text(), force)
    models = target / "database" / "models"
    _write(
        models / "__init__.py",
        '"""Import every model module here so Base.metadata is complete.\n\n'
        'Alembic autogenerate only sees tables reachable from this import.\n"""\n',
        force,
    )
    _write(models / "example.py", (ASSETS / "common/models_example.py").read_text(), force)


def _resource_model(models_dir: Path, resource: str, force: bool) -> None:
    """Write the resource's model and re-export it, so the scaffold actually runs.

    Without this the generated access layer imports a model that does not exist and
    the app fails on the first import - a poor first impression of the pattern.
    """
    subs = _subs(resource, None)
    rp = _plural(resource)
    _write(models_dir / f"{rp}.py",
           _render((ASSETS / "common/model_template.py").read_text(), subs), force)
    init = models_dir / "__init__.py"
    line = f"from .{rp} import {_camel(resource)}\n"
    existing = init.read_text() if init.exists() else ""
    if line not in existing:
        init.write_text(existing + line)
        print(f"  updated: {init}")


def _resource_files(target: Path, resource: str, service_pkg: str | None, force: bool,
                    app_name: str = "service") -> None:
    """Write routes/ access/ schemas/ modules/ for one resource."""
    subs = _subs(resource, service_pkg, app_name)
    rp = _plural(resource)
    mapping = {
        ASSETS / "service/routes/__init__.py": target / "routes/__init__.py",
        ASSETS / "service/routes/widgets.py": target / "routes" / f"{rp}.py",
        ASSETS / "service/access/__init__.py": target / "access/__init__.py",
        ASSETS / "service/access/widgets.py": target / "access" / f"{rp}.py",
        ASSETS / "service/schemas/__init__.py": target / "schemas/__init__.py",
        ASSETS / "service/schemas/widgets.py": target / "schemas" / f"{rp}.py",
        ASSETS / "service/main.py": target / "main.py",
    }
    for src, dst in mapping.items():
        _write(dst, _render(src.read_text(), subs), force)
    _write(target / "modules" / "__init__.py",
           '"""Domain logic and external clients for this service."""\n', force)
    if service_pkg:
        # uv_build needs the package root to exist. In the single layout src/ is a
        # path entry rather than a package, so it must NOT get an __init__.py.
        _write(target / "__init__.py", "", force)


def scaffold_single(dest: Path, app: str, resource: str, force: bool) -> None:
    src = dest / "src"
    print(f"single-service layout -> {dest}")
    _write(dest / "pyproject.toml",
           (ASSETS / "pyproject/single.toml").read_text().replace("__APP__", app), force)
    _common_layer(src / "common", force)
    _resource_model(src / "common/database/models", resource, force)
    _resource_files(src, resource, None, force, app_name=app)
    print(f"\n  uv sync")
    print(f"  uv run uvicorn main:app --app-dir src --reload")


def scaffold_workspace(dest: Path, service: str, resource: str, force: bool) -> None:
    print(f"uv workspace layout -> {dest}")
    root = dest / "pyproject.toml"
    if not root.exists() or force:
        _write(root, (ASSETS / "pyproject/workspace_root.toml").read_text(), force)
    common_pkg = dest / "packages/common"
    if not (common_pkg / "pyproject.toml").exists() or force:
        _write(common_pkg / "pyproject.toml", (ASSETS / "pyproject/common.toml").read_text(), force)
        _common_layer(common_pkg / "src/common", force)
    else:
        print("  packages/common already exists - leaving it alone")

    _resource_model(common_pkg / "src/common/database/models", resource, force)

    svc = dest / "services" / service
    _write(svc / "pyproject.toml",
           (ASSETS / "pyproject/service.toml").read_text().replace("__SERVICE__", service), force)
    _resource_files(svc / "src" / service, resource, service, force, app_name=service)
    print(f"\n  uv sync --package {service}")
    print(f"  uv run --package {service} uvicorn {service}.main:app --reload")


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--layout", choices=["single", "workspace"], required=True,
                   help="single = one deployable; workspace = uv workspace monorepo")
    p.add_argument("--dest", type=Path, default=Path("."), help="repo root (default: .)")
    p.add_argument("--app", default="myapi", help="single layout: project name")
    p.add_argument("--service", help="workspace layout: service package name")
    p.add_argument("--resource", default="widget", help="first resource, singular")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    if args.layout == "workspace" and not args.service:
        p.error("--layout workspace requires --service NAME")
    if args.resource == args.service:
        p.error(
            f"--service and --resource are both {args.resource!r}; that produces "
            f"services/{args.service}/src/{args.service}/routes/{_plural(args.resource)}.py, "
            "which repeats the name. Name the service for its domain "
            "(billing, catalog), not for its first resource."
        )

    dest = args.dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    if args.layout == "single":
        scaffold_single(dest, args.app, args.resource, args.force)
    else:
        scaffold_workspace(dest, args.service, args.resource, args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
