---
name: lottie-animation
description: Use this skill whenever the user wants to create, edit, refine, debug, package, or convert Lottie animations or dotLottie v2.0 packages — including any mention of .lottie files, .json animation files, Bodymovin output, lottie-web/ios/android or dotlottie-* renderers, or requests like "animate this SVG", "build a loading spinner", "morph this icon", "make a Lottie", "draw on", "animate a logo reveal", "create a microinteraction", "package as .lottie", "add light/dark themes", "build a state machine for this", or "make this interactive". Also use for fixing broken Lottie/.lottie files, adding easing, converting SVG to Lottie, or bundling animations + themes + state machines. Trigger even without the word "Lottie" — if the user wants JSON-based vector animation or packaged animated UI for web/mobile, this is the right skill.
---

# Lottie & dotLottie Animation

A skill for building **production-quality** Lottie animations and **dotLottie v2.0** packages from text descriptions, SVGs, reference images, or existing files. The skill targets two layers:

- **Lottie JSON** — the animation itself: vector shapes, layers, keyframes, easing. Renders in lottie-web / lottie-ios / lottie-android / lottie-react-native and (extracted) in dotLottie players.
- **dotLottie v2.0** — a ZIP archive (`.lottie`) that bundles one or more animations with optional themes (slot-based property overrides), state machines (interactivity), images, and fonts. Renders in the dotlottie-* player family.

