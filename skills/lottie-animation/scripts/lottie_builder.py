"""
lottie_builder.py — Programmatic helpers for building well-formed Lottie JSON.

Designed for hand-authoring complex animations where loops, stagger, or many
similar layers make hand-written JSON error-prone. Produces clean, validated
Lottie 5.x output.

Usage:
    from lottie_builder import (
        Animation, ShapeLayer, ellipse, rect, star, path, fill, stroke,
        group_transform, keyframes, ease, EASE, hex_to_rgba,
    )

    anim = Animation(width=512, height=512, fps=60, duration_frames=60)
    layer = ShapeLayer(
        name="dot",
        shapes=[
            ellipse(size=[60, 60]),
            fill(color=hex_to_rgba("#F250D8")),
            group_transform(
                position=[256, 256],
                scale=keyframes([
                    (0,  [80, 80],   EASE.OUT_CUBIC),
                    (30, [110, 110], EASE.OUT_CUBIC),
                    (60, [80, 80]),
                ]),
            ),
        ],
    )
    anim.add_layer(layer)
    anim.save("output.json")

Design notes:
- All keyframe scalar values are auto-wrapped in single-element arrays
  (Lottie requires this; the most common hand-authoring mistake is forgetting).
- Tangent dimensions auto-match value dimensions.
- Group transforms always include all five properties (o, r, p, a, s) with
  sensible defaults, so partially-specified transforms still produce valid Lottie.
- The library doesn't attempt to model every Lottie feature — it covers the
  90% case (shape layers, common shapes, common animations). For exotic
  features, hand-edit the JSON after building.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any, Optional


# ---------- Easing presets ----------

class EASE:
    """Ready-to-use easing tangent dicts. Use with the `keyframes()` helper.

    Format: (out_x, out_y, in_x, in_y) — meaning
      this keyframe's `o` = {x: [out_x], y: [out_y]}
      next keyframe's `i` = {x: [in_x],  y: [in_y]}
    """
    LINEAR        = (1.0,   1.0,   0.0,   0.0)
    OUT_CUBIC     = (0.215, 0.61,  0.355, 1.0)
    IN_CUBIC      = (0.55,  0.055, 0.675, 0.19)
    IN_OUT_CUBIC  = (0.645, 0.045, 0.355, 1.0)
    OUT_QUART     = (0.165, 0.84,  0.44,  1.0)
    OUT_EXPO      = (0.19,  1.0,   0.22,  1.0)
    OUT_BACK      = (0.175, 0.885, 0.32,  1.275)
    IN_BACK       = (0.6,  -0.28,  0.735, 0.045)
    IN_OUT_BACK   = (0.68, -0.55,  0.265, 1.55)
    MATERIAL_STD  = (0.4,   0.0,   0.2,   1.0)
    MATERIAL_DEC  = (0.0,   0.0,   0.2,   1.0)
    MATERIAL_ACC  = (0.4,   0.0,   1.0,   1.0)
    EASE_OUT      = (0.0,   0.0,   0.58,  1.0)
    EASE_IN       = (0.42,  0.0,   1.0,   1.0)
    EASE_IN_OUT   = (0.42,  0.0,   0.58,  1.0)


# Alias for ergonomic short form: ease.OUT_CUBIC, ease.IN_BACK, etc.
ease = EASE


# ---------- Color helpers ----------

def hex_to_rgba(hex_str: str, alpha: float = 1.0) -> list[float]:
    """Convert '#RRGGBB' or '#RRGGBBAA' to a Lottie color array [r, g, b, a]
    in 0-1 floats."""
    s = hex_str.lstrip("#")
    if len(s) == 6:
        r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
        return [round(r / 255, 4), round(g / 255, 4), round(b / 255, 4), alpha]
    if len(s) == 8:
        r, g, b, a = (int(s[0:2], 16), int(s[2:4], 16),
                      int(s[4:6], 16), int(s[6:8], 16))
        return [round(r / 255, 4), round(g / 255, 4),
                round(b / 255, 4), round(a / 255, 4)]
    raise ValueError(f"Invalid hex color: {hex_str}")


# ---------- Property builders ----------

def _as_array(value) -> list:
    """Ensure a value is a list (Lottie wraps even scalars in arrays for keyframes)."""
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def static(value) -> dict:
    """Build a static (non-animated) property.

    For scalar values (rotation, opacity), pass the raw number — it'll be stored
    as `k: <number>` (not array), per Lottie spec for static scalars.
    For vector values (position, scale, color), pass a list.
    """
    return {"a": 0, "k": value}


def keyframes(specs: list[tuple]) -> dict:
    """Build an animated property from a list of (time, value[, easing]) tuples.

    Each spec is one of:
      (time, value)                          — last keyframe (no outgoing easing)
      (time, value, easing_tuple)            — keyframe with easing to next

    `easing_tuple` is one of the EASE constants: (out_x, out_y, in_x, in_y).

    The value can be a scalar (for 1D properties like rotation, opacity) or a
    list (for ND properties like position, scale, color). Either way, the
    resulting keyframe's `s` will be an array (per Lottie spec).

    Tangent dimensions auto-match the value's dimension.
    """
    if len(specs) < 2:
        raise ValueError("keyframes() needs at least 2 entries")

    out_keyframes = []
    for i, spec in enumerate(specs):
        if len(spec) == 2:
            t, value = spec
            this_easing = None
        elif len(spec) == 3:
            t, value, this_easing = spec
        else:
            raise ValueError(f"Bad keyframe spec: {spec!r}")

        value_arr = _as_array(value)
        dim = len(value_arr)
        kf = {"t": t, "s": value_arr}

        if this_easing is not None and i < len(specs) - 1:
            ox, oy, _, _ = this_easing
            kf["o"] = {"x": [ox] * dim, "y": [oy] * dim}

        if i > 0:
            prev_spec = specs[i - 1]
            if len(prev_spec) == 3:
                _, _, prev_easing = prev_spec
                _, _, ix, iy = prev_easing
                kf["i"] = {"x": [ix] * dim, "y": [iy] * dim}
            else:
                # Previous keyframe had no easing — default to linear in-tangent
                kf["i"] = {"x": [0.0] * dim, "y": [0.0] * dim}

        out_keyframes.append(kf)

    return {"a": 1, "k": out_keyframes}


# ---------- Shape primitives ----------

def ellipse(size: list, position: list = None) -> dict:
    """Ellipse shape primitive. `size` is [w, h]. `position` is local position
    within the group (usually [0, 0])."""
    return {
        "ty": "el",
        "d": 1,
        "s": static(size),
        "p": static(position or [0, 0]),
    }


def rect(size: list, position: list = None, corner_radius: float = 0) -> dict:
    """Rectangle primitive. `size` is [w, h]. `corner_radius` for rounded
    corners."""
    return {
        "ty": "rc",
        "d": 1,
        "s": static(size),
        "p": static(position or [0, 0]),
        "r": static(corner_radius),
    }


def star(
    points: int,
    outer_radius: float,
    inner_radius: float = None,
    position: list = None,
    rotation: float = 0,
    polygon: bool = False,
) -> dict:
    """Star or polygon primitive. Set `polygon=True` for a regular polygon
    (no inner radius)."""
    return {
        "ty": "sr",
        "sy": 2 if polygon else 1,
        "pt": static(points),
        "p": static(position or [0, 0]),
        "r": static(rotation),
        "or": static(outer_radius),
        "ir": static(inner_radius if inner_radius is not None else outer_radius * 0.5),
        "os": static(0),
        "is": static(0),
    }


def path(
    vertices: list[list[float]],
    closed: bool = True,
    in_tangents: list[list[float]] = None,
    out_tangents: list[list[float]] = None,
) -> dict:
    """Custom path primitive.

    `vertices`: list of [x, y] points.
    `closed`: whether to close the path (last point connects to first).
    `in_tangents` / `out_tangents`: Bézier handles relative to each vertex.
        If omitted, defaults to zero tangents (straight lines).
    """
    n = len(vertices)
    in_t = in_tangents if in_tangents is not None else [[0, 0]] * n
    out_t = out_tangents if out_tangents is not None else [[0, 0]] * n
    return {
        "ty": "sh",
        "ks": {
            "a": 0,
            "k": {
                "c": closed,
                "v": vertices,
                "i": in_t,
                "o": out_t,
            },
        },
    }


def fill(color: list, opacity: float = 100) -> dict:
    """Solid fill. `color` is [r, g, b, a] in 0-1 floats — use `hex_to_rgba()`
    to convert from hex."""
    return {
        "ty": "fl",
        "c": static(color),
        "o": static(opacity),
        "r": 1,
    }


def stroke(
    color: list,
    width: float,
    opacity: float = 100,
    line_cap: int = 2,
    line_join: int = 2,
) -> dict:
    """Stroke. `line_cap`/`line_join`: 1=butt/miter, 2=round, 3=square/bevel."""
    return {
        "ty": "st",
        "c": static(color),
        "o": static(opacity),
        "w": static(width),
        "lc": line_cap,
        "lj": line_join,
        "ml": 4,
        "d": [],
    }


def trim_path(
    start=0,
    end=100,
    offset=0,
    mode: int = 1,
) -> dict:
    """Trim path effect. `start`/`end` can be static values (0-100 percent)
    or `keyframes()` results to animate."""
    s = start if isinstance(start, dict) else static(start)
    e = end if isinstance(end, dict) else static(end)
    o = offset if isinstance(offset, dict) else static(offset)
    return {
        "ty": "tm",
        "s": s,
        "e": e,
        "o": o,
        "m": mode,
    }


def group_transform(
    position=None,
    anchor=None,
    scale=None,
    rotation=None,
    opacity=None,
) -> dict:
    """Group transform — always the LAST item in a shape group's `it` array.

    Each argument can be a static value (list or scalar) or a `keyframes()`
    result. Defaults produce an identity transform."""
    def _prop(value, default_static):
        if value is None:
            return static(default_static)
        if isinstance(value, dict):  # already a keyframes() or static() result
            return value
        return static(value)

    return {
        "ty": "tr",
        "p": _prop(position, [0, 0]),
        "a": _prop(anchor, [0, 0]),
        "s": _prop(scale, [100, 100]),
        "r": _prop(rotation, 0),
        "o": _prop(opacity, 100),
        "sk": static(0),
        "sa": static(0),
    }


def group(name: str, items: list[dict]) -> dict:
    """Wrap a list of shape items in a group. The last item should be a
    `group_transform()` — but if it's missing, an identity transform is added."""
    has_transform = items and items[-1].get("ty") == "tr"
    if not has_transform:
        items = list(items) + [group_transform()]
    return {
        "ty": "gr",
        "nm": name,
        "it": items,
    }


