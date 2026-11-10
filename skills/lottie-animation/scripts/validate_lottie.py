#!/usr/bin/env python3
"""
validate_lottie.py — Structure + common-pitfall validator for Lottie JSON.

Catches the issues that most often produce broken or low-fidelity output:
- Missing required top-level fields
- Layer transforms missing properties
- Tangent dimensions not matching value dimensions (silent linear fallback)
- Scalar keyframes not wrapped in arrays
- Colors in 0-255 instead of 0-1
- Closed paths with duplicated first vertex
- Path morph keyframes with mismatched vertex counts
- Linear-only easing (warning, not error)
- Zero-duration tweens
- Layer ip >= op
- Missing group transform inside shape groups

Usage:
    python validate_lottie.py path/to/animation.json [--strict]

Exit codes:
    0 — pass (no errors, may have warnings)
    1 — structural errors found
    2 — warnings only (--strict turns these into errors)
"""

from __future__ import annotations
import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Issue:
    level: str  # 'error' | 'warning'
    path: str
    message: str


@dataclass
class Report:
    issues: list[Issue] = field(default_factory=list)

    def error(self, path: str, message: str):
        self.issues.append(Issue("error", path, message))

    def warn(self, path: str, message: str):
        self.issues.append(Issue("warning", path, message))

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "warning"]


# ---------- Top-level validation ----------

REQUIRED_TOP_LEVEL = ["v", "fr", "ip", "op", "w", "h", "assets", "layers"]


def validate_top_level(data: dict, report: Report) -> None:
    if not isinstance(data, dict):
        report.error("$", "Root must be a JSON object")
        return

    for field_name in REQUIRED_TOP_LEVEL:
        if field_name not in data:
            report.error("$", f"Missing required top-level field: '{field_name}'")

    if "fr" in data:
        fr = data["fr"]
        if not isinstance(fr, (int, float)) or fr <= 0:
            report.error("$.fr", f"Frame rate must be positive number, got {fr!r}")
        elif fr not in (24, 25, 30, 50, 60, 120):
            report.warn("$.fr", f"Unusual frame rate {fr}; common values are 24, 30, 60")

    if "ip" in data and "op" in data:
        ip, op = data["ip"], data["op"]
        if isinstance(ip, (int, float)) and isinstance(op, (int, float)):
            if op <= ip:
                report.error("$", f"Composition op ({op}) must be greater than ip ({ip})")
            if op - ip > 600 and data.get("fr", 60) >= 60:
                report.warn("$", f"Long animation ({op - ip} frames at {data.get('fr')} fps) — may be large file")

    if "w" in data and (not isinstance(data["w"], int) or data["w"] <= 0):
        report.error("$.w", f"Width must be positive integer, got {data['w']!r}")
    if "h" in data and (not isinstance(data["h"], int) or data["h"] <= 0):
        report.error("$.h", f"Height must be positive integer, got {data['h']!r}")

    if "v" in data and not isinstance(data["v"], str):
        report.warn("$.v", f"Version 'v' should be a string like '5.12.2'")


# ---------- Layer validation ----------

REQUIRED_LAYER_FIELDS = ["ind", "ty", "ks", "ip", "op"]
LAYER_TYPES = {0: "precomp", 1: "solid", 2: "image", 3: "null", 4: "shape", 5: "text"}


def validate_layers(data: dict, report: Report) -> None:
    layers = data.get("layers", [])
    if not isinstance(layers, list):
        report.error("$.layers", "Layers must be an array")
        return

    if not layers:
        report.warn("$.layers", "Animation has no layers")

    comp_op = data.get("op")
    seen_indices = set()

    for i, layer in enumerate(layers):
        path = f"$.layers[{i}]"
        if not isinstance(layer, dict):
            report.error(path, "Layer must be an object")
            continue

        for f in REQUIRED_LAYER_FIELDS:
            if f not in layer:
                report.error(path, f"Layer missing required field '{f}'")

        ind = layer.get("ind")
        if ind is not None:
            if ind in seen_indices:
                report.error(path, f"Duplicate layer ind: {ind}")
            seen_indices.add(ind)

        ty = layer.get("ty")
        if ty is not None and ty not in LAYER_TYPES:
            report.warn(path, f"Unknown layer type {ty}")

        ip, op = layer.get("ip"), layer.get("op")
        if isinstance(ip, (int, float)) and isinstance(op, (int, float)):
            if op <= ip:
                report.error(path, f"Layer op ({op}) must be > ip ({ip})")
            if comp_op is not None and op < comp_op:
                report.warn(
                    path,
                    f"Layer '{layer.get('nm', '?')}' ends at frame {op} but composition runs to {comp_op} — layer will disappear mid-animation",
                )

        # Validate transform
        if "ks" in layer:
            validate_transform(layer["ks"], f"{path}.ks", report)

        # Validate shapes for shape layers
        if ty == 4 and "shapes" in layer:
            validate_shapes(layer["shapes"], f"{path}.shapes", report)


