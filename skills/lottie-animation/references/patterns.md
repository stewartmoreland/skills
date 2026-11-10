# Lottie Patterns: Worked Examples

Complete worked examples for common animation patterns. Each shows the planning step, the technique used, and the resulting JSON. Copy and adapt these — they're tested and they apply the principles from [`principles.md`](principles.md).

## Table of contents

1. [Pulsing dot loader](#1-pulsing-dot-loader)
2. [Three-dot staggered loader](#2-three-dot-staggered-loader)
3. [Checkmark draw-on (trim path)](#3-checkmark-draw-on-trim-path)
4. [Icon morph between two states](#4-icon-morph-between-two-states)
5. [Logo wordmark assembly](#5-logo-wordmark-assembly)
6. [Spinner with trailing arc](#6-spinner-with-trailing-arc)
7. [Notification bell shake](#7-notification-bell-shake)
8. [Progress ring fill](#8-progress-ring-fill)

---

## 1. Pulsing dot loader

**Use case**: minimal "thinking" indicator. Single element, infinite loop, low visual weight.

**Plan**: A circle that scales from 80% → 110% → 80% over 60 frames (1s at 60fps), with eased motion to feel like a breath rather than a metronome. Opacity also pulses subtly (60% → 100% → 60%) in sync.

**Principles applied**: Slow in/slow out, secondary action (opacity pulse).

```json
{
  "v": "5.12.2", "fr": 60, "ip": 0, "op": 60, "w": 200, "h": 200,
  "nm": "Pulsing Dot", "ddd": 0, "assets": [], "layers": [
    {
      "ddd": 0, "ind": 1, "ty": 4, "nm": "Dot", "sr": 1,
      "ks": {
        "o": { "a": 1, "k": [
          { "t": 0,  "s": [60],  "o": {"x":[0.4],"y":[0]}, "i": {"x":[0.6],"y":[1]} },
          { "t": 30, "s": [100], "o": {"x":[0.4],"y":[0]}, "i": {"x":[0.6],"y":[1]} },
          { "t": 60, "s": [60] }
        ]},
        "r": { "a": 0, "k": 0 },
        "p": { "a": 0, "k": [100, 100, 0] },
        "a": { "a": 0, "k": [0, 0, 0] },
        "s": { "a": 1, "k": [
          { "t": 0,  "s": [80, 80, 100],  "o": {"x":[0.4,0.4,0.4],"y":[0,0,0]}, "i": {"x":[0.6,0.6,0.6],"y":[1,1,1]} },
          { "t": 30, "s": [110, 110, 100], "o": {"x":[0.4,0.4,0.4],"y":[0,0,0]}, "i": {"x":[0.6,0.6,0.6],"y":[1,1,1]} },
          { "t": 60, "s": [80, 80, 100] }
        ]}
      },
      "ao": 0, "shapes": [
        { "ty": "gr", "nm": "Group", "it": [
          { "ty": "el", "d": 1, "s": { "a": 0, "k": [60, 60] }, "p": { "a": 0, "k": [0, 0] } },
          { "ty": "fl", "c": { "a": 0, "k": [0.95, 0.31, 0.85, 1] }, "o": { "a": 0, "k": 100 }, "r": 1 },
          { "ty": "tr",
            "p": { "a": 0, "k": [0, 0] }, "a": { "a": 0, "k": [0, 0] },
            "s": { "a": 0, "k": [100, 100] }, "r": { "a": 0, "k": 0 }, "o": { "a": 0, "k": 100 }
          }
        ]}
      ],
      "ip": 0, "op": 60, "st": 0, "bm": 0
    }
  ]
}
```

To loop infinitely, the renderer config sets `loop: true` — the animation itself just plays from 0→60 and the player restarts.

---

## 2. Three-dot staggered loader

**Use case**: "typing" indicator, more visual weight than single dot.

**Plan**: Three dots arranged horizontally. Each scales 100→130→100 over 30 frames, but their start times are staggered by 6 frames. Composition runs 60 frames total so the cycle restarts cleanly.

**Principles applied**: Overlapping action (the core technique here), slow in/slow out.

```json
{
  "v": "5.12.2", "fr": 60, "ip": 0, "op": 60, "w": 300, "h": 100,
  "nm": "Three Dot Loader", "ddd": 0, "assets": [], "layers": [
    { "ddd": 0, "ind": 1, "ty": 4, "nm": "Dot 1", "sr": 1,
      "ks": {
        "o": { "a": 0, "k": 100 }, "r": { "a": 0, "k": 0 },
        "p": { "a": 0, "k": [100, 50, 0] }, "a": { "a": 0, "k": [0, 0, 0] },
        "s": { "a": 1, "k": [
          { "t": 0,  "s": [100,100,100], "o":{"x":[0.4,0.4,0.4],"y":[0,0,0]}, "i":{"x":[0.6,0.6,0.6],"y":[1,1,1]} },
          { "t": 15, "s": [130,130,100], "o":{"x":[0.4,0.4,0.4],"y":[0,0,0]}, "i":{"x":[0.6,0.6,0.6],"y":[1,1,1]} },
          { "t": 30, "s": [100,100,100] }
        ]}
      },
      "ao": 0, "shapes": [
        { "ty": "gr", "it": [
          { "ty": "el", "d": 1, "s": { "a": 0, "k": [30, 30] }, "p": { "a": 0, "k": [0, 0] } },
          { "ty": "fl", "c": { "a": 0, "k": [0.95, 0.31, 0.85, 1] }, "o": { "a": 0, "k": 100 }, "r": 1 },
          { "ty": "tr", "p":{"a":0,"k":[0,0]}, "a":{"a":0,"k":[0,0]}, "s":{"a":0,"k":[100,100]}, "r":{"a":0,"k":0}, "o":{"a":0,"k":100} }
        ]}
      ], "ip": 0, "op": 60, "st": 0, "bm": 0
    },
    { "ddd": 0, "ind": 2, "ty": 4, "nm": "Dot 2", "sr": 1,
      "ks": {
        "o": { "a": 0, "k": 100 }, "r": { "a": 0, "k": 0 },
        "p": { "a": 0, "k": [150, 50, 0] }, "a": { "a": 0, "k": [0, 0, 0] },
        "s": { "a": 1, "k": [
          { "t": 6,  "s": [100,100,100], "o":{"x":[0.4,0.4,0.4],"y":[0,0,0]}, "i":{"x":[0.6,0.6,0.6],"y":[1,1,1]} },
          { "t": 21, "s": [130,130,100], "o":{"x":[0.4,0.4,0.4],"y":[0,0,0]}, "i":{"x":[0.6,0.6,0.6],"y":[1,1,1]} },
          { "t": 36, "s": [100,100,100] }
        ]}
      },
      "ao": 0, "shapes": [
        { "ty": "gr", "it": [
          { "ty": "el", "d": 1, "s": { "a": 0, "k": [30, 30] }, "p": { "a": 0, "k": [0, 0] } },
          { "ty": "fl", "c": { "a": 0, "k": [0.95, 0.31, 0.85, 1] }, "o": { "a": 0, "k": 100 }, "r": 1 },
          { "ty": "tr", "p":{"a":0,"k":[0,0]}, "a":{"a":0,"k":[0,0]}, "s":{"a":0,"k":[100,100]}, "r":{"a":0,"k":0}, "o":{"a":0,"k":100} }
        ]}
      ], "ip": 0, "op": 60, "st": 0, "bm": 0
    },
    { "ddd": 0, "ind": 3, "ty": 4, "nm": "Dot 3", "sr": 1,
      "ks": {
        "o": { "a": 0, "k": 100 }, "r": { "a": 0, "k": 0 },
        "p": { "a": 0, "k": [200, 50, 0] }, "a": { "a": 0, "k": [0, 0, 0] },
        "s": { "a": 1, "k": [
          { "t": 12, "s": [100,100,100], "o":{"x":[0.4,0.4,0.4],"y":[0,0,0]}, "i":{"x":[0.6,0.6,0.6],"y":[1,1,1]} },
          { "t": 27, "s": [130,130,100], "o":{"x":[0.4,0.4,0.4],"y":[0,0,0]}, "i":{"x":[0.6,0.6,0.6],"y":[1,1,1]} },
          { "t": 42, "s": [100,100,100] }
        ]}
      },
      "ao": 0, "shapes": [
        { "ty": "gr", "it": [
          { "ty": "el", "d": 1, "s": { "a": 0, "k": [30, 30] }, "p": { "a": 0, "k": [0, 0] } },
          { "ty": "fl", "c": { "a": 0, "k": [0.95, 0.31, 0.85, 1] }, "o": { "a": 0, "k": 100 }, "r": 1 },
          { "ty": "tr", "p":{"a":0,"k":[0,0]}, "a":{"a":0,"k":[0,0]}, "s":{"a":0,"k":[100,100]}, "r":{"a":0,"k":0}, "o":{"a":0,"k":100} }
        ]}
      ], "ip": 0, "op": 60, "st": 0, "bm": 0
    }
  ]
}
```

This is exactly the kind of repetitive structure that benefits from `lottie_builder.py` — a loop over `i in range(3)` produces all three layers without copy-paste error risk.

---

## 3. Checkmark draw-on (trim path)

**Use case**: success confirmation. The classic "checkmark draws itself in" microinteraction.

**Plan**: A V-shaped path with a stroke (no fill). Use a trim path animator to reveal the stroke from 0% to 100% over 20 frames with ease-out timing. Add a subtle scale-in on the entire group to give it presence.

**Principles applied**: Slow in/slow out (ease-out reveal), follow-through (scale-up overshoot, then settle).

```json
{
  "v": "5.12.2", "fr": 60, "ip": 0, "op": 30, "w": 200, "h": 200,
  "nm": "Checkmark Draw", "ddd": 0, "assets": [], "layers": [
    { "ddd": 0, "ind": 1, "ty": 4, "nm": "Check", "sr": 1,
      "ks": {
        "o": { "a": 0, "k": 100 }, "r": { "a": 0, "k": 0 },
        "p": { "a": 0, "k": [100, 100, 0] }, "a": { "a": 0, "k": [0, 0, 0] },
        "s": { "a": 1, "k": [
          { "t": 0,  "s": [0,0,100],     "o":{"x":[0.16,0.16,0.16],"y":[0.85,0.85,0.85]}, "i":{"x":[0.32,0.32,0.32],"y":[1.275,1.275,1.275]} },
          { "t": 20, "s": [110,110,100], "o":{"x":[0.4,0.4,0.4],"y":[0,0,0]}, "i":{"x":[0.6,0.6,0.6],"y":[1,1,1]} },
          { "t": 30, "s": [100,100,100] }
        ]}
      },
      "ao": 0, "shapes": [
        { "ty": "gr", "nm": "Check Shape", "it": [
          { "ty": "sh", "ind": 0, "ks": { "a": 0, "k": {
            "c": false,
            "v": [[-40, 0], [-10, 30], [40, -30]],
            "i": [[0,0], [0,0], [0,0]],
            "o": [[0,0], [0,0], [0,0]]
          }}},
          { "ty": "tm", "s": { "a": 0, "k": 0 },
            "e": { "a": 1, "k": [
              { "t": 2,  "s": [0],   "o": {"x":[0.16],"y":[1]}, "i": {"x":[0.3],"y":[1]} },
              { "t": 22, "s": [100] }
            ]},
            "o": { "a": 0, "k": 0 }, "m": 1
          },
          { "ty": "st",
            "c": { "a": 0, "k": [0.21, 0.91, 0.45, 1] },
            "o": { "a": 0, "k": 100 },
            "w": { "a": 0, "k": 12 },
            "lc": 2, "lj": 2, "ml": 4, "d": []
          },
          { "ty": "tr", "p":{"a":0,"k":[0,0]}, "a":{"a":0,"k":[0,0]}, "s":{"a":0,"k":[100,100]}, "r":{"a":0,"k":0}, "o":{"a":0,"k":100} }
        ]}
      ], "ip": 0, "op": 30, "st": 0, "bm": 0
    }
  ]
}
```

**Key points**:
- The path is `c: false` (open) — it's just the V shape, no fill needed.
- The trim path animates `e` (end percentage) from 0 → 100 with ease-out.
- The trim sits **after** the path in the group's `it` array. Trim affects the path above it.
- Stroke comes after the trim, with `lc: 2` (round caps) so the drawing line has soft ends.

---

## 4. Icon morph between two states

**Use case**: hamburger ↔ X, play ↔ pause, plus ↔ minus.

**Plan**: Two paths with **matching vertex counts** that morph between each other. The play→pause is the classic example.

**Principle**: paths morphing requires identical vertex counts and matched in/out tangents. The renderer interpolates each vertex independently — if vertex counts differ, behavior is undefined.

For a **play triangle ↔ pause bars** morph, both shapes need 4 corner vertices arranged in a way that lets them smoothly interpolate. This is fiddly to write by hand — usually best to construct in After Effects with shape morphing enabled, OR to build the two paths as two separate shape items and crossfade them with opacity instead (simpler and renders identically in most cases).

### Crossfade approach (recommended for hand-authored)

```json
{
  "v": "5.12.2", "fr": 60, "ip": 0, "op": 30, "w": 200, "h": 200,
  "nm": "Play to Pause", "ddd": 0, "assets": [], "layers": [
    { "ddd": 0, "ind": 1, "ty": 4, "nm": "Play",  "sr": 1,
      "ks": {
        "o": { "a": 1, "k": [
          { "t": 0,  "s": [100], "o": {"x":[0.4],"y":[0]}, "i": {"x":[0.6],"y":[1]} },
          { "t": 15, "s": [0] }
        ]},
        "r": { "a": 1, "k": [
          { "t": 0,  "s": [0],   "o":{"x":[0.4],"y":[0]}, "i":{"x":[0.6],"y":[1]} },
          { "t": 15, "s": [90] }
        ]},
        "p": { "a": 0, "k": [100, 100, 0] }, "a": { "a": 0, "k": [0, 0, 0] },
        "s": { "a": 0, "k": [100, 100, 100] }
      },
      "ao": 0, "shapes": [
        { "ty": "gr", "it": [
          { "ty": "sh", "ks": { "a": 0, "k": {
            "c": true,
            "v": [[-25, -30], [25, 0], [-25, 30]],
            "i": [[0,0],[0,0],[0,0]], "o": [[0,0],[0,0],[0,0]]
          }}},
          { "ty": "fl", "c": { "a": 0, "k": [0.95, 0.31, 0.85, 1] }, "o": { "a": 0, "k": 100 }, "r": 1 },
          { "ty": "tr", "p":{"a":0,"k":[0,0]}, "a":{"a":0,"k":[0,0]}, "s":{"a":0,"k":[100,100]}, "r":{"a":0,"k":0}, "o":{"a":0,"k":100} }
        ]}
      ], "ip": 0, "op": 30, "st": 0, "bm": 0
    },
    { "ddd": 0, "ind": 2, "ty": 4, "nm": "Pause", "sr": 1,
      "ks": {
        "o": { "a": 1, "k": [
          { "t": 0,  "s": [0],   "o": {"x":[0.4],"y":[0]}, "i": {"x":[0.6],"y":[1]} },
          { "t": 15, "s": [100] }
        ]},
        "r": { "a": 1, "k": [
          { "t": 0,  "s": [-90], "o":{"x":[0.4],"y":[0]}, "i":{"x":[0.6],"y":[1]} },
          { "t": 15, "s": [0] }
        ]},
        "p": { "a": 0, "k": [100, 100, 0] }, "a": { "a": 0, "k": [0, 0, 0] },
        "s": { "a": 0, "k": [100, 100, 100] }
      },
      "ao": 0, "shapes": [
        { "ty": "gr", "it": [
          { "ty": "rc", "d": 1, "s": { "a": 0, "k": [12, 50] }, "p": { "a": 0, "k": [-12, 0] }, "r": { "a": 0, "k": 2 } },
          { "ty": "rc", "d": 1, "s": { "a": 0, "k": [12, 50] }, "p": { "a": 0, "k": [12, 0] }, "r": { "a": 0, "k": 2 } },
          { "ty": "fl", "c": { "a": 0, "k": [0.95, 0.31, 0.85, 1] }, "o": { "a": 0, "k": 100 }, "r": 1 },
          { "ty": "tr", "p":{"a":0,"k":[0,0]}, "a":{"a":0,"k":[0,0]}, "s":{"a":0,"k":[100,100]}, "r":{"a":0,"k":0}, "o":{"a":0,"k":100} }
        ]}
      ], "ip": 0, "op": 30, "st": 0, "bm": 0
    }
  ]
}
```

The play layer fades out + rotates from 0° → 90°. The pause layer fades in + rotates from -90° → 0°. Both happen simultaneously, producing a unified "morph through rotation" effect that reads as a single shape transforming.

This trick — crossfade with synchronized rotation — is the workhorse for state-toggle icon morphs because it's robust across all renderers and easy to author.

---

## 5. Logo wordmark assembly

**Use case**: hero animation for brand intros. Letters assemble from off-screen with staggered timing.

**Plan**: Each letter is its own shape layer with the same baseline Y. Each letter slides up from 40px below its final position while fading in. Stagger by 3–5 frames between letters. Letters use ease-out-back for subtle landing overshoot.

**Principles applied**: Anticipation (the overshoot during landing), overlapping action (the stagger), exaggeration (the overshoot magnitude), staging (letters assemble left-to-right so the eye follows).

This pattern is **strongly recommended for the programmatic Python builder** — hand-authoring 10+ letter layers is error-prone. The pseudo-code:

```python
letters = "ANIVECT"
spacing = 60
start_x = 256 - (len(letters) - 1) * spacing / 2

for i, letter in enumerate(letters):
    delay = i * 4  # 4-frame stagger between letters
    layer = ShapeLayer(
        name=f"letter_{letter}",
        shapes=[text_path_for(letter)],
        transform=Transform(
            position=keyframes([
                (delay,      [start_x + i * spacing, 140], ease.OUT_BACK),
                (delay + 24, [start_x + i * spacing, 100]),
            ]),
            opacity=keyframes([
                (delay,      [0], ease.OUT_CUBIC),
                (delay + 18, [100]),
            ]),
        ),
    )
    anim.add_layer(layer)
```

Total duration is `(len(letters) - 1) * 4 + 24 + buffer ≈ (n*4 + 30)` frames.

For a 7-letter wordmark at 60fps with 4-frame stagger and 24-frame per-letter animation: 7*4 + 24 = 52 frames ≈ 0.87 seconds. Add 30 frames of held-state at the end before any outro motion.

---

## 6. Spinner with trailing arc

**Use case**: indeterminate progress, "still working" indicator.

**Plan**: A stroked arc (270° of a circle) that rotates continuously. Combined with a trim path that animates the start and end positions, producing the "snake" effect of a Material spinner.

**Principles applied**: Continuous loop (linear easing is acceptable here), repetition, hypnotic predictable timing.

This is one of the few cases where **linear easing on rotation is correct** — the spinner should rotate at constant angular velocity. The trim animation, however, eases in/out as the arc grows and shrinks.

```json
{
  "v": "5.12.2", "fr": 60, "ip": 0, "op": 120, "w": 200, "h": 200,
  "nm": "Snake Spinner", "ddd": 0, "assets": [], "layers": [
    { "ddd": 0, "ind": 1, "ty": 4, "nm": "Arc", "sr": 1,
      "ks": {
        "o": { "a": 0, "k": 100 },
        "r": { "a": 1, "k": [
          { "t": 0,   "s": [0],   "o": {"x":[1],"y":[1]}, "i": {"x":[0],"y":[0]} },
          { "t": 120, "s": [360] }
        ]},
        "p": { "a": 0, "k": [100, 100, 0] }, "a": { "a": 0, "k": [0, 0, 0] },
        "s": { "a": 0, "k": [100, 100, 100] }
      },
      "ao": 0, "shapes": [
        { "ty": "gr", "it": [
          { "ty": "el", "d": 1, "s": { "a": 0, "k": [60, 60] }, "p": { "a": 0, "k": [0, 0] } },
          { "ty": "tm",
            "s": { "a": 1, "k": [
              { "t": 0,  "s": [0],  "o":{"x":[0.4],"y":[0]}, "i":{"x":[0.6],"y":[1]} },
              { "t": 60, "s": [75], "o":{"x":[0.4],"y":[0]}, "i":{"x":[0.6],"y":[1]} },
              { "t": 120,"s": [100] }
            ]},
            "e": { "a": 1, "k": [
              { "t": 0,  "s": [25], "o":{"x":[0.4],"y":[0]}, "i":{"x":[0.6],"y":[1]} },
              { "t": 60, "s": [100],"o":{"x":[0.4],"y":[0]}, "i":{"x":[0.6],"y":[1]} },
              { "t": 120,"s": [100] }
            ]},
            "o": { "a": 0, "k": 0 }, "m": 1
          },
          { "ty": "st",
            "c": { "a": 0, "k": [0.95, 0.31, 0.85, 1] },
            "o": { "a": 0, "k": 100 },
            "w": { "a": 0, "k": 6 },
            "lc": 2, "lj": 2, "ml": 4, "d": []
          },
          { "ty": "tr", "p":{"a":0,"k":[0,0]}, "a":{"a":0,"k":[0,0]}, "s":{"a":0,"k":[100,100]}, "r":{"a":0,"k":0}, "o":{"a":0,"k":100} }
        ]}
      ], "ip": 0, "op": 120, "st": 0, "bm": 0
    }
  ]
}
```

---

## 7. Notification bell shake

**Use case**: drawing attention to a notification badge or alert icon.

**Plan**: Quick rotational shake — rotate +12° → -12° → +8° → -8° → +4° → 0° over ~30 frames. Each oscillation diminishes by ~30% (classic damped oscillation feel). Easing on each segment is ease-out.

**Principles applied**: Damped oscillation (follow-through), exaggeration (the first swing is the largest), anticipation absent intentionally (this is a *reaction*, not a planned move).

Set the anchor at the **top** of the bell (where the hanger attaches) so it pivots correctly:

```json
"ks": {
  "p": { "a": 0, "k": [100, 100, 0] },
  "a": { "a": 0, "k": [0, -40, 0] },
  "r": { "a": 1, "k": [
    { "t": 0,  "s": [0],   "o": {"x":[0.16],"y":[1]}, "i": {"x":[0.3],"y":[1]} },
    { "t": 5,  "s": [12],  "o": {"x":[0.16],"y":[1]}, "i": {"x":[0.3],"y":[1]} },
    { "t": 10, "s": [-12], "o": {"x":[0.16],"y":[1]}, "i": {"x":[0.3],"y":[1]} },
    { "t": 15, "s": [8],   "o": {"x":[0.16],"y":[1]}, "i": {"x":[0.3],"y":[1]} },
    { "t": 20, "s": [-8],  "o": {"x":[0.16],"y":[1]}, "i": {"x":[0.3],"y":[1]} },
    { "t": 25, "s": [4],   "o": {"x":[0.16],"y":[1]}, "i": {"x":[0.3],"y":[1]} },
    { "t": 30, "s": [0] }
  ]}
}
```

Anchor at `[0, -40]` means rotation pivots 40px above the layer's position — i.e., at the top of a bell that's drawn centered. Adjust to match your actual bell geometry.

---

## 8. Progress ring fill

**Use case**: determinate progress indicator (download progress, video progress, percentage complete).

**Plan**: A stroked ring with a trim path that animates `e` from 0 → 100 based on progress. The ring rotates -90° on its anchor so that the trim starts from "12 o'clock" (top) rather than "3 o'clock" (right, the default for circle paths).

```json
{
  "v": "5.12.2", "fr": 60, "ip": 0, "op": 60, "w": 200, "h": 200,
  "nm": "Progress Ring", "ddd": 0, "assets": [], "layers": [
    { "ddd": 0, "ind": 1, "ty": 4, "nm": "Ring", "sr": 1,
      "ks": {
        "o": { "a": 0, "k": 100 },
        "r": { "a": 0, "k": -90 },
        "p": { "a": 0, "k": [100, 100, 0] }, "a": { "a": 0, "k": [0, 0, 0] },
        "s": { "a": 0, "k": [100, 100, 100] }
      },
      "ao": 0, "shapes": [
        { "ty": "gr", "it": [
          { "ty": "el", "d": 1, "s": { "a": 0, "k": [120, 120] }, "p": { "a": 0, "k": [0, 0] } },
          { "ty": "tm",
            "s": { "a": 0, "k": 0 },
            "e": { "a": 1, "k": [
              { "t": 0,  "s": [0],   "o": {"x":[0.4],"y":[0]}, "i": {"x":[0.2],"y":[1]} },
              { "t": 60, "s": [100] }
            ]},
            "o": { "a": 0, "k": 0 }, "m": 1
          },
          { "ty": "st",
            "c": { "a": 0, "k": [0.16, 0.78, 0.45, 1] },
            "o": { "a": 0, "k": 100 },
            "w": { "a": 0, "k": 10 },
            "lc": 2, "lj": 2, "ml": 4, "d": []
          },
          { "ty": "tr", "p":{"a":0,"k":[0,0]}, "a":{"a":0,"k":[0,0]}, "s":{"a":0,"k":[100,100]}, "r":{"a":0,"k":0}, "o":{"a":0,"k":100} }
        ]}
      ], "ip": 0, "op": 60, "st": 0, "bm": 0
    }
  ]
}
```

For a **live progress** indicator (driven by actual download progress), don't animate `e` in the JSON — leave it static at `0`, expose the property via the renderer's API, and update it from the host application based on real progress data.

---

## Patterns checklist

When picking a pattern for a new request:

| User says... | Pattern to start from |
|---|---|
| "Loading spinner", "thinking indicator" | Pulsing dot or Snake spinner |
| "Typing indicator", "chat dots" | Three-dot staggered |
| "Success animation", "completed" | Checkmark draw-on |
| "Toggle icon", "play/pause", "menu/close" | Icon morph (crossfade approach) |
| "Logo animation", "brand reveal", "intro" | Wordmark assembly |
| "Progress indicator with percentage" | Progress ring fill |
| "Notification badge", "alert" | Bell shake |
| "Hero animation", "splash screen" | Wordmark + secondary elements |

For anything not covered here, the principles in [`principles.md`](principles.md) apply — pick the closest pattern, adapt the timing, and use easing presets from [`easing.md`](easing.md).
