#!/usr/bin/env python3
"""
dotlottie_packager.py — Assemble a dotLottie v2.0 .lottie archive from
animation, theme, state machine, image, and font source files.

Two modes:

1. From a source directory whose layout already mirrors the dotLottie spec:

    sources/
    ├── manifest.json
    ├── a/*.json
    ├── t/*.json   (optional)
    ├── s/*.json   (optional)
    ├── i/*        (optional)
    └── f/*        (optional)

   Usage: python dotlottie_packager.py --from-dir sources/ -o my.lottie

2. From an explicit file list with auto-generated manifest:

   Usage: python dotlottie_packager.py \\
              --animation a/loader.json \\
              --animation a/success.json \\
              --theme    t/dark.json \\
              --theme    t/light.json \\
              --state    s/toggle.json \\
              --initial-animation loader \\
              -o my.lottie

In both modes the output is a ZIP archive (Deflate) at the path given by -o.
The packager validates inputs before writing.

Spec: https://dotlottie.io/spec/2.0/
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

GENERATOR_TAG = "lottie-animation-skill@1.0"

# POSIX-compliant pattern from the dotLottie spec
NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._\- ]+$")


# --- Validation primitives -------------------------------------------------


class PackagerError(Exception):
    """Raised for any validation failure that should abort packaging."""


def _check_filename(name: str, kind: str) -> None:
    if not NAME_PATTERN.match(name):
        raise PackagerError(
            f"Invalid {kind} filename {name!r} — must match ^[a-zA-Z0-9._\\- ]+$"
        )


def _check_json_load(path: Path) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        raise PackagerError(f"File not found: {path}")
    except json.JSONDecodeError as e:
        raise PackagerError(f"Invalid JSON in {path}: {e}")


def validate_lottie_animation(path: Path) -> None:
    """Light shape check on a Lottie file — full validation lives in
    validate_lottie.py. Here we just confirm it's parseable JSON with the
    minimal Lottie fields."""
    data = _check_json_load(path)
    required = {"v", "fr", "ip", "op", "w", "h", "layers"}
    missing = required - set(data.keys())
    if missing:
        raise PackagerError(
            f"{path}: not a valid Lottie animation — missing top-level "
            f"field(s): {', '.join(sorted(missing))}"
        )


def validate_theme(path: Path) -> None:
    data = _check_json_load(path)
    if not isinstance(data, dict) or "rules" not in data:
        raise PackagerError(f"{path}: theme must be an object with a 'rules' array")
    if not isinstance(data["rules"], list):
        raise PackagerError(f"{path}: theme 'rules' must be an array")
    allowed_types = {"Color", "Scalar", "Position", "Vector", "Gradient", "Image", "Text"}
    for i, rule in enumerate(data["rules"]):
        if not isinstance(rule, dict):
            raise PackagerError(f"{path}: rule[{i}] must be an object")
        if "id" not in rule:
            raise PackagerError(f"{path}: rule[{i}] missing 'id'")
        if "type" not in rule:
            raise PackagerError(f"{path}: rule[{i}] missing 'type'")
        if rule["type"] not in allowed_types:
            raise PackagerError(
                f"{path}: rule[{i}] has invalid type {rule['type']!r}; "
                f"expected one of {sorted(allowed_types)}"
            )
        has_value = "value" in rule
        has_kfs = "keyframes" in rule
        has_expr = "expression" in rule
        if not (has_value or has_kfs or has_expr):
            raise PackagerError(
                f"{path}: rule[{i}] ({rule['id']}) needs one of value/keyframes/expression"
            )
        if has_value and has_kfs:
            raise PackagerError(
                f"{path}: rule[{i}] ({rule['id']}) has both 'value' and 'keyframes' "
                f"— exactly one is allowed"
            )


def validate_state_machine(path: Path, known_animations: set[str]) -> None:
    data = _check_json_load(path)
    if "initial" not in data:
        raise PackagerError(f"{path}: state machine missing 'initial'")
    if "states" not in data or not isinstance(data["states"], list) or len(data["states"]) == 0:
        raise PackagerError(f"{path}: state machine missing non-empty 'states' array")

    state_names: set[str] = set()
    for i, state in enumerate(data["states"]):
        if not isinstance(state, dict):
            raise PackagerError(f"{path}: states[{i}] must be an object")
        name = state.get("name")
        ty = state.get("type")
        if not name:
            raise PackagerError(f"{path}: states[{i}] missing 'name'")
        if name in state_names:
            raise PackagerError(f"{path}: duplicate state name {name!r}")
        state_names.add(name)
        if ty not in ("PlaybackState", "GlobalState"):
            raise PackagerError(
                f"{path}: states[{i}] ({name}) has invalid type {ty!r}; "
                f"expected PlaybackState or GlobalState"
            )
        if ty == "PlaybackState":
            anim_id = state.get("animation")
            if not anim_id:
                raise PackagerError(
                    f"{path}: PlaybackState {name!r} missing 'animation'"
                )
            if anim_id not in known_animations:
                raise PackagerError(
                    f"{path}: PlaybackState {name!r} references animation "
                    f"{anim_id!r} which is not in the manifest"
                )
            if state.get("final") and state.get("transitions"):
                raise PackagerError(
                    f"{path}: state {name!r} is final but has transitions"
                )

    # All transitions point to valid states
    for state in data["states"]:
        for j, t in enumerate(state.get("transitions", []) or []):
            target = t.get("toState")
            if target not in state_names:
                raise PackagerError(
                    f"{path}: state {state['name']!r} transition[{j}] "
                    f"targets unknown state {target!r}"
                )
            t_type = t.get("type")
            if t_type not in ("Transition", "Tweened"):
                raise PackagerError(
                    f"{path}: state {state['name']!r} transition[{j}] has "
                    f"invalid type {t_type!r}"
                )
            if t_type == "Tweened":
                if "duration" not in t or "easing" not in t:
                    raise PackagerError(
                        f"{path}: state {state['name']!r} Tweened transition[{j}] "
                        f"requires both duration and easing"
                    )
                easing = t.get("easing")
                if not isinstance(easing, list) or len(easing) != 4:
                    raise PackagerError(
                        f"{path}: Tweened easing must be a 4-number array "
                        f"[x1,y1,x2,y2], got {easing!r}"
                    )

    # Inputs are unique
    input_names: set[str] = set()
    for i, inp in enumerate(data.get("inputs", []) or []):
        n = inp.get("name")
        if not n:
            raise PackagerError(f"{path}: inputs[{i}] missing 'name'")
        if n in input_names:
            raise PackagerError(f"{path}: duplicate input name {n!r}")
        input_names.add(n)

    # Initial state exists
    if data["initial"] not in state_names:
        raise PackagerError(
            f"{path}: initial state {data['initial']!r} not found in states"
        )

    # OnComplete/OnLoopComplete reference real states
    for i, interaction in enumerate(data.get("interactions", []) or []):
        if interaction.get("type") in ("OnComplete", "OnLoopComplete"):
            sname = interaction.get("stateName")
            if sname not in state_names:
                raise PackagerError(
                    f"{path}: interactions[{i}] references unknown state {sname!r}"
                )


def validate_manifest(manifest: dict, sources: dict) -> None:
    """Cross-check the manifest against the actual source files.

    sources: { 'animations': {id -> Path}, 'themes': {id -> Path},
               'stateMachines': {id -> Path} }
    """
    if manifest.get("version") != "2":
        raise PackagerError(
            f"Manifest 'version' must be the string \"2\", got {manifest.get('version')!r}"
        )

    anims = manifest.get("animations", [])
    if not anims:
        raise PackagerError("Manifest must declare at least one animation")

    declared_anim_ids = set()
    for i, a in enumerate(anims):
        if "id" not in a:
            raise PackagerError(f"animations[{i}] missing 'id'")
        _check_filename(a["id"], "animation id")
        if a["id"] in declared_anim_ids:
            raise PackagerError(f"Duplicate animation id {a['id']!r}")
        declared_anim_ids.add(a["id"])
        if a["id"] not in sources["animations"]:
            raise PackagerError(
                f"animations[{i}] id {a['id']!r} has no matching file in a/"
            )

    declared_theme_ids = set()
    for t in manifest.get("themes", []) or []:
        _check_filename(t["id"], "theme id")
        if t["id"] not in sources["themes"]:
            raise PackagerError(
                f"theme {t['id']!r} declared in manifest but no t/{t['id']}.json file"
            )
        declared_theme_ids.add(t["id"])

    declared_sm_ids = set()
    for sm in manifest.get("stateMachines", []) or []:
        _check_filename(sm["id"], "state machine id")
        if sm["id"] not in sources["stateMachines"]:
            raise PackagerError(
                f"state machine {sm['id']!r} declared in manifest but no s/{sm['id']}.json file"
            )
        declared_sm_ids.add(sm["id"])

    # Per-animation scoping checks
    for a in anims:
        if a.get("initialTheme") and a["initialTheme"] not in declared_theme_ids:
            raise PackagerError(
                f"animation {a['id']!r} initialTheme {a['initialTheme']!r} "
                f"not in manifest themes"
            )
        for scoped in a.get("themes", []) or []:
            if scoped not in declared_theme_ids:
                raise PackagerError(
                    f"animation {a['id']!r} scoped theme {scoped!r} not in manifest themes"
                )

    initial = manifest.get("initial")
    if initial:
        if "stateMachine" in initial and initial["stateMachine"] not in declared_sm_ids:
            raise PackagerError(
                f"initial.stateMachine {initial['stateMachine']!r} not declared in manifest"
            )
        if "animation" in initial and initial["animation"] not in declared_anim_ids:
            raise PackagerError(
                f"initial.animation {initial['animation']!r} not declared in manifest"
            )


# --- Source discovery ------------------------------------------------------


def discover_sources(source_dir: Path) -> tuple[dict, dict]:
    """Walk source_dir for the standard layout. Returns (manifest_dict, source_map)."""
    if not source_dir.is_dir():
        raise PackagerError(f"{source_dir} is not a directory")
    manifest_path = source_dir / "manifest.json"
    if not manifest_path.exists():
        raise PackagerError(f"{source_dir}/manifest.json not found")
    manifest = _check_json_load(manifest_path)

    sources = {"animations": {}, "themes": {}, "stateMachines": {}, "images": {}, "fonts": {}}

    def index(subdir: str, key: str, extensions: tuple[str, ...] | None) -> None:
        d = source_dir / subdir
        if not d.is_dir():
            return
        for f in sorted(d.iterdir()):
            if not f.is_file():
                continue
            if extensions and not f.name.lower().endswith(extensions):
                continue
            stem = f.stem
            _check_filename(f.name, f"{subdir} filename")
            sources[key][stem] = f

    index("a", "animations", (".json",))
    index("t", "themes", (".json",))
    index("s", "stateMachines", (".json",))
    index("i", "images", None)  # any extension
    index("f", "fonts", None)

    return manifest, sources


def build_manifest_from_files(
    animations: list[Path],
    themes: list[Path],
    state_machines: list[Path],
    initial_animation: str | None,
    initial_state_machine: str | None,
) -> dict:
    """Construct a minimal manifest dict from explicit input files."""
    manifest: dict = {
        "version": "2",
        "generator": GENERATOR_TAG,
        "animations": [{"id": p.stem} for p in animations],
    }
    if themes:
        manifest["themes"] = [{"id": p.stem} for p in themes]
    if state_machines:
        manifest["stateMachines"] = [{"id": p.stem} for p in state_machines]
    if initial_animation or initial_state_machine:
        initial: dict = {}
        if initial_state_machine:
            initial["stateMachine"] = initial_state_machine
        if initial_animation:
            initial["animation"] = initial_animation
        manifest["initial"] = initial
    return manifest


# --- Packaging -------------------------------------------------------------


def write_archive(output_path: Path, manifest: dict, sources: dict) -> int:
    """Write the .lottie archive. Returns the byte size."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

        for anim_id, src_path in sources["animations"].items():
            zf.write(src_path, f"a/{src_path.name}")
        for theme_id, src_path in sources["themes"].items():
            zf.write(src_path, f"t/{src_path.name}")
        for sm_id, src_path in sources["stateMachines"].items():
            zf.write(src_path, f"s/{src_path.name}")
        for img_id, src_path in sources["images"].items():
            zf.write(src_path, f"i/{src_path.name}")
        for font_id, src_path in sources["fonts"].items():
            zf.write(src_path, f"f/{src_path.name}")

    return output_path.stat().st_size