# ---------- Transform validation ----------

REQUIRED_TRANSFORM_PROPS = ["o", "r", "p", "a", "s"]


def validate_transform(ks: dict, path: str, report: Report) -> None:
    if not isinstance(ks, dict):
        report.error(path, "Transform must be an object")
        return

    for prop in REQUIRED_TRANSFORM_PROPS:
        if prop not in ks:
            report.error(path, f"Transform missing required property '{prop}'")
            continue
        validate_property(ks[prop], f"{path}.{prop}", report, expected_dim_hint=_dim_hint_for(prop))


def _dim_hint_for(prop: str) -> int | None:
    """Expected dimensionality for known transform properties."""
    return {"o": 1, "r": 1, "p": 3, "a": 3, "s": 3}.get(prop)


# ---------- Property validation ----------

def validate_property(prop: dict, path: str, report: Report, expected_dim_hint: int | None = None) -> None:
    if not isinstance(prop, dict):
        report.error(path, f"Property must be an object, got {type(prop).__name__}")
        return

    if "a" not in prop:
        report.error(path, "Property missing 'a' field (animated flag)")
        return
    if "k" not in prop:
        report.error(path, "Property missing 'k' field (value or keyframes)")
        return

    a = prop["a"]
    k = prop["k"]

    if a == 0:
        # Static value — just sanity check it's a sensible type
        if expected_dim_hint == 1:
            if not isinstance(k, (int, float)):
                report.warn(path, f"Scalar property '{path}' has non-scalar static value: {k!r}")
        elif expected_dim_hint is not None:
            if not isinstance(k, list):
                report.warn(path, f"Multi-dim property has non-list value: {k!r}")
        # Note: color sanity checks live in validate_shapes() where we know the
        # property is actually a color — checking here would false-positive on
        # positions like [100, 100, 0].
    elif a == 1:
        # Animated — keyframes array
        if not isinstance(k, list):
            report.error(path, "Animated property 'k' must be an array of keyframes")
            return
        validate_keyframes(k, path, report, expected_dim_hint)
    else:
        report.error(path, f"Property 'a' must be 0 or 1, got {a!r}")