# ---------- Layer transform ----------

def layer_transform(
    position=None,
    anchor=None,
    scale=None,
    rotation=None,
    opacity=None,
) -> dict:
    """Build a layer-level transform (`ks` field). Always 3D-style (3-element
    arrays for position/anchor/scale) since Lottie internally treats layer
    transforms as 3D even when `ddd: 0`."""
    def _prop_3d(value, default_3d):
        if value is None:
            return static(default_3d)
        if isinstance(value, dict):
            return value
        if isinstance(value, (list, tuple)):
            arr = list(value)
            if len(arr) == 2:
                arr.append(0)
            return static(arr)
        return static(value)

    def _prop_scalar(value, default_scalar):
        if value is None:
            return static(default_scalar)
        if isinstance(value, dict):
            return value
        return static(value)

    return {
        "o": _prop_scalar(opacity, 100),
        "r": _prop_scalar(rotation, 0),
        "p": _prop_3d(position, [0, 0, 0]),
        "a": _prop_3d(anchor, [0, 0, 0]),
        "s": _prop_3d(scale, [100, 100, 100]),
    }


# ---------- Layer types ----------

@dataclass
class ShapeLayer:
    """A vector shape layer. Pass shape items in `shapes` (use `group()` to bundle
    related items, or pass primitives directly for a single shape)."""
    name: str
    shapes: list[dict]
    transform: dict = None
    in_point: int = 0
    out_point: Optional[int] = None  # If None, uses composition's op

    def to_dict(self, index: int, comp_op: int) -> dict:
        # Auto-wrap loose shape items in a group if they're not already grouped
        shapes_array = self.shapes
        if shapes_array and not all(s.get("ty") == "gr" for s in shapes_array):
            # Some items aren't groups — wrap them all in a single group
            has_any_group = any(s.get("ty") == "gr" for s in shapes_array)
            if not has_any_group:
                shapes_array = [group(self.name + "_g", list(shapes_array))]

        return {
            "ddd": 0,
            "ind": index,
            "ty": 4,
            "nm": self.name,
            "sr": 1,
            "ks": self.transform or layer_transform(),
            "ao": 0,
            "shapes": shapes_array,
            "ip": self.in_point,
            "op": self.out_point if self.out_point is not None else comp_op,
            "st": 0,
            "bm": 0,
        }


