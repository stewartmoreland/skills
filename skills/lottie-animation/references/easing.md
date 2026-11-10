# Easing in Lottie

Lottie easing is encoded as **cubic Bézier tangent control points** on each keyframe. This file gives you the math, the format, and ready-to-paste values for every common easing curve.

## How Lottie easing works

Each keyframe carries two tangent objects:
- `o` ("out" tangent) — controls how the curve **leaves** this keyframe heading toward the next
- `i` ("in" tangent) — controls how the curve **arrives** at this keyframe from the previous

The interpolation between keyframe A and keyframe B is the cubic Bézier curve:
- Control point 1 = `A.o` (x, y) in normalized [0,1] space
- Control point 2 = `B.i` (x, y) in normalized [0,1] space

This is the **exact same parameterization as CSS `cubic-bezier(x1, y1, x2, y2)`**:
- `x1, y1 = A.o.x, A.o.y`
- `x2, y2 = B.i.x, B.i.y`

So any CSS easing curve translates directly. This is enormously useful — you can prototype in CSS and copy the values over.

## Tangent format

For a **single-dimension** animated value (rotation, opacity, single-axis scale):

```json
{
  "t": 0,
  "s": [100],
  "o": { "x": [0.16], "y": [1] },
  "i": { "x": [0.3], "y": [1] }
}
```

For a **multi-dimensional** animated value (position 2D/3D, scale 2D, color), the `x` and `y` arrays must have one entry per dimension:

```json
{
  "t": 0,
  "s": [100, 200],
  "o": { "x": [0.16, 0.16], "y": [1, 1] },
  "i": { "x": [0.3, 0.3], "y": [1, 1] }
}
```

If the tangent array length doesn't match the value array length, **the renderer silently falls back to linear**. This is the most common cause of "I added easing but it still looks linear" bugs.

## Where to put tangents

Tangents on the **first keyframe** describe how motion leaves that keyframe toward the next:
- `o` is required (out tangent — used in interpolation)
- `i` is technically optional but conventionally `{"x": [0], "y": [0]}` (zero-tangent for "no previous segment")

Tangents on the **last keyframe** describe how motion arrived:
- `i` is required (in tangent — used in interpolation)
- `o` is conventionally `{"x": [0], "y": [0]}`

**Middle keyframes** need both `i` (arriving from previous) and `o` (leaving to next).

## Easing presets (ready to paste)

These are normalized for a single-dimension value. For N dimensions, repeat each scalar N times in the array.

### Linear (avoid unless intentional)
```json
"o": { "x": [1], "y": [1] }, "i": { "x": [0], "y": [0] }
```

### Ease (standard) — gentle in, fast out, gentle settle
```json
"o": { "x": [0.25], "y": [0.1] }, "i": { "x": [0.25], "y": [1] }
```

### Ease-in (slow start, fast finish) — good for **exits**
```json
"o": { "x": [0.42], "y": [0] }, "i": { "x": [1], "y": [1] }
```

### Ease-out (fast start, slow finish) — good for **entrances**
```json
"o": { "x": [0], "y": [0] }, "i": { "x": [0.58], "y": [1] }
```

### Ease-in-out (slow-fast-slow) — good for **between-states**
```json
"o": { "x": [0.42], "y": [0] }, "i": { "x": [0.58], "y": [1] }
```

### Material standard (Google's default)
```json
"o": { "x": [0.4], "y": [0] }, "i": { "x": [0.2], "y": [1] }
```

### Material decelerate (entering screen)
```json
"o": { "x": [0], "y": [0] }, "i": { "x": [0.2], "y": [1] }
```

### Material accelerate (exiting screen)
```json
"o": { "x": [0.4], "y": [0] }, "i": { "x": [1], "y": [1] }
```

### Cubic in
```json
"o": { "x": [0.55], "y": [0.055] }, "i": { "x": [0.675], "y": [0.19] }
```

### Cubic out — **recommended default for entrances**
```json
"o": { "x": [0.215], "y": [0.61] }, "i": { "x": [0.355], "y": [1] }
```

### Cubic in-out
```json
"o": { "x": [0.645], "y": [0.045] }, "i": { "x": [0.355], "y": [1] }
```

