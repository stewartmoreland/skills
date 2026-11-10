# Lottie JSON Schema Reference

A field-by-field cheatsheet for valid Lottie. Covers the top-level structure, layer types, shape primitives, and property formats. For easing tangents, see [`easing.md`](easing.md).

## Table of contents

1. [Top-level structure](#top-level-structure)
2. [Layer common fields](#layer-common-fields)
3. [Layer types](#layer-types)
4. [Transform (`ks`) object](#transform-ks-object)
5. [Animated property format](#animated-property-format)
6. [Shape primitives](#shape-primitives)
7. [Path data format](#path-data-format)
8. [Masks](#masks)
9. [Assets](#assets)

---

## Top-level structure

```json
{
  "v": "5.12.2",
  "fr": 60,
  "ip": 0,
  "op": 120,
  "w": 512,
  "h": 512,
  "nm": "Animation Name",
  "ddd": 0,
  "assets": [],
  "layers": [],
  "markers": []
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `v` | string | yes | Bodymovin spec version. Use `"5.12.2"` for current lottie-web. Older renderers may need `"5.7.4"`. |
| `fr` | number | yes | Frame rate (frames per second). Common: 24, 30, 60. |
| `ip` | number | yes | Composition in-point (start frame). Almost always 0. |
| `op` | number | yes | Composition out-point (end frame, exclusive). Duration in frames. |
| `w` | integer | yes | Canvas width in pixels. |
| `h` | integer | yes | Canvas height in pixels. |
| `nm` | string | no | Animation name (informational). |
| `ddd` | 0 or 1 | yes | 3D flag. Use 0 unless you actually need Z-axis. |
| `assets` | array | yes | Image assets and precomps. Can be empty `[]`. |
| `layers` | array | yes | Layer stack. **Rendered top-to-bottom** — index 0 is in front. |
| `markers` | array | no | Named time markers, useful for chaptered animations. |

## Layer common fields

Every layer has these:

| Field | Type | Notes |
|---|---|---|
| `ind` | integer | Unique layer index within composition. |
| `ty` | integer | Layer type (see below). |
| `nm` | string | Layer name. |
| `ks` | object | Transform (anchor, position, scale, rotation, opacity). See [Transform](#transform-ks-object). |
| `ip` | number | Layer in-point — frame at which layer appears. |
| `op` | number | Layer out-point — frame at which layer disappears. |
| `st` | number | Start time (frame offset for the layer's internal timeline). |
| `bm` | integer | Blend mode (0 = normal, 1 = multiply, 2 = screen, 3 = overlay, …). |
| `ao` | 0 or 1 | Auto-orient on path. |
| `ddd` | 0 or 1 | 3D layer flag. |

**`ip`/`op` gotcha**: layer `ip`/`op` are within the *composition's* frame range. A composition with `op: 120` and a layer with `op: 60` means that layer disappears at the halfway mark. Unless you want that, match composition `op`.

## Layer types

| `ty` | Type | Use for |
|---|---|---|
| 0 | Precomp | Nested composition (asset referenced by `refId`). |
| 1 | Solid | Solid-color rectangle filling layer bounds. |
| 2 | Image | Bitmap asset. |
| 3 | Null | Transform-only layer (parenting target). |
| 4 | Shape | Vector shapes — the workhorse type for icon/UI animation. |
| 5 | Text | Animated text (limited cross-platform support; see [platforms.md](platforms.md)). |

### Shape layer (`ty: 4`)

Adds a `shapes` array of shape items:

```json
{
  "ddd": 0, "ind": 1, "ty": 4, "nm": "Circle",
  "sr": 1,
  "ks": { /* transform */ },
  "ao": 0,
  "shapes": [ /* shape items */ ],
  "ip": 0, "op": 120, "st": 0, "bm": 0
}
```

### Solid layer (`ty: 1`)

```json
{
  "ddd": 0, "ind": 1, "ty": 1, "nm": "Background",
  "sr": 1, "ks": { /* transform */ },
  "ao": 0,
  "sw": 512, "sh": 512,
  "sc": "#0a0a14",
  "ip": 0, "op": 120, "st": 0, "bm": 0
}
```

`sw`/`sh` are solid dimensions. `sc` is the solid color as a **hex string** (note: solids use hex, shape fills use 0–1 RGBA arrays — inconsistent but that's the spec).

### Null layer (`ty: 3`)

No visual output. Useful as a parent for other layers — animate the null's transform and child layers inherit it. Set `parent: <ind of null>` on child layers.

## Transform (`ks`) object

Every layer has a transform. Every shape group also has its own transform (`tr` item) that nests inside.

```json
"ks": {
  "o": { "a": 0, "k": 100 },
  "r": { "a": 0, "k": 0 },
  "p": { "a": 0, "k": [256, 256, 0] },
  "a": { "a": 0, "k": [0, 0, 0] },
  "s": { "a": 0, "k": [100, 100, 100] }
}
```

| Field | Meaning | Units | Dimensions |
|---|---|---|---|
| `o` | Opacity | 0–100 (percent) | 1 |
| `r` | Rotation | degrees (clockwise) | 1 |
| `p` | Position | pixels, top-left origin | 2 or 3 (2D/3D) |
| `a` | Anchor | pixels, layer-local | 2 or 3 |
| `s` | Scale | percent (100 = 100%) | 2 or 3 |
| `sk` | Skew | degrees | 1 (optional) |
| `sa` | Skew axis | degrees | 1 (optional) |
| `px`/`py`/`pz` | Split position components | pixels | 1 each (alternative to `p`) |

Note that scale is **percent** (100 = original size), not a multiplier (1.0). Forgetting this and writing `[1, 1]` makes things tiny.

## Animated property format

Every transform property and most shape properties follow this shape:

### Static (not animated):

```json
{ "a": 0, "k": value_or_array }
```

The `k` is the value directly — scalar for 1D properties (`o: {"a": 0, "k": 100}`), array for multi-D (`p: {"a": 0, "k": [256, 256, 0]}`).

### Animated:

```json
{
  "a": 1,
  "k": [
    {
      "t": 0,
      "s": [0],
      "o": { "x": [0.16], "y": [1] },
      "i": { "x": [0], "y": [0] }
    },
    {
      "t": 30,
      "s": [100],
      "o": { "x": [0], "y": [0] },
      "i": { "x": [0.3], "y": [1] }
    }
  ]
}
```

**Critical rules:**
- `s` (start value) is **always an array**, even for scalar properties. Rotation animated from 0° → 360° has keyframes with `s: [0]` and `s: [360]`, not `s: 0` and `s: 360`.
- Keyframes are listed in chronological order (ascending `t`).
- Tangent arrays (`o.x`, `o.y`, `i.x`, `i.y`) must match the dimensionality of `s`. 2D position → 2-element tangent arrays.
- Last keyframe doesn't need `o` (no segment leaves it), first doesn't need `i` (no segment arrives at it) — but most exporters include both, with the unused side as `{"x": [0], "y": [0]}`.
- Older Lottie files use `e` (end value) alongside `s`. This is deprecated — modern format uses `s` only, with the next keyframe's `s` as the implicit end. The validator accepts both.

### Hold keyframe (no interpolation):

```json
{ "t": 30, "s": [100], "h": 1 }
```

Value snaps from previous to this on frame `t`, no tween.

## Shape primitives

Inside a shape layer's `shapes` array, items are either **shape primitives** (which contribute geometry/styling) or **groups** (`ty: "gr"`) that bundle items together with their own transform.

| `ty` | Name | Purpose |
|---|---|---|
| `"gr"` | Group | Bundle items with shared transform. Has `it` (items array). |
| `"rc"` | Rectangle | Box with rounded corners. |
| `"el"` | Ellipse | Oval/circle. |
| `"sr"` | Star | Star or polygon. |
| `"sh"` | Path | Custom Bézier path. |
| `"fl"` | Fill | Solid fill applied to preceding shapes in group. |
| `"st"` | Stroke | Line stroke applied to preceding shapes. |
| `"gf"` | Gradient fill | Linear or radial gradient fill. |
| `"gs"` | Gradient stroke | Gradient stroke. |
| `"tr"` | Transform | Group transform (always last item in a group). |
| `"tm"` | Trim path | Trim/draw-on effect. |
| `"rp"` | Repeater | Duplicate with offset (radial menus, particle effects). |
| `"rd"` | Round corners | Round the corners of preceding shapes. |
| `"mm"` | Merge paths | Boolean ops on shapes (union, intersect, etc.). |

### Group structure

```json
{
  "ty": "gr",
  "nm": "Dot",
  "it": [
    { "ty": "el", "p": { "a": 0, "k": [0, 0] }, "s": { "a": 0, "k": [40, 40] } },
    { "ty": "fl", "c": { "a": 0, "k": [1, 0.42, 0.84, 1] }, "o": { "a": 0, "k": 100 } },
    { "ty": "tr",
      "p": { "a": 0, "k": [256, 256] },
      "a": { "a": 0, "k": [0, 0] },
      "s": { "a": 0, "k": [100, 100] },
      "r": { "a": 0, "k": 0 },
      "o": { "a": 0, "k": 100 }
    }
  ]
}
```

Pattern: **geometry first, styling next, transform last**. The transform applies to everything above it in the group.

### Rectangle

```json
{
  "ty": "rc",
  "d": 1,
  "s": { "a": 0, "k": [100, 80] },
  "p": { "a": 0, "k": [0, 0] },
  "r": { "a": 0, "k": 12 }
}
```

| Field | Meaning |
|---|---|
| `s` | Size (width, height) |
| `p` | Center position |
| `r` | Corner radius |
| `d` | Direction (1 = clockwise) |

### Ellipse

```json
{
  "ty": "el",
  "d": 1,
  "s": { "a": 0, "k": [80, 80] },
  "p": { "a": 0, "k": [0, 0] }
}
```

`s` is (width, height). For a circle, both equal.

### Star / polygon

```json
{
  "ty": "sr",
  "sy": 1,
  "pt": { "a": 0, "k": 5 },
  "p": { "a": 0, "k": [0, 0] },
  "r": { "a": 0, "k": 0 },
  "or": { "a": 0, "k": 50 },
  "ir": { "a": 0, "k": 25 },
  "os": { "a": 0, "k": 0 },
  "is": { "a": 0, "k": 0 }
}
```

| Field | Meaning |
|---|---|
| `sy` | Star type: 1 = star, 2 = polygon. |
| `pt` | Number of points. |
| `or` | Outer radius. |
| `ir` | Inner radius (star only). |
| `os` / `is` | Outer/inner roundness (0 = sharp). |
| `r` | Rotation of the star. |

### Fill

```json
{
  "ty": "fl",
  "c": { "a": 0, "k": [1, 0.42, 0.84, 1] },
  "o": { "a": 0, "k": 100 },
  "r": 1
}
```

`c` is RGBA in **0–1 floats**. `o` is opacity 0–100. `r` is fill rule (1 = non-zero, 2 = even-odd).

### Stroke

```json
{
  "ty": "st",
  "c": { "a": 0, "k": [0, 1, 1, 1] },
  "o": { "a": 0, "k": 100 },
  "w": { "a": 0, "k": 4 },
  "lc": 2,
  "lj": 2,
  "ml": 4,
  "d": []
}
```

| Field | Meaning |
|---|---|
| `c` | Color (RGBA 0–1). |
| `o` | Opacity (0–100). |
| `w` | Width in pixels. |
| `lc` | Line cap (1 = butt, 2 = round, 3 = square). |
| `lj` | Line join (1 = miter, 2 = round, 3 = bevel). |
| `ml` | Miter limit. |
| `d` | Dash array, e.g., `[{"n": "d", "v": {"a": 0, "k": 10}}, {"n": "g", "v": {"a": 0, "k": 5}}]` for 10-on/5-off dashes. |

### Trim path

```json
{
  "ty": "tm",
  "s": { "a": 1, "k": [...keyframes...] },
  "e": { "a": 0, "k": 100 },
  "o": { "a": 0, "k": 0 },
  "m": 1
}
```

Trims the preceding path(s) by a start/end percentage. Animate `s` from 100→0 or `e` from 0→100 for a "draw on" effect.

| Field | Meaning |
|---|---|
| `s` | Trim start (0–100 percent). |
| `e` | Trim end (0–100 percent). |
| `o` | Trim offset (rotates the trim range around the path). |
| `m` | Mode (1 = trim all paths in group as one, 2 = trim individually). |

### Repeater

```json
{
  "ty": "rp",
  "c": { "a": 0, "k": 6 },
  "o": { "a": 0, "k": 0 },
  "m": 1,
  "tr": {
    "p": { "a": 0, "k": [50, 0] },
    "a": { "a": 0, "k": [0, 0] },
    "s": { "a": 0, "k": [100, 100] },
    "r": { "a": 0, "k": 60 },
    "so": { "a": 0, "k": 100 },
    "eo": { "a": 0, "k": 100 }
  }
}
```

Duplicates preceding shapes `c` times, applying `tr` per copy cumulatively. `r: 60` with 6 copies gives a full circular arrangement.

## Path data format

Custom paths (`ty: "sh"`) carry a `ks` (shape keyframes) object whose value is the path data:

```json
{
  "ty": "sh",
  "ks": {
    "a": 0,
    "k": {
      "c": true,
      "v": [[0, 0], [100, 0], [100, 100], [0, 100]],
      "i": [[0, 0], [0, 0], [0, 0], [0, 0]],
      "o": [[0, 0], [0, 0], [0, 0], [0, 0]]
    }
  }
}
```

| Field | Meaning |
|---|---|
| `c` | Closed flag. If true, last vertex connects to first. **Do not duplicate the first vertex at the end.** |
| `v` | Vertex array — list of `[x, y]` points. |
| `i` | In-tangent per vertex — **relative to the vertex**. |
| `o` | Out-tangent per vertex — **relative to the vertex**. |

For straight-line polygons, all `i`/`o` are `[0, 0]` (no Bézier bulge).

For curves, in/out tangents define the Bézier handle offsets from each vertex (this is how After Effects represents paths internally).

### Animating paths (morphing)

When `a: 1`, `k` is a list of keyframes whose `s` is the path data object:

```json
{
  "ty": "sh",
  "ks": {
    "a": 1,
    "k": [
      {
        "t": 0,
        "s": [{ "c": true, "v": [...A...], "i": [...], "o": [...] }],
        "o": { "x": [0.4], "y": [0] },
        "i": { "x": [0.6], "y": [1] }
      },
      {
        "t": 30,
        "s": [{ "c": true, "v": [...B...], "i": [...], "o": [...] }]
      }
    ]
  }
}
```

**Critical**: vertex counts must match across path keyframes. To morph between shapes with different point counts, add invisible duplicate vertices to the simpler shape until counts match. The renderer interpolates vertex-by-vertex; mismatched counts produce undefined behavior.

Also note `s` wraps the path object in an array — `s: [pathObj]`, not `s: pathObj`. This is consistent with the "scalar keyframes are always arrays" rule.

## Masks

A layer can carry a `masksProperties` array of mask objects. Each mask is a path that clips the layer.

```json
"masksProperties": [
  {
    "inv": false,
    "mode": "a",
    "pt": { "a": 0, "k": { /* path data */ } },
    "o": { "a": 0, "k": 100 },
    "x": { "a": 0, "k": 0 }
  }
]
```

| Field | Meaning |
|---|---|
| `inv` | Invert mask. |
| `mode` | `"a"` = add, `"s"` = subtract, `"i"` = intersect, `"l"` = lighten, `"d"` = darken, `"f"` = difference. |
| `pt` | Mask shape (animatable path). |
| `o` | Mask opacity. |
| `x` | Mask expansion (positive = grow, negative = shrink). |

Mattes (one layer used as alpha for another) work differently: the matte layer sits above its target with `td: 1` (matte track), and the target has `tt: 1` (alpha) or `tt: 2` (alpha inverted).

## Assets

```json
"assets": [
  {
    "id": "image_0",
    "w": 100,
    "h": 100,
    "u": "images/",
    "p": "img_0.png",
    "e": 0
  },
  {
    "id": "comp_0",
    "layers": [ /* nested composition */ ]
  }
]
```

Image asset: referenced by image layers (`ty: 2`) via `refId`. Path `u + p` resolves to the file. If `e: 1` and `p` is a data URI, the image is embedded.

Precomp asset: a nested composition, referenced by precomp layers (`ty: 0`) via `refId`. Treat the precomp like its own animation — has its own `layers` but inherits parent comp's `fr`.

---

## Quick validation checklist

Before finalizing any Lottie file, eyeball these:

- [ ] Top-level: `v`, `fr`, `ip`, `op`, `w`, `h`, `assets`, `layers` all present
- [ ] Every layer has `ind`, `ty`, `nm`, `ks`, `ip`, `op`
- [ ] Every transform `ks` has `o`, `r`, `p`, `a`, `s`
- [ ] Colors are 0–1 floats, not 0–255 integers
- [ ] Scalar animated values use `[value]` arrays in `s`
- [ ] Tangent dimensions match value dimensions
- [ ] Keyframes are in time order (ascending `t`)
- [ ] Closed paths use `c: true`, do not duplicate first vertex
- [ ] Path morph keyframes have matching vertex counts
- [ ] Shape groups have `tr` as last item
- [ ] Layer `op` matches composition `op` (unless intentional exit)

The `validate_lottie.py` script checks all of these automatically.
