# dotLottie Themes Reference (v2.0)

Themes let one animation render with different palettes, stroke widths, or
even different images and text — without duplicating the Lottie file. Common
use cases: light/dark variants of a single icon, multi-brand theming of a
generic loader, or runtime customization driven by a state machine.

Spec: https://dotlottie.io/spec/2.0/#themes

## The Slot Prerequisite

Themes do not target Lottie properties by name or path. They target **slot
IDs**. A slot ID is a string you place inside the Lottie animation on the
specific property you want themed.

**If a property has no slot ID, no theme can change it.** This is the most
common source of "my theme is ignored" issues. Slot the property in the
animation first, then write the theme rule.

Slots are part of the [Lottie spec itself](https://lottie.github.io/lottie-spec/1.0/specs/helpers/#slots),
not dotLottie. The slot ID is added as a `sid` field on the animated
property, alongside its `a`, `k`, etc.

### Slotting a Fill Color (Example)

A normal fill, before slotting:

```json
{
  "ty": "fl",
  "c": { "a": 0, "k": [0.95, 0.31, 0.85, 1] },
  "o": { "a": 0, "k": 100 },
  "r": 1
}
```

After slotting the color so a theme can override it:

```json
{
  "ty": "fl",
  "c": { "a": 0, "k": [0.95, 0.31, 0.85, 1], "sid": "brand_primary" },
  "o": { "a": 0, "k": 100 },
  "r": 1
}
```

Slot IDs are **case-sensitive** and arbitrary strings — name them by what they
represent (`brand_primary`, `accent`, `outline_width`, `logo_text`), not what
they are technically.

### Which Properties Can Be Slotted

Any animated property in the Lottie spec accepts a `sid`. The dotLottie theme
system supports rules of these types:

| Theme Type    | Lottie property examples                                       |
| ------------- | -------------------------------------------------------------- |
| `Color`       | fill `c`, stroke `c`, gradient stop colors, text fill          |
| `Scalar`      | opacity `o`, stroke width `w`, rotation `r`, single rotations  |
| `Vector`      | scale `s`, ellipse size `s`, rect size `s`                     |
| `Position`    | position `p`, anchor point `a`, gradient endpoints             |
| `Gradient`    | gradient fill `g`, gradient stroke `g`                         |
| `Image`       | image asset references                                          |
| `Text`        | text document properties (`text`, font, color, etc.)           |

## Theme File Structure

A theme file is a JSON object with a `rules` array. Each rule targets exactly
one slotted property.

```json
{
  "rules": [
    {
      "id": "brand_primary",
      "type": "Color",
      "value": [0.949, 0.314, 0.847]
    },
    {
      "id": "outline_width",
      "type": "Scalar",
      "value": 4
    }
  ]
}
```

## Rule Common Fields

| Field        | Required | Description                                                                 |
| ------------ | -------- | --------------------------------------------------------------------------- |
| `id`         | yes      | Slot ID inside the animation. Case-sensitive.                               |
| `type`       | yes      | One of `Color`, `Scalar`, `Position`, `Vector`, `Gradient`, `Image`, `Text`. |
| `animations` | no       | Array of animation IDs. If omitted, the rule applies to **all** animations in the package. |
| `value`      | one of   | Static override. **Either** `value` **or** `keyframes` must be present, not both. |
| `keyframes`  | one of   | Time-varying override.                                                       |
| `expression` | no       | Lottie expression. Takes precedence over both `value` and `keyframes`.       |

## Per-Type Value Formats

### Color

Static:
```json
{ "id": "brand", "type": "Color", "value": [0.95, 0.31, 0.85] }
```

The array is `[R, G, B]` in normalized 0–1 floats. RGBA `[R, G, B, A]` is also
accepted (per the schema), but the renderer-side support for alpha in theme
colors is inconsistent — use opacity (Scalar) on a sibling property if you
need translucency.

Animated:
```json
{
  "id": "brand",
  "type": "Color",
  "keyframes": [
    { "frame": 0,  "value": [0.95, 0.31, 0.85] },
    { "frame": 60, "value": [0.31, 0.95, 0.45] }
  ]
}
```

### Scalar

```json
{ "id": "stroke_width", "type": "Scalar", "value": 4 }
```

Numeric — opacity (0–100 for Lottie `o` properties, 0–1 for some others
depending on which property is slotted; the theme just hands the raw number
through, so match what the underlying property expects).

### Vector

Used for 2-component values like scale and size. The value is a 2-number array:
```json
{ "id": "logo_scale", "type": "Vector", "value": [100, 100] }
```

### Position

2D or 3D coordinates:
```json
{ "id": "center", "type": "Position", "value": [200, 150] }
```
Position keyframes also accept `valueInTangent` / `valueOutTangent` for spatial
(curved-path) interpolation, distinct from the temporal `inTangent`/`outTangent`
that handle easing.

### Gradient

The value is an array of `{color, offset}` stops:
```json
{
  "id": "bg_gradient",
  "type": "Gradient",
  "value": [
    { "color": [0.95, 0.31, 0.85], "offset": 0 },
    { "color": [0.31, 0.95, 0.85], "offset": 1 }
  ]
}
```
`offset` is normalized 0–1. `color` is `[R, G, B]` or `[R, G, B, A]`, 0–1.

### Image

Replaces an image asset by reference to another image in the `i/` directory
or by an external URL:
```json
{
  "id": "hero_image",
  "type": "Image",
  "value": {
    "id": "hero_dark",
    "width": 400,
    "height": 300
  }
}
```
`url` is also valid as a fallback or external source — HTTP(S) URLs and
data URIs are both supported by the schema. Renderer support for remote
URLs varies.

### Text

Replaces text document properties on a slotted text layer:
```json
{
  "id": "title",
  "type": "Text",
  "value": {
    "text": "Welcome",
    "fontName": "Inter-Bold",
    "fontSize": 48,
    "fillColor": [1, 1, 1],
    "justify": "Center",
    "textCaps": "AllCaps"
  }
}
```

Full text-document field list: `text`, `fontName`, `fontSize`, `fillColor`,
`strokeColor`, `strokeWidth`, `strokeOverFill`, `lineHeight`, `tracking`,
`justify` (Left/Right/Center/JustifyLast*), `textCaps` (Regular/AllCaps/SmallCaps),
`baselineShift`, `wrapSize`, `wrapPosition`. All optional — omitted fields
keep the animation's original values.

## Keyframe Format

Every animated rule type (except `Image`, which is non-temporal) uses the
same keyframe shape:

```json
{
  "frame": 30,
  "value": <type-specific>,
  "inTangent":  { "x": [0.4], "y": [0.0] },   // optional
  "outTangent": { "x": [0.6], "y": [1.0] },   // optional
  "hold": false                                // optional, default false
}
```

Tangents use the same Lottie bezier-handle format as the underlying spec —
arrays for multi-dimensional values, scalars or arrays for scalar values.

`hold: true` makes the value step-change at the next keyframe instead of
interpolating.

> See `easing.md` for tangent presets that work in both Lottie and theme
> keyframes.

## Expressions

`expression` is a string of JavaScript-like code that returns a value via the
`$bm_rt` variable. Expressions take precedence over `value` and `keyframes`,
are evaluated continuously, and fall back to the original property value if
invalid.

```json
{
  "id": "pulse_opacity",
  "type": "Scalar",
  "expression": "var $bm_rt; $bm_rt = Math.abs(Math.sin(time)) * 100;"
}
```

Available globals: `time` (seconds from animation start), `value` (the
original property value before theming), `thisComp`, `thisLayer`.

Built-ins: `Math.*`, `linear(t, v1, v2)`, `ease(t, v1, v2)`, `clamp(v, min, max)`,
`degreesToRadians(d)`, `timeToFrames(t, fps)`.

A few patterns that exercise the system:

```javascript
// Pulsing color brightness
var $bm_rt;
var pulse = (Math.sin(time * 2) + 1) / 2;
$bm_rt = [pulse, 0.3 * pulse, 0.8 * pulse];

// Orbiting position around the original spot
var $bm_rt;
var r = 50;
$bm_rt = [value[0] + Math.cos(time) * r, value[1] + Math.sin(time) * r];

// Clamp to stay in range
var $bm_rt;
$bm_rt = clamp(value * 1.5, 0, 100);
```

Reference: https://lottiefiles.github.io/lottie-docs/expressions/

> Expression evaluation is renderer-dependent and can be a performance hot
> path. If a `keyframes`-based version of the same effect is feasible, prefer
> it — predictable, faster, and works in renderers with limited expression
> support.

## Scoping with `animations`

To restrict a rule to specific animations in a multi-animation package:

```json
{
  "id": "accent",
  "type": "Color",
  "animations": ["loader", "success"],
  "value": [0.95, 0.31, 0.85]
}
```

Without the `animations` field, the rule fires on every animation in the
package that has a matching slot ID.

## Complete Worked Example: Light/Dark for a Loader

Animation `a/loader.json` (the relevant slotted properties):

```json
{
  "ty": "fl",
  "c": { "a": 0, "k": [0.95, 0.31, 0.85, 1], "sid": "primary_color" },
  "o": { "a": 0, "k": 100, "sid": "primary_opacity" }
}
```

Theme `t/light.json`:

```json
{
  "rules": [
    { "id": "primary_color",   "type": "Color",  "value": [0.07, 0.09, 0.15] },
    { "id": "primary_opacity", "type": "Scalar", "value": 100 }
  ]
}
```

Theme `t/dark.json`:

```json
{
  "rules": [
    { "id": "primary_color",   "type": "Color",  "value": [0.95, 0.95, 0.97] },
    { "id": "primary_opacity", "type": "Scalar", "value": 100 }
  ]
}
```

Manifest `manifest.json`:

```json
{
  "version": "2",
  "animations": [
    {
      "id": "loader",
      "initialTheme": "dark",
      "themes": ["light", "dark"]
    }
  ],
  "themes": [
    { "id": "light", "name": "Light Mode" },
    { "id": "dark",  "name": "Dark Mode" }
  ]
}
```

Runtime: the player loads `loader.json`, applies `dark.json` (the
`initialTheme`), and exposes `light` as an alternative. A state machine
or host application can switch by firing a `SetTheme` action.

## Common Mistakes

**No `sid` on the property** — the most frequent issue. Without slot IDs in
the animation, theme rules silently do nothing.

**Value type doesn't match rule type** — `Color` rule with a single number
instead of an `[R, G, B]` array, or `Scalar` with an array. Renderers will
reject the rule and fall back.

**Colors in 0–255 range** — themes use **0–1 floats**, same as Lottie itself.
`[255, 80, 200]` will render as washed-out white because the values clamp.

**Both `value` and `keyframes` set** — the schema enforces exactly one.

**Forgetting renderer-side validation** — the spec says "unknown themes are
rejected during validation" and "theme changes apply to the renderer
immediately." If you ship a theme that references a slot ID that doesn't
exist in the animation, the renderer will reject the theme, not silently
ignore the missing slot.

**Named colors** — explicitly unsupported. `"red"`, `"#F250D8"`, and CSS
notation will all fail. Use float RGB(A) arrays only.

**Trying to add new layers or shapes via theme** — themes can override
existing properties; they can't add geometry. For different visuals, either
include both as separate layers (with opacity slots) or ship two animations.

**Expression returns wrong type** — an expression on a `Color` rule must
return a 3-element (or 4-element) array; a `Scalar` rule expects a single
number. Type mismatch falls back silently to the original value.