### Quart out (sharper than cubic)
```json
"o": { "x": [0.165], "y": [0.84] }, "i": { "x": [0.44], "y": [1] }
```

### Expo out (very fast start, long settle)
```json
"o": { "x": [0.19], "y": [1] }, "i": { "x": [0.22], "y": [1] }
```

### Back in (slight backward dip before forward motion)
```json
"o": { "x": [0.6], "y": [-0.28] }, "i": { "x": [0.735], "y": [0.045] }
```

### Back out (overshoot then settle) — **great for entrances with personality**
```json
"o": { "x": [0.175], "y": [0.885] }, "i": { "x": [0.32], "y": [1.275] }
```
The `y > 1` is intentional and supported — it produces the overshoot.

### Back in-out
```json
"o": { "x": [0.68], "y": [-0.55] }, "i": { "x": [0.265], "y": [1.55] }
```

### Spring (multi-keyframe) — see below

## Spring / bounce — multi-keyframe approach

Lottie doesn't have a native spring easing. For convincing spring motion, use 3+ keyframes with eased segments:

```
frame 0:  scale = [0, 0]         (start)
frame 18: scale = [115, 115]     (overshoot — back-out easing from previous)
frame 28: scale = [96, 96]       (undershoot — ease-in-out)
frame 36: scale = [102, 102]     (settle — ease-in-out)
frame 44: scale = [100, 100]     (rest — ease-out)
```

Each segment uses the standard cubic eases above. The amplitude of overshoot/undershoot should diminish ~50% per oscillation.

For "snappy" UI springs, two overshoots is plenty. For "bouncy" character springs, 3–4. More than 4 reads as broken rather than spring.

## Picking the right easing

| Action type | Default choice |
|---|---|
| Fade in / scale in / slide in | Cubic out or Back out |
| Fade out / scale out / slide out | Cubic in |
| Move from A to B (both stationary) | Cubic in-out or Quart in-out |
| Continuous loop (rotation, idle pulse) | Linear (with care) or sine wave |
| Acknowledging input (button tap, etc.) | Back out (subtle, e.g., y: 1.1 not 1.5) |
| Dismissive exit (modal close, etc.) | Cubic in or Quart in |
| Attention pulse (notification, error) | Spring with 2 overshoots |

## Hold keyframes

To make a value "stick" with no interpolation until the next keyframe (e.g., visibility toggles), set `h: 1` on the keyframe:

```json
{ "t": 30, "s": [100], "h": 1 }
```

The value stays at 100 until the next keyframe at time T, then snaps to the next value. Useful for stepped/digital animations or layer visibility tricks.

## A note on dotLottie tween-transition easing

dotLottie state machines have a different easing representation for **Tweened transitions** (state-to-state crossfades). Where a Lottie keyframe expresses easing as the pair of objects `o: {x, y}` and `i: {x, y}` on consecutive keyframes, a Tweened transition expresses the entire curve as a single 4-tuple:

```json
{
  "type": "Tweened",
  "toState": "active",
  "duration": 0.3,
  "easing": [0.4, 0.0, 0.2, 1.0]
}
```

The four numbers are `[x1, y1, x2, y2]` — the same cubic Bézier control points as CSS `cubic-bezier()` and the same numbers you'd derive from a Lottie keyframe pair (`o.x, o.y, i.x, i.y` of the next keyframe). They just live in a flat array instead of two objects.

| Curve            | Lottie keyframe `o`/`i`                           | Tween `easing`            |
|------------------|---------------------------------------------------|---------------------------|
| Material standard | `o: {x:[0.4], y:[0]}, i: {x:[0.2], y:[1]}`      | `[0.4, 0.0, 0.2, 1.0]`    |
| Cubic in-out      | `o: {x:[0.65], y:[0]}, i: {x:[0.35], y:[1]}`    | `[0.65, 0.0, 0.35, 1.0]`  |
| Back out          | `o: {x:[0.34], y:[1.56]}, i: {x:[0.64], y:[1]}` | `[0.34, 1.56, 0.64, 1.0]` |
| Linear            | (no tangents / `o.y=x, i.y=x`)                    | `[0, 0, 1, 1]`            |

Use the same curves you'd use in CSS — there's no separate aesthetic vocabulary, just two different serializations of the same math.