def validate_keyframes(keyframes: list, path: str, report: Report, expected_dim_hint: int | None = None) -> None:
    if len(keyframes) < 1:
        report.error(path, "Keyframes array is empty")
        return

    last_time = None
    has_any_easing = False
    value_dim = None

    for i, kf in enumerate(keyframes):
        kf_path = f"{path}.k[{i}]"
        if not isinstance(kf, dict):
            report.error(kf_path, "Keyframe must be an object")
            continue

        # Time ordering
        if "t" not in kf:
            report.error(kf_path, "Keyframe missing 't' (time)")
            continue
        t = kf["t"]
        if last_time is not None and t <= last_time:
            report.error(kf_path, f"Keyframe time {t} not greater than previous {last_time}")
        last_time = t

        # Value (`s`) must always be an array
        if "s" not in kf:
            # Some older formats use `e` only for the last keyframe pair — accept but warn
            report.warn(kf_path, "Keyframe missing 's' (start value) — uncommon in modern Lottie")
        else:
            s = kf["s"]
            if not isinstance(s, list):
                report.error(
                    kf_path + ".s",
                    f"Keyframe value 's' must be an array, even for scalar values. Got {s!r} — wrap as [{s}].",
                )
            else:
                if value_dim is None:
                    value_dim = len(s)
                elif len(s) != value_dim:
                    # Path data has dict values; skip dim check for those
                    if not (isinstance(s, list) and s and isinstance(s[0], dict)):
                        report.error(
                            kf_path + ".s",
                            f"Keyframe value dimension {len(s)} doesn't match previous keyframes ({value_dim})",
                        )

        # Easing tangent dimension check
        # Only check non-final keyframes (last keyframe doesn't need outgoing tangents)
        is_last = (i == len(keyframes) - 1)
        if not is_last and value_dim is not None:
            for tangent_key in ("o", "i"):
                if tangent_key not in kf:
                    if tangent_key == "o" and not kf.get("h"):
                        # Missing outgoing tangent on non-final keyframe → silent linear
                        pass  # not an error per se, just won't ease
                    continue
                tangent = kf[tangent_key]
                if not isinstance(tangent, dict):
                    report.error(kf_path + f".{tangent_key}", "Tangent must be an object")
                    continue
                for axis in ("x", "y"):
                    if axis not in tangent:
                        report.error(kf_path + f".{tangent_key}", f"Tangent missing '{axis}'")
                        continue
                    arr = tangent[axis]
                    # Tangents can be scalars (older format) or arrays (modern)
                    if isinstance(arr, (int, float)):
                        # Scalar tangent format — implicitly broadcast. Mark as OK.
                        continue
                    if not isinstance(arr, list):
                        report.error(
                            kf_path + f".{tangent_key}.{axis}",
                            f"Tangent axis must be array or scalar, got {arr!r}",
                        )
                        continue
                    # Don't check tangent dim against path-data values
                    skip_dim_check = (
                        "s" in kf
                        and isinstance(kf["s"], list)
                        and kf["s"]
                        and isinstance(kf["s"][0], dict)
                    )
                    if not skip_dim_check and len(arr) != value_dim:
                        report.error(
                            kf_path + f".{tangent_key}.{axis}",
                            f"Tangent dimension {len(arr)} doesn't match value dimension {value_dim} — will fall back to LINEAR",
                        )

        # Detect non-linear easing for the "all linear" warning
        if not is_last:
            o = kf.get("o", {})
            if isinstance(o, dict):
                ox = o.get("x")
                if isinstance(ox, list) and ox and ox[0] not in (0, 1):
                    has_any_easing = True
                elif isinstance(ox, (int, float)) and ox not in (0, 1):
                    has_any_easing = True

    if not is_last:  # noqa — variable from loop
        pass

    if len(keyframes) >= 2 and not has_any_easing:
        # All linear or no tangents
        report.warn(path, "Property has no non-linear easing — motion will look mechanical (see references/easing.md)")


# ---------- Shape validation ----------

VALID_SHAPE_TYPES = {"gr", "rc", "el", "sr", "sh", "fl", "st", "gf", "gs", "tr", "tm", "rp", "rd", "mm"}


def validate_shapes(shapes: list, path: str, report: Report) -> None:
    if not isinstance(shapes, list):
        report.error(path, "shapes must be an array")
        return

    for i, item in enumerate(shapes):
        item_path = f"{path}[{i}]"
        if not isinstance(item, dict):
            report.error(item_path, "Shape item must be an object")
            continue

        ty = item.get("ty")
        if ty not in VALID_SHAPE_TYPES:
            report.warn(item_path, f"Unknown shape type '{ty}'")
            continue

        if ty == "gr":
            # Group — recurse into items
            it = item.get("it", [])
            validate_shapes(it, f"{item_path}.it", report)
            # Last item should be 'tr' (group transform)
            if it and it[-1].get("ty") != "tr":
                report.error(
                    item_path,
                    "Shape group's last item must be 'tr' (group transform). Without it, the renderer may misposition the group.",
                )
        elif ty == "sh":
            # Path
            validate_path_shape(item, item_path, report)
        elif ty == "fl":
            # Fill color check
            c = item.get("c", {})
            if isinstance(c, dict) and c.get("a") == 0:
                k = c.get("k", [])
                if isinstance(k, list) and any(isinstance(v, (int, float)) and v > 1.5 for v in k):
                    report.warn(item_path + ".c.k", f"Color {k!r} appears to be 0-255 range; Lottie uses 0-1 floats")
        elif ty == "st":
            # Stroke color
            c = item.get("c", {})
            if isinstance(c, dict) and c.get("a") == 0:
                k = c.get("k", [])
                if isinstance(k, list) and any(isinstance(v, (int, float)) and v > 1.5 for v in k):
                    report.warn(item_path + ".c.k", f"Stroke color {k!r} appears to be 0-255 range")


