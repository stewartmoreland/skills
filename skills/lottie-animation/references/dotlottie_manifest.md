# dotLottie Manifest Reference (v2.0)

The `manifest.json` at the root of every `.lottie` archive declares what's
inside and how it loads. This file is **required**; everything else (themes,
state machines, image and font assets) is optional.

Spec: https://dotlottie.io/spec/2.0/

## File Layout Recap

```
my_animation.lottie         ← ZIP archive (Deflate), MIME: application/zip+dotlottie
├── manifest.json           ← required
├── a/                      ← required: Lottie JSON animations
│   ├── loader.json
│   └── success.json
├── i/                      ← optional: image assets (png/jpg/webp/svg)
├── t/                      ← optional: theme JSON files
├── s/                      ← optional: state machine JSON files
└── f/                      ← optional: font assets (ttf/otf/woff/woff2)
```

Every filename in those directories must match the pattern
`^[a-zA-Z0-9._\- ]+$` — POSIX-compliant, no slashes, no special characters.

## Top-Level Manifest Fields

| Field             | Required | Type     | Notes |
| ----------------- | -------- | -------- | ----- |
| `version`         | yes      | string   | **Must be the string `"2"`** (not the number 2). |
| `generator`       | no       | string   | Identifies the tool, e.g. `"Anivect@1.0"`. |
| `animations`      | yes      | array    | At least one entry. Each `id` must match a file in `a/`. |
| `themes`          | no       | array    | One entry per theme file in `t/`. |
| `stateMachines`   | no       | array    | One entry per state machine file in `s/`. |
| `initial`         | no       | object   | `{stateMachine?: string, animation?: string}` — what the player loads first. If omitted, players load the first animation in the array. |

## Per-Animation Entry

```json
{
  "id": "loader",              // matches a/loader.json
  "initialTheme": "dark",      // optional, ID of a theme to apply on load
  "background": 4126537471,    // optional, u32 RGBA (see below)
  "themes": ["light", "dark"]  // optional: scoped themes available for this animation
}
```

The `id` is the **filename stem** — `a/loader.json` → `id: "loader"`. Same
pattern restriction as filenames: `^[a-zA-Z0-9._\- ]+$`.

`themes` here is *scoping*: it limits which themes from the top-level `themes`
array can be applied to this specific animation. Omitting it means all themes
can target this animation. This matters when one package contains multiple
animations and you want to restrict which themes are valid for each.

### Background Color: u32 RGBA Encoding

`background` is a single u32 integer, NOT an array. The byte order is **RGBA**:

```
0xRRGGBBAA
```

Conversion helpers:

```python
def rgba_to_u32(r, g, b, a=255):
    """0-255 ints → u32 RGBA."""
    return (r << 24) | (g << 16) | (b << 8) | a

def hex_to_u32(hex_str, alpha=255):
    """'#F250D8' → u32 with alpha."""
    h = hex_str.lstrip("#")
    return (int(h[0:2], 16) << 24) | (int(h[2:4], 16) << 16) | (int(h[4:6], 16) << 8) | alpha
```

Examples:
- `0xFFFFFFFF` (4294967295) = opaque white
- `0x000000FF` (255) = opaque black
- `0xF250D8FF` (4065856255) = Anivect pink, opaque
- `0x00000000` (0) = fully transparent

The spec example uses `4126537471` which is `0xF5F6F7FF` — a near-white opaque
background.

## Per-Theme Entry

```json
{
  "id": "dark",   // matches t/dark.json
  "name": "Dark Mode"   // optional human-readable label
}
```

## Per-State-Machine Entry

```json
{
  "id": "button",   // matches s/button.json
  "name": "Button States"   // optional human-readable label
}
```

## Initial Loading

```json
"initial": {
  "stateMachine": "button",   // load this state machine on open
  "animation": "loader"       // OR load this animation directly
}
```

You can set either, both, or neither. If both are set, the state machine
takes effect and its initial state determines which animation actually plays.
If neither is set, players load the **first entry** in the `animations` array.

## Complete Example

A logo animation with light and dark themes plus a hover-to-play state machine:

```json
{
  "version": "2",
  "generator": "Anivect@1.0",
  "initial": {
    "stateMachine": "hover"
  },
  "animations": [
    {
      "id": "logo",
      "initialTheme": "light",
      "themes": ["light", "dark"]
    }
  ],
  "themes": [
    { "id": "light", "name": "Light Mode" },
    { "id": "dark",  "name": "Dark Mode" }
  ],
  "stateMachines": [
    { "id": "hover", "name": "Hover to Play" }
  ]
}
```

Corresponding archive contents:
```
manifest.json
a/logo.json
t/light.json
t/dark.json
s/hover.json
```

## Validation Checklist

Before packaging, confirm:

- [ ] `version` is the string `"2"`, not the integer `2`
- [ ] Every `animations[].id` has a matching `a/<id>.json` file
- [ ] Every `themes[].id` has a matching `t/<id>.json` file
- [ ] Every `stateMachines[].id` has a matching `s/<id>.json` file
- [ ] Every per-animation `initialTheme` exists in the top-level `themes`
- [ ] Every per-animation `themes` entry exists in the top-level `themes`
- [ ] `initial.stateMachine` (if set) exists in `stateMachines`
- [ ] `initial.animation` (if set) exists in `animations`
- [ ] All IDs and filenames match `^[a-zA-Z0-9._\- ]+$`
- [ ] All filenames in archive directories include the `.json` extension
- [ ] The `a/` directory contains **at least one** animation
- [ ] No `additionalProperties` are present (the schema is strict)

The `validate_dotlottie.py` script enforces all of these.

## Common Mistakes

**Wrong version type** — using `"version": 2` (integer) instead of `"version": "2"` (string).
The schema requires the string form.

**Filename/ID mismatch** — `manifest.json` says `"id": "loader"` but the
file is `a/loader-v2.json`. The packager will fail to resolve the reference.

**Missing animations directory** — the `a/` directory is required even
if you only have one animation. Putting the JSON at the archive root won't
work.

**Slashes in IDs** — IDs like `"animations/loader"` violate the pattern.
Use simple identifiers, then organize within the file structure (but the
spec doesn't support subdirectories inside `a/`, `t/`, `s/`, `i/`, or `f/`).

**Extra fields** — both the manifest and theme/state-machine schemas use
`"additionalProperties": false`. Custom keys will fail strict validation.