# --- CLI -------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(description="Package a dotLottie v2.0 archive.")
    p.add_argument("-o", "--output", help="Output .lottie file path (required unless --check-only)")
    p.add_argument("--check-only", action="store_true", help="Validate inputs without writing the archive")
    p.add_argument("--from-dir", help="Source directory in dotLottie layout")
    p.add_argument("--animation", action="append", default=[], help="Animation JSON file (repeatable)")
    p.add_argument("--theme", action="append", default=[], help="Theme JSON file (repeatable)")
    p.add_argument("--state", action="append", default=[], help="State machine JSON file (repeatable)")
    p.add_argument("--image", action="append", default=[], help="Image asset (repeatable)")
    p.add_argument("--font", action="append", default=[], help="Font asset (repeatable)")
    p.add_argument("--initial-animation", help="Initial animation id (sets manifest.initial.animation)")
    p.add_argument("--initial-state-machine", help="Initial state machine id (sets manifest.initial.stateMachine)")
    p.add_argument("--quiet", action="store_true", help="Suppress per-file progress output")
    args = p.parse_args()

    try:
        if args.from_dir:
            if args.animation or args.theme or args.state:
                raise PackagerError(
                    "--from-dir is mutually exclusive with --animation/--theme/--state"
                )
            manifest, sources = discover_sources(Path(args.from_dir))
        else:
            if not args.animation:
                raise PackagerError(
                    "Need at least one --animation, or use --from-dir"
                )
            anim_paths = [Path(p) for p in args.animation]
            theme_paths = [Path(p) for p in args.theme]
            sm_paths = [Path(p) for p in args.state]
            img_paths = [Path(p) for p in args.image]
            font_paths = [Path(p) for p in args.font]

            for path in anim_paths + theme_paths + sm_paths + img_paths + font_paths:
                if not path.exists():
                    raise PackagerError(f"File not found: {path}")
                _check_filename(path.name, "source filename")

            manifest = build_manifest_from_files(
                anim_paths, theme_paths, sm_paths,
                args.initial_animation, args.initial_state_machine,
            )
            sources = {
                "animations":    {p.stem: p for p in anim_paths},
                "themes":        {p.stem: p for p in theme_paths},
                "stateMachines": {p.stem: p for p in sm_paths},
                "images":        {p.stem: p for p in img_paths},
                "fonts":         {p.stem: p for p in font_paths},
            }

        # Validation pass — checks structural integrity before writing anything
        for anim_id, path in sources["animations"].items():
            validate_lottie_animation(path)
        for theme_id, path in sources["themes"].items():
            validate_theme(path)
        animation_ids = set(sources["animations"].keys())
        for sm_id, path in sources["stateMachines"].items():
            validate_state_machine(path, animation_ids)
        validate_manifest(manifest, sources)

        if args.check_only:
            if not args.quiet:
                print("✓ Validation passed (--check-only, no archive written)")
                print(f"  animations:    {len(sources['animations'])}")
                if sources["themes"]:
                    print(f"  themes:        {len(sources['themes'])}")
                if sources["stateMachines"]:
                    print(f"  stateMachines: {len(sources['stateMachines'])}")
            return 0

        if not args.output:
            raise PackagerError("--output is required unless --check-only is set")

        # Write the archive
        out = Path(args.output)
        size = write_archive(out, manifest, sources)

    except PackagerError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"✓ Packaged {out} ({size:,} bytes)")
        print(f"  manifest version: {manifest.get('version')}")
        print(f"  animations:    {len(sources['animations'])}")
        if sources["themes"]:
            print(f"  themes:        {len(sources['themes'])}")
        if sources["stateMachines"]:
            print(f"  stateMachines: {len(sources['stateMachines'])}")
        if sources["images"]:
            print(f"  images:        {len(sources['images'])}")
        if sources["fonts"]:
            print(f"  fonts:         {len(sources['fonts'])}")
        if manifest.get("initial"):
            print(f"  initial:       {manifest['initial']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