def validate_path_shape(shape: dict, path: str, report: Report) -> None:
    ks = shape.get("ks")
    if not isinstance(ks, dict):
        report.error(path + ".ks", "Path shape missing 'ks' field")
        return

    a = ks.get("a")
    k = ks.get("k")

    if a == 0:
        validate_path_data(k, path + ".ks.k", report)
    elif a == 1:
        # Animated path — each keyframe's `s` should be [path_data_obj]
        if not isinstance(k, list):
            report.error(path + ".ks.k", "Animated path keyframes must be array")
            return
        vertex_counts = []
        for i, kf in enumerate(k):
            kf_path = f"{path}.ks.k[{i}]"
            s = kf.get("s")
            if not isinstance(s, list) or not s:
                report.error(kf_path + ".s", "Path keyframe 's' should be [path_data_object]")
                continue
            path_obj = s[0]
            validate_path_data(path_obj, kf_path + ".s[0]", report)
            if isinstance(path_obj, dict) and "v" in path_obj:
                vertex_counts.append(len(path_obj["v"]))
        if len(set(vertex_counts)) > 1:
            report.error(
                path,
                f"Path morph keyframes have differing vertex counts: {vertex_counts}. All keyframes must have the same number of vertices.",
            )


def validate_path_data(path_obj: Any, path: str, report: Report) -> None:
    if not isinstance(path_obj, dict):
        report.error(path, f"Path data must be an object, got {type(path_obj).__name__}")
        return

    v = path_obj.get("v", [])
    i_arr = path_obj.get("i", [])
    o_arr = path_obj.get("o", [])

    if not isinstance(v, list):
        report.error(path + ".v", "Path vertices 'v' must be an array")
        return

    n = len(v)
    if not isinstance(i_arr, list) or len(i_arr) != n:
        report.error(path, f"Path in-tangents 'i' length ({len(i_arr) if isinstance(i_arr, list) else '?'}) must match vertex count ({n})")
    if not isinstance(o_arr, list) or len(o_arr) != n:
        report.error(path, f"Path out-tangents 'o' length ({len(o_arr) if isinstance(o_arr, list) else '?'}) must match vertex count ({n})")

    if path_obj.get("c") is True and n >= 2:
        # Check if last vertex is suspiciously close to first (common mistake)
        first, last = v[0], v[-1]
        if isinstance(first, list) and isinstance(last, list) and len(first) == len(last) == 2:
            if abs(first[0] - last[0]) < 0.01 and abs(first[1] - last[1]) < 0.01:
                report.warn(
                    path,
                    "Closed path 'c: true' has duplicate first/last vertex — this creates a glitchy seam. Remove the last vertex; the renderer auto-closes.",
                )


# ---------- CLI ----------

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Lottie JSON file.")
    parser.add_argument("file", help="Path to Lottie JSON file")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--json", action="store_true", help="Output report as JSON")
    args = parser.parse_args()

    try:
        with open(args.file) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON: {e}", file=sys.stderr)
        return 1

    report = Report()
    validate_top_level(data, report)
    validate_layers(data, report)

    if args.json:
        out = {
            "errors": [{"path": i.path, "message": i.message} for i in report.errors],
            "warnings": [{"path": i.path, "message": i.message} for i in report.warnings],
        }
        print(json.dumps(out, indent=2))
    else:
        n_err, n_warn = len(report.errors), len(report.warnings)
        if n_err == 0 and n_warn == 0:
            print(f"✓ {args.file}: validation passed, no issues found")
        else:
            for issue in report.issues:
                marker = "✗" if issue.level == "error" else "⚠"
                print(f"  {marker} [{issue.level}] {issue.path}")
                print(f"      {issue.message}")
            print(f"\nSummary: {n_err} error(s), {n_warn} warning(s)")

    if report.errors:
        return 1
    if report.warnings and args.strict:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
