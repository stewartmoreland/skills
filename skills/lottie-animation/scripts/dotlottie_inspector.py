#!/usr/bin/env python3
"""
dotlottie_inspector.py — Read a .lottie archive and report its structure
without extracting it.

Use cases:
  - QA: confirm a package contains the animations/themes/state machines you expect
  - Debugging: see slot IDs declared in animations vs slot IDs targeted by themes
  - Reverse-engineering an existing .lottie to understand its layout

Usage:
    python dotlottie_inspector.py path/to/file.lottie
    python dotlottie_inspector.py path/to/file.lottie --json    # machine-readable
    python dotlottie_inspector.py path/to/file.lottie --slots   # list all slot IDs
    python dotlottie_inspector.py path/to/file.lottie --extract animation_name
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path


def find_slot_ids(obj, found: set[str], path: str = "") -> None:
    """Recursively walk a Lottie JSON object collecting any 'sid' values."""
    if isinstance(obj, dict):
        if "sid" in obj and isinstance(obj["sid"], str):
            found.add(obj["sid"])
        for k, v in obj.items():
            find_slot_ids(v, found, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            find_slot_ids(item, found, f"{path}[{i}]")


def u32_rgba_to_hex(value: int) -> str:
    """Convert a u32 RGBA integer to '#RRGGBBAA' string."""
    if not isinstance(value, int):
        return repr(value)
    r = (value >> 24) & 0xFF
    g = (value >> 16) & 0xFF
    b = (value >> 8) & 0xFF
    a = value & 0xFF
    return f"#{r:02X}{g:02X}{b:02X}{a:02X}"


def inspect_archive(archive_path: Path) -> dict:
    """Read a .lottie file and return a structured dict describing it."""
    if not archive_path.exists():
        raise FileNotFoundError(archive_path)

    info: dict = {
        "path": str(archive_path),
        "size_bytes": archive_path.stat().st_size,
        "manifest": None,
        "animations": {},
        "themes": {},
        "stateMachines": {},
        "images": [],
        "fonts": [],
        "unknown_files": [],
        "issues": [],
    }

    try:
        with zipfile.ZipFile(archive_path) as zf:
            names = zf.namelist()
            info["file_count"] = len(names)

            if "manifest.json" not in names:
                info["issues"].append("manifest.json missing — not a valid dotLottie")
                return info

            with zf.open("manifest.json") as f:
                info["manifest"] = json.loads(f.read().decode("utf-8"))

            for name in sorted(names):
                if name == "manifest.json":
                    continue
                if name.endswith("/"):
                    continue
                if name.startswith("a/"):
                    stem = Path(name).stem
                    with zf.open(name) as f:
                        try:
                            data = json.loads(f.read().decode("utf-8"))
                        except json.JSONDecodeError as e:
                            info["issues"].append(f"{name}: invalid JSON — {e}")
                            continue
                    slots: set[str] = set()
                    find_slot_ids(data, slots)
                    info["animations"][stem] = {
                        "file": name,
                        "size": zf.getinfo(name).file_size,
                        "nm": data.get("nm"),
                        "fr": data.get("fr"),
                        "ip": data.get("ip"),
                        "op": data.get("op"),
                        "w":  data.get("w"),
                        "h":  data.get("h"),
                        "layers": len(data.get("layers", [])),
                        "slot_ids": sorted(slots),
                        "markers": [m.get("cm") for m in data.get("markers", []) or []],
                    }
                elif name.startswith("t/"):
                    stem = Path(name).stem
                    with zf.open(name) as f:
                        try:
                            data = json.loads(f.read().decode("utf-8"))
                        except json.JSONDecodeError as e:
                            info["issues"].append(f"{name}: invalid JSON — {e}")
                            continue
                    rules = data.get("rules", [])
                    targeted_slots = sorted({r.get("id") for r in rules if r.get("id")})
                    rule_types: dict[str, int] = {}
                    for r in rules:
                        t = r.get("type", "?")
                        rule_types[t] = rule_types.get(t, 0) + 1
                    info["themes"][stem] = {
                        "file": name,
                        "rules": len(rules),
                        "targeted_slots": targeted_slots,
                        "rule_types": rule_types,
                    }
                elif name.startswith("s/"):
                    stem = Path(name).stem
                    with zf.open(name) as f:
                        try:
                            data = json.loads(f.read().decode("utf-8"))
                        except json.JSONDecodeError as e:
                            info["issues"].append(f"{name}: invalid JSON — {e}")
                            continue
                    states = data.get("states", [])
                    info["stateMachines"][stem] = {
                        "file": name,
                        "initial": data.get("initial"),
                        "states": [
                            {
                                "name": s.get("name"),
                                "type": s.get("type"),
                                "animation": s.get("animation"),
                                "transitions": len(s.get("transitions", []) or []),
                            }
                            for s in states
                        ],
                        "interactions": len(data.get("interactions", []) or []),
                        "inputs": [
                            {"name": i.get("name"), "type": i.get("type")}
                            for i in data.get("inputs", []) or []
                        ],
                    }
                elif name.startswith("i/"):
                    info["images"].append({
                        "file": name,
                        "size": zf.getinfo(name).file_size,
                    })
                elif name.startswith("f/"):
                    info["fonts"].append({
                        "file": name,
                        "size": zf.getinfo(name).file_size,
                    })
                else:
                    info["unknown_files"].append(name)
    except zipfile.BadZipFile:
        info["issues"].append("not a valid ZIP archive")
    return info


def cross_reference_issues(info: dict) -> list[str]:
    """Find inconsistencies between manifest, animations, themes, and state machines."""
    issues = []
    manifest = info.get("manifest") or {}

    declared_anim_ids = {a.get("id") for a in manifest.get("animations", []) or []}
    declared_theme_ids = {t.get("id") for t in manifest.get("themes", []) or []}
    declared_sm_ids = {s.get("id") for s in manifest.get("stateMachines", []) or []}

    actual_anims = set(info["animations"].keys())
    actual_themes = set(info["themes"].keys())
    actual_sms = set(info["stateMachines"].keys())

    for missing in declared_anim_ids - actual_anims:
        issues.append(f"Manifest declares animation {missing!r} but a/{missing}.json is missing")
    for orphan in actual_anims - declared_anim_ids:
        issues.append(f"a/{orphan}.json exists but is not declared in manifest.animations")
    for missing in declared_theme_ids - actual_themes:
        issues.append(f"Manifest declares theme {missing!r} but t/{missing}.json is missing")
    for orphan in actual_themes - declared_theme_ids:
        issues.append(f"t/{orphan}.json exists but is not declared in manifest.themes")
    for missing in declared_sm_ids - actual_sms:
        issues.append(f"Manifest declares state machine {missing!r} but s/{missing}.json is missing")
    for orphan in actual_sms - declared_sm_ids:
        issues.append(f"s/{orphan}.json exists but is not declared in manifest.stateMachines")

    # Theme slot IDs that don't appear in any animation
    all_slot_ids: set[str] = set()
    for a in info["animations"].values():
        all_slot_ids.update(a["slot_ids"])
    for theme_id, theme in info["themes"].items():
        for slot in theme["targeted_slots"]:
            if slot not in all_slot_ids:
                issues.append(
                    f"Theme {theme_id!r} targets slot {slot!r} that no animation declares"
                )

    # State machine references unknown animations
    for sm_id, sm in info["stateMachines"].items():
        for state in sm["states"]:
            anim = state.get("animation")
            if anim and anim not in actual_anims:
                issues.append(
                    f"State machine {sm_id!r} state {state['name']!r} references "
                    f"unknown animation {anim!r}"
                )

    # Manifest version
    if manifest.get("version") != "2":
        issues.append(
            f"manifest.version is {manifest.get('version')!r}, expected the string \"2\""
        )

    return issues


def format_human(info: dict) -> str:
    out: list[str] = []
    out.append(f"=== {info['path']} ({info['size_bytes']:,} bytes, "
               f"{info['file_count']} files in archive) ===")

    if info.get("issues"):
        out.append("\nArchive-level issues:")
        for issue in info["issues"]:
            out.append(f"  ✗ {issue}")
        return "\n".join(out)

    manifest = info["manifest"] or {}
    out.append(f"\nManifest:")
    out.append(f"  version:   {manifest.get('version')!r}")
    if manifest.get("generator"):
        out.append(f"  generator: {manifest['generator']!r}")
    if manifest.get("initial"):
        out.append(f"  initial:   {manifest['initial']}")

    if info["animations"]:
        out.append(f"\nAnimations ({len(info['animations'])}):")
        for anim_id, a in info["animations"].items():
            duration = ((a["op"] or 0) - (a["ip"] or 0)) / max(a["fr"] or 1, 1)
            out.append(f"  • {anim_id}: {a['w']}×{a['h']} @ {a['fr']}fps, "
                       f"{duration:.2f}s, {a['layers']} layers, {a['size']:,}B")
            if a["nm"] and a["nm"] != anim_id:
                out.append(f"      name: {a['nm']!r}")
            if a["slot_ids"]:
                out.append(f"      slot IDs: {', '.join(a['slot_ids'])}")
            if a["markers"]:
                out.append(f"      markers: {', '.join(str(m) for m in a['markers'] if m)}")

    if info["themes"]:
        out.append(f"\nThemes ({len(info['themes'])}):")
        for theme_id, t in info["themes"].items():
            types = ", ".join(f"{k}×{v}" for k, v in t["rule_types"].items())
            out.append(f"  • {theme_id}: {t['rules']} rules ({types})")
            if t["targeted_slots"]:
                out.append(f"      targets: {', '.join(t['targeted_slots'])}")

    if info["stateMachines"]:
        out.append(f"\nState Machines ({len(info['stateMachines'])}):")
        for sm_id, s in info["stateMachines"].items():
            out.append(f"  • {sm_id}: initial={s['initial']!r}, "
                       f"{len(s['states'])} states, {s['interactions']} interactions, "
                       f"{len(s['inputs'])} inputs")
            for state in s["states"]:
                anim_str = f" → {state['animation']}" if state.get("animation") else ""
                out.append(f"      [{state['type']}] {state['name']}"
                           f"{anim_str} ({state['transitions']} transitions)")
            if s["inputs"]:
                inps = ", ".join(f"{i['name']}:{i['type']}" for i in s["inputs"])
                out.append(f"      inputs: {inps}")

    if info["images"]:
        out.append(f"\nImages ({len(info['images'])}):")
        for img in info["images"]:
            out.append(f"  • {img['file']} ({img['size']:,}B)")
    if info["fonts"]:
        out.append(f"\nFonts ({len(info['fonts'])}):")
        for f in info["fonts"]:
            out.append(f"  • {f['file']} ({f['size']:,}B)")
    if info["unknown_files"]:
        out.append(f"\nUnrecognized files (not in spec layout):")
        for u in info["unknown_files"]:
            out.append(f"  ? {u}")

    issues = cross_reference_issues(info)
    if issues:
        out.append(f"\nCross-reference issues:")
        for issue in issues:
            out.append(f"  ⚠ {issue}")
    else:
        out.append(f"\n✓ Manifest and contents are internally consistent.")

    return "\n".join(out)


def extract_file(archive_path: Path, target: str, output_dir: Path) -> Path:
    """Extract a single entry from the archive to output_dir."""
    with zipfile.ZipFile(archive_path) as zf:
        candidates = [n for n in zf.namelist() if Path(n).stem == target or n == target]
        if not candidates:
            raise FileNotFoundError(f"No file matching {target!r} in archive")
        if len(candidates) > 1:
            # Prefer the JSON file
            json_candidates = [c for c in candidates if c.endswith(".json")]
            candidates = json_candidates or candidates[:1]
        name = candidates[0]
        output_dir.mkdir(parents=True, exist_ok=True)
        target_path = output_dir / Path(name).name
        with zf.open(name) as src, open(target_path, "wb") as dst:
            dst.write(src.read())
        return target_path


def main() -> int:
    p = argparse.ArgumentParser(description="Inspect a dotLottie v2.0 archive.")
    p.add_argument("file", help=".lottie file to inspect")
    p.add_argument("--json", action="store_true", help="Output as JSON instead of human-readable")
    p.add_argument("--slots", action="store_true", help="Just list all slot IDs found in animations")
    p.add_argument("--extract", metavar="NAME", help="Extract a single file by stem to current dir")
    p.add_argument("--output-dir", default=".", help="Where to write extracted files")
    args = p.parse_args()

    archive_path = Path(args.file)
    if not archive_path.exists():
        print(f"Error: {archive_path} does not exist", file=sys.stderr)
        return 1

    if args.extract:
        try:
            out_path = extract_file(archive_path, args.extract, Path(args.output_dir))
            print(f"Extracted: {out_path}")
            return 0
        except (FileNotFoundError, KeyError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    info = inspect_archive(archive_path)

    if args.slots:
        all_slots: set[str] = set()
        for a in info["animations"].values():
            all_slots.update(a["slot_ids"])
        for slot in sorted(all_slots):
            print(slot)
        return 0

    if args.json:
        print(json.dumps(info, indent=2, default=str))
    else:
        print(format_human(info))

    issues = info.get("issues", []) + cross_reference_issues(info)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