@dataclass
class NullLayer:
    """A transform-only layer for use as a parent."""
    name: str
    transform: dict = None
    in_point: int = 0
    out_point: Optional[int] = None

    def to_dict(self, index: int, comp_op: int) -> dict:
        return {
            "ddd": 0,
            "ind": index,
            "ty": 3,
            "nm": self.name,
            "sr": 1,
            "ks": self.transform or layer_transform(),
            "ao": 0,
            "ip": self.in_point,
            "op": self.out_point if self.out_point is not None else comp_op,
            "st": 0,
            "bm": 0,
        }


@dataclass
class SolidLayer:
    """A solid-color rectangle filling the layer's bounds."""
    name: str
    width: int
    height: int
    color: str  # hex string
    transform: dict = None
    in_point: int = 0
    out_point: Optional[int] = None

    def to_dict(self, index: int, comp_op: int) -> dict:
        return {
            "ddd": 0,
            "ind": index,
            "ty": 1,
            "nm": self.name,
            "sr": 1,
            "ks": self.transform or layer_transform(),
            "ao": 0,
            "sw": self.width,
            "sh": self.height,
            "sc": self.color,
            "ip": self.in_point,
            "op": self.out_point if self.out_point is not None else comp_op,
            "st": 0,
            "bm": 0,
        }