Most prompts want either a single Lottie JSON or a `.lottie` package. Decide which based on what the user is actually building (see [Choosing the output format](#choosing-the-output-format) below).

## Why this skill exists

Lottie is unforgiving in two directions. Get the JSON structure wrong (missing `ip`/`op`, wrong tangent dimensions, scalar-not-wrapped-in-array) and the file silently fails to render or renders glitchy. Get the *animation* wrong (linear easing, no anticipation, sequential timing where overlap is wanted) and it renders fine but looks robotic and amateur.

dotLottie adds a third failure mode: structural correctness inside the ZIP. A theme rule with no matching slot in the animation silently does nothing. A state machine that references a missing animation ID fails to load. A manifest with `"version": 2` (integer) instead of `"version": "2"` (string) fails schema validation. These don't surface as obvious errors — they surface as "the animation just plays without the theme" or "the package won't load" with no useful diagnostic.

Most Lottie produced by language models fails the second test (animation quality); most dotLottie produced by language models fails the third (package structure). This skill exists to close both gaps.

## Workflow

For any task, work through these steps in order. Skip steps only when they don't apply.

1. **Understand the request.** What's the animation showing? What's the duration, frame rate, and canvas size? What's the input — text description, SVG, image, or existing Lottie/dotLottie? Do they need themes (light/dark, brand variants)? Do they need interactivity (toggle, hover-to-play, branching states)? If they handed you an SVG or existing file, **read it first** before designing motion.

2. **Choose the output format.** Single animation → Lottie JSON. Multi-animation, themed, or interactive → dotLottie. See [Choosing the output format](#choosing-the-output-format).

3. **Plan the motion before writing JSON.** Sketch the timing in plain words: "Frames 0–12: dot scales up with bounce. Frames 8–24: ring fades in (overlap). Frames 24–60: ring rotates while dot pulses." Decide what's a hero element (gets most attention/anticipation) vs. supporting motion (subtler, offset timing). This planning step is the difference between hand-tuned animation and randomly-timed keyframes.

4. **Plan the package** (dotLottie only). What animations are in it? What slot IDs does each one expose for theming? What themes exist? Does it need a state machine, and if so what are the states and what events drive transitions?

5. **Choose the build approach** for the animations themselves (see [Build approaches](#build-approaches)):
   - Direct JSON for simple, single-composition animations
   - Programmatic Python builder via `scripts/lottie_builder.py` for stagger, repetition, or >3 layers

6. **Add slot IDs to themable properties** (dotLottie only). A property without a `sid` field cannot be themed. See [`references/dotlottie_themes.md`](references/dotlottie_themes.md) for the slotting pattern.

7. **Apply easing on every keyframe.** Linear easing is almost always wrong. See [`references/easing.md`](references/easing.md) for ready-to-paste tangent values. Tweened state machine transitions use a separate 4-tuple format also covered there.

8. **Validate.** For animations: `python scripts/validate_lottie.py <file.json>`. For dotLottie packages: `python scripts/dotlottie_packager.py --from-dir <sources/> --check-only`. Both catch structural errors before you ship.

9. **Preview.** For animations: `python scripts/preview_lottie.py <file.json> --frames 8 --gif`. For dotLottie packages: `python scripts/dotlottie_inspector.py <file.lottie>` to print the structure including slot IDs, theme targets, and state machine wiring.

10. **Save to `/mnt/user-data/outputs/`** and present the file. For dotLottie deliveries, include the inspector output as proof of correctness.

## Choosing the output format

| Situation                                                              | Format        |
|------------------------------------------------------------------------|---------------|
| "Animate this SVG", "make a loader", "animate my logo"                 | Lottie JSON   |
| "Make a light/dark variant of this animation"                          | dotLottie     |
| "Make this animation interactive" (click, hover, toggle, ratings, etc.) | dotLottie     |
| "Bundle these three animations together"                               | dotLottie     |
| "Add brand theming"                                                    | dotLottie     |
| "Convert this to .lottie format" or any explicit mention of `.lottie`  | dotLottie     |

When in doubt: if the user only needs one animation with no theming or interactivity, a plain Lottie JSON is simpler to embed and works in more places (including legacy renderers). If they need any of the v2.0 features — themes, state machines, multi-animation packages — use dotLottie.

You can always start with Lottie JSON and wrap it in a dotLottie later — the JSON file becomes `a/<id>.json` inside the archive.

## Build approaches (animations)

### Direct JSON

Best for: small, focused animations — a loading dot, a fade-in checkmark, a single icon morph. Keeps the artifact human-readable and tweakable.

Start from `assets/templates/basic_starter.json` rather than writing from scratch. The template has correct top-level structure (`v`, `fr`, `ip`, `op`, `w`, `h`, `assets`, `layers`) and one shape layer with a properly-formed transform — copy and modify.

### Programmatic Python builder

Best for: anything with repetition, stagger, computed timing, parametric motion, or many layers.

```python
from lottie_builder import (
    Animation, ShapeLayer, ellipse, fill, group, group_transform,
    layer_transform, keyframes, EASE, hex_to_rgba,
)

anim = Animation(width=200, height=200, fps=60, duration_frames=60)

for i in range(8):
    delay = i * 3  # stagger by 3 frames at 60fps
    dot = ShapeLayer(
        name=f"dot_{i}",
        transform=layer_transform(position=[100 + i*15, 100]),
        shapes=[group(f"g{i}", [
            ellipse(size=[40, 40]),
            fill(color=hex_to_rgba("#F250D8")),
            group_transform(scale=keyframes([
                (delay,      [0, 0, 100],     EASE.OUT_BACK),
                (delay + 18, [100, 100, 100]),
            ])),
        ])],
    )
    anim.add_layer(dot)

anim.save("dots.json")
```

The builder handles the boilerplate (default transforms, proper array wrapping for scalar keyframes, tangent dimension matching) so the resulting JSON is well-formed.

## The fidelity multipliers

Five things separate professional Lottie from amateur output. In order of impact:

### 1. Easing curves on every keyframe

Linear interpolation is the single biggest tell that an animation was generated by something that doesn't understand motion. Real motion accelerates and decelerates. Every meaningful property change (position, scale, rotation, opacity, color, path data) should have eased keyframes.

Standard presets in `references/easing.md`:
- **Ease out** for entrances (object starts fast, settles) — `o:{x:[0.16],y:[1]}`, next keyframe `i:{x:[0.3],y:[1]}`
- **Ease in** for exits (object starts slow, accelerates away)
- **Ease in-out** for moves between two static states
- **Spring/back** for playful overshoots

For multidimensional properties (position, scale), the `x` and `y` tangent arrays must have the same dimensionality as the value being animated — get this wrong and the renderer silently falls back to linear.

### 2. Correct anchor points

The anchor (`a` in `ks`) is the pivot for rotation and scale. Default `[0,0]` means rotation pivots around the top-left of the layer's coordinate space — almost never what you want. For a centered shape that should scale or rotate around its center:
- Put the shape geometry at `[0,0]` (e.g., circle at `{"p": [0,0]}`)
- Set the **group transform's** `a` to `[0,0]`
- Set the layer's `ks.p` to where you want it on canvas
- Set the layer's `ks.a` to `[0,0]`

### 3. Stagger and overlap

Sequential motion feels mechanical. Overlapping motion (B starts at A's 60% mark, C starts at B's 60% mark) feels organic. Offset each layer's first keyframe by 3–6 frames at 60fps.

### 4. Anticipation

Before a big motion, briefly move slightly in the opposite direction. A scale-up can briefly scale down by 5–10% before expanding. Costs 4–8 frames at the start of an action but transforms how it reads.

### 5. Secondary motion

Hero element does the main move. Smaller elements do supporting moves *during* the hero move, not before or after. Adds visual richness without competing for attention.

For deeper coverage of all 12 animation principles applied to Lottie, see [`references/principles.md`](references/principles.md).

## Lottie JSON essentials

Lottie is frame-based, not time-based. The `fr` field is frame rate; `ip` (in point) and `op` (out point) are frame numbers. A 2-second animation at 60fps means `ip: 0, op: 120`.

Coordinate system: origin is top-left, Y increases downward, rotation is clockwise (matches SVG/CSS conventions).

Colors inside Lottie JSON are arrays of floats in `[0, 1]`, NOT 0–255 integers. `[1, 0.42, 0.84, 1]` is hot pink with full alpha. Forgetting this produces invisible white-clipped output.

Scalar animated values are still arrays. Rotation keyframe values are `[degrees]`, not `degrees`. Opacity keyframe values are `[percent]`, not `percent`.

Full schema reference: [`references/schema.md`](references/schema.md).

## dotLottie packaging

A `.lottie` is a ZIP archive containing a `manifest.json` plus a layout:

```
my.lottie
├── manifest.json    # required
├── a/*.json         # animations (at least one)
├── t/*.json         # themes (optional)
├── s/*.json         # state machines (optional)
├── i/*              # image assets (optional)
└── f/*              # font assets (optional)
```

Three reference docs cover the moving parts:
- [`references/dotlottie_manifest.md`](references/dotlottie_manifest.md) — the `manifest.json` schema, filename rules, u32 RGBA encoding for backgrounds, initial loading
- [`references/dotlottie_themes.md`](references/dotlottie_themes.md) — slot IDs, rule types (Color/Scalar/Position/Vector/Gradient/Image/Text), keyframes, expressions
- [`references/dotlottie_state_machines.md`](references/dotlottie_state_machines.md) — PlaybackState/GlobalState, transitions (immediate and Tweened), guards (Numeric/String/Boolean/Event), actions, interactions, inputs

### Building a `.lottie`

Two workflows. Both end with `scripts/dotlottie_packager.py`.

**A. From a source directory** (the cleanest path — mirror the spec layout, then package):

```bash
sources/
├── manifest.json
├── a/indicator.json
├── t/brand.json
├── t/dark.json
└── s/toggle.json

python scripts/dotlottie_packager.py --from-dir sources/ -o my.lottie
```

A working starter in this layout lives at `assets/templates/dotlottie_starter/` — copy it, edit, package.

**B. From explicit files** (no manifest needed — the packager generates one):

```bash
python scripts/dotlottie_packager.py \
    --animation a/loader.json \
    --theme    t/light.json \
    --theme    t/dark.json \
    --state    s/toggle.json \
    --initial-state-machine toggle \
    -o my.lottie
```

### Validating before shipping

```bash
python scripts/dotlottie_packager.py --from-dir sources/ --check-only
```

The validator catches:
- `version` not the string `"2"`
- Filenames violating `^[a-zA-Z0-9._\- ]+$`
- Manifest IDs without matching files (or files without manifest entries)
- Per-animation `initialTheme` not in the top-level themes
- State machine `animation` references that don't exist in the manifest
- State machine `toState` references that don't match any state name
- `initial` state name that doesn't match any state
- Tweened transitions missing `duration` or `easing`, or with a wrong-shape `easing`
- Duplicate input names
- Final states with transitions (contradiction)
- Themes with rules that have both `value` and `keyframes`

### Inspecting an existing `.lottie`

```bash
python scripts/dotlottie_inspector.py path/to/file.lottie
```

Prints the manifest, every animation (with size, duration, layer count, and slot IDs declared), every theme (with rule counts and which slot IDs it targets), every state machine (with states, transitions, interactions, inputs), and any cross-reference issues (theme targeting a slot ID that no animation declares, state machine referencing a missing animation, etc.).

Useful for QA on a `.lottie` you didn't build yourself and for confirming a build is wired correctly before delivery.

### Slot IDs: the most important concept

A `dotLottie` theme can only override Lottie properties that have been marked with a `sid` field. Without slot IDs in the animation, themes silently do nothing.

```json
// before slotting
{ "ty": "fl", "c": { "a": 0, "k": [0.95, 0.31, 0.85, 1] } }

// after — now themes can target "brand_primary"
{ "ty": "fl", "c": { "a": 0, "k": [0.95, 0.31, 0.85, 1], "sid": "brand_primary" } }
```

When generating an animation that will be themed, plan the slot ID list **before** writing JSON: primary fill, secondary fill, accent stroke, line width, etc. Name slots by what they represent (`brand_primary`), not what they technically are (`fill_color_layer_1`). The inspector script lists all slot IDs found in animations — use it to verify before shipping.

## Cross-platform support

Animations work in lottie-web/iOS/Android/RN. dotLottie packages need a dotlottie-* player (dotlottie-web, dotlottie-react, dotlottie-ios, dotlottie-android, dotlottie-react-native). Legacy lottie-* players will not load a `.lottie` — they can render the extracted `a/<id>.json` but ignore manifests, themes, and state machines.

| Feature                  | lottie-* (legacy) | dotlottie-* (v2.0) |
|--------------------------|-------------------|--------------------|
| Lottie JSON animations   | ✅                | ✅                 |
| Manifest                 | n/a (no archive)  | ✅                 |
| Themes (slot-based)      | ❌                | ✅                 |
| State machines           | ❌                | ✅                 |
| Embedded images / fonts  | partial           | ✅                 |

Full feature matrix and the per-feature web/iOS/Android caveats live in [`references/platforms.md`](references/platforms.md).

When you use a feature that's not universally supported, flag it inline in your response (e.g. *"Note: this uses merge paths, which isn't supported on Android — provide an Android-safe version if needed"*).

## Common pitfalls

### Animation-quality pitfalls (apply to both Lottie JSON and dotLottie animations)

1. **Linear easing everywhere.** Default to ease-out for entrances, ease-in for exits, ease-in-out for between-states. Only use linear for continuous rotation loops.
2. **Anchor at `[0,0]` for centered shapes.** Use the group-transform anchor pattern from § Fidelity multipliers.
3. **Colors as 0–255.** Always 0–1 floats. `[0.95, 0.31, 0.55, 1]` not `[242, 79, 140, 255]`.
4. **Scalar keyframes not wrapped in arrays.** Rotation `s: [45]` not `s: 45`. Opacity `s: [100]` not `s: 100`.
5. **Tangent dimensions don't match value dimensions.** Position `s: [256, 200]` needs `o.x: [0.16, 0.16], o.y: [1, 1]` — two-element arrays.
6. **Layer `ip`/`op` mismatched with composition.** A layer with `ip: 0, op: 30` in a composition with `op: 60` will disappear halfway through. Set layer `op` to composition `op` unless you want it to exit.
7. **Stagger of 0 frames between siblings.** That's not stagger, that's synchronization. Use 3–8 frame offsets at 60fps.
8. **Forgetting the group transform `tr` inside a shape group.** Every `"ty": "gr"` group needs a `"ty": "tr"` item as its last element.
9. **Animating from `scale: [0, 0]` with non-centered anchor.** Creates a "growing from the corner" effect. Fix the anchor first.
10. **Frame rate mismatch on edits.** After Effects exports are often 30fps; if you import an existing Lottie and add keyframes, match the existing `fr`.

### dotLottie pitfalls

11. **`"version": 2` instead of `"version": "2"`.** The schema requires the string form. Integer fails validation.
12. **Theme rules with no matching slot.** The most common dotLottie bug. Add `sid` to the animation property first, then write the theme rule. The inspector lists declared vs targeted slot IDs.
13. **Manifest references a file that isn't there** (or vice versa). Every `animations[].id` needs an `a/<id>.json`; every theme/state machine entry needs a matching file. `--check-only` catches this.
14. **State machine `animation` field doesn't match a manifest ID.** It's the manifest's animation `id` (file stem), not the Lottie's internal `nm`.
15. **`Equal` vs `equals` in guard conditions.** The schema enum is `Equal`, `NotEqual`, `GreaterThan`, etc. — case-sensitive. The spec's own example uses `equals` in one place; that's a spec example error, not the schema.
16. **Tween easing as an object instead of a 4-tuple.** Tweened transitions use `easing: [x1, y1, x2, y2]`. Lottie-style `{x, y}` tangent objects don't work here. (See `references/easing.md`.)
17. **Background as a hex string.** `manifest.json` and PlaybackState `backgroundColor` use a u32 RGBA integer, e.g. `0xF250D8FF`. Strings fail.
18. **Filenames with slashes or special chars.** All names in `a/`, `t/`, `s/`, `i/`, `f/` must match `^[a-zA-Z0-9._\- ]+$`. No subdirectories inside those folders.
19. **Final state with non-empty transitions.** `final: true` is terminal — transitions are dead code. Pick one.
20. **Event guard with no event firing.** Event inputs need a `Fire` action or an SDK call to actually fire. They don't auto-fire on input changes.

## Examples and templates

### Animation patterns

Worked Lottie examples in [`references/patterns.md`](references/patterns.md):
- Pulsing neon dot loader
- SVG-to-Lottie checkmark draw-on (trim path)
- Logo wordmark assembly with staggered letter slide-in and bounce
- Path morph between two shapes
- Spinner with frame-perfect loop

Single-file templates in `assets/templates/`:
- `basic_starter.json` — the minimum valid Lottie
- `pulsing_loader.json` — a one-layer pulsing dot with proper easing
- `checkmark_draw.json` — trim path draw-on with overshoot

### dotLottie patterns

Full-package starter at `assets/templates/dotlottie_starter/` — a single animation with two themes (brand/dark) and a click-to-toggle state machine. Copy the directory, edit, and package.

Standalone state-machine template at `assets/templates/state_machine_hover.json` — drop into your `s/` directory and reference from a manifest. Plays only while hovered.

## File layout

```
lottie-animation/
├── SKILL.md (this file)
├── references/
│   ├── schema.md                    — full Lottie JSON schema reference
│   ├── easing.md                    — bezier tangent values + tween easing
│   ├── principles.md                — 12 animation principles applied to Lottie
│   ├── patterns.md                  — worked Lottie examples
│   ├── platforms.md                 — feature support: lottie-* and dotlottie-* renderers
│   ├── dotlottie_manifest.md        — manifest.json schema and rules
│   ├── dotlottie_themes.md          — slot-based theming
│   └── dotlottie_state_machines.md  — state machine spec (states, guards, actions, inputs)
├── scripts/
│   ├── lottie_builder.py            — Python builder for programmatic Lottie construction
│   ├── validate_lottie.py           — Lottie JSON structure validator
│   ├── preview_lottie.py            — render frames and GIF preview from JSON
│   ├── dotlottie_packager.py        — assemble + validate .lottie archives
│   └── dotlottie_inspector.py       — read a .lottie and report its structure
└── assets/templates/
    ├── basic_starter.json
    ├── pulsing_loader.json
    ├── checkmark_draw.json
    ├── state_machine_hover.json
    └── dotlottie_starter/           — full v2.0 starter package (manifest + a/t/s)
```

Read references on demand — they're each focused and don't all need to be loaded for every task. For a simple icon animation, `easing.md` and the schema essentials in this file are usually enough. For a themed `.lottie`, add `dotlottie_manifest.md` + `dotlottie_themes.md`. For interactivity, add `dotlottie_state_machines.md`.