# ---------- Animation container ----------

@dataclass
class Animation:
    width: int
    height: int
    fps: int = 60
    duration_frames: int = 60
    name: str = "Animation"
    version: str = "5.12.2"
    _layers: list = field(default_factory=list)

    def add_layer(self, layer):
        self._layers.append(layer)

    def to_dict(self) -> dict:
        layer_dicts = []
        for i, layer in enumerate(self._layers):
            layer_dicts.append(layer.to_dict(index=i + 1, comp_op=self.duration_frames))

        return {
            "v": self.version,
            "fr": self.fps,
            "ip": 0,
            "op": self.duration_frames,
            "w": self.width,
            "h": self.height,
            "nm": self.name,
            "ddd": 0,
            "assets": [],
            "layers": layer_dicts,
            "markers": [],
        }

    def save(self, path: str, indent: Optional[int] = None) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=indent)

    def to_json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# ---------- Quick self-test when run directly ----------

if __name__ == "__main__":
    # Smoke test: build a pulsing dot and dump JSON to stdout
    anim = Animation(width=200, height=200, fps=60, duration_frames=60,
                     name="Pulsing Dot")

    dot = ShapeLayer(
        name="Dot",
        transform=layer_transform(
            position=[100, 100],
            opacity=keyframes([
                (0,  60,  EASE.IN_OUT_CUBIC),
                (30, 100, EASE.IN_OUT_CUBIC),
                (60, 60),
            ]),
            scale=keyframes([
                (0,  [80, 80, 100],   EASE.IN_OUT_CUBIC),
                (30, [110, 110, 100], EASE.IN_OUT_CUBIC),
                (60, [80, 80, 100]),
            ]),
        ),
        shapes=[
            group("Dot Group", [
                ellipse(size=[60, 60]),
                fill(color=hex_to_rgba("#F250D8")),
                group_transform(),
            ])
        ],
    )
    anim.add_layer(dot)

    print(anim.to_json(indent=2))
