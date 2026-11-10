# Animation Principles for Lottie

The 12 principles from Disney's *Illusion of Life* are the canonical foundation for animation. Most of them translate directly to Lottie. This file maps each principle to specific Lottie techniques and shows what to actually change in the JSON to apply it.

If you only read three sections, read **Easing (Slow In/Slow Out)**, **Anticipation**, and **Follow-Through & Overlapping Action**. These are the highest-leverage on motion graphics.

## Table of contents

1. [Squash and stretch](#1-squash-and-stretch)
2. [Anticipation](#2-anticipation)
3. [Staging](#3-staging)
4. [Pose to pose](#4-pose-to-pose)
5. [Follow-through and overlapping action](#5-follow-through-and-overlapping-action)
6. [Slow in and slow out](#6-slow-in-and-slow-out-easing)
7. [Arcs](#7-arcs)
8. [Secondary action](#8-secondary-action)
9. [Timing](#9-timing)
10. [Exaggeration](#10-exaggeration)
11. [Solid drawing](#11-solid-drawing)
12. [Appeal](#12-appeal)

---

## 1. Squash and stretch

Living things deform under force. A bouncing ball squashes on impact and stretches mid-flight. In motion graphics, even abstract shapes feel alive when they deform slightly.

### Lottie technique

Animate the scale **non-uniformly** — independently on X and Y. A circle that lands on the ground:

```
frame 0:  scale = [100, 100]   (falling)
frame 8:  scale = [115, 85]    (impact — squash)
frame 14: scale = [95, 105]    (rebound — stretch)
frame 20: scale = [100, 100]   (settle)
```

For 2D scale, this is `s` in the layer transform or group transform. Make sure your anchor is at the bottom of the shape if you want the squash to "ground" properly — otherwise the shape will appear to compress around its center.

### When to use

- Buttons being pressed (slight squash on tap)
- Logos animating in (subtle stretch as they land)
- Anywhere you want the animation to feel organic rather than mechanical

### When NOT to use

- Static UI elements (rulers, dividers, etc.) — squash on these reads as bug, not feature
- Text — squashing text is almost always a mistake unless very subtle and intentional

## 2. Anticipation

Before a big action, briefly move in the opposite direction. A character about to jump crouches first. A wind-up before a throw. In Lottie this is 4–8 frames of counter-motion before the primary motion.

### Lottie technique

For a scale-in:

```
frame 0:  scale = [100, 100]
frame 4:  scale = [92, 92]      ← anticipation crouch
frame 18: scale = [115, 115]    ← main action with overshoot
frame 28: scale = [100, 100]    ← settle
```

For a slide-right entrance:

```
frame 0:  position.x = -120
frame 6:  position.x = -135     ← anticipation: slide further left first
frame 24: position.x = 280      ← main slide-in
```

The counter-motion should be **smaller and slower** than the main motion. Roughly 10–15% the magnitude, ~30% the time.

### When to use

- Any "hero" entrance (logo reveal, modal appearance)
- Button responses to important actions (submit, save)
- Character animations (always)

### When NOT to use

- Loops (anticipation only reads on first play)
- Subtle background animations (don't draw attention here)
- Strict utility microinteractions (a loading spinner doesn't anticipate)

## 3. Staging

Every animation should have a single clear focal point at any given moment. Multiple things competing for attention dilutes the message.

### Lottie technique

Sequence — don't synchronize — multiple animated elements. If you have a logo + tagline + CTA button, animate them in series:

```
frame 0–24:  logo enters (hero motion)
frame 18–36: tagline fades in (overlaps logo's settle)
frame 30–48: button slides up (overlaps tagline)
```

Use opacity, scale, and motion to control which element pulls focus at each moment. A subtle pulse on a CTA button after everything else has settled is good staging — the button is now the focus.

### How to implement

- Stagger layer in-points (`ip` field)
- Use offset keyframe times within each layer's animation
- Hold attention with subtle secondary motion on the current focal element

## 4. Pose to pose

In hand-drawn animation, this is the distinction between drawing key poses first then filling in between, versus drawing every frame in sequence. Lottie is **inherently pose-to-pose** — you define keyframes and the renderer interpolates.

The principle still applies in how you design the animation: identify the 2–4 key poses (start, anticipation, peak, settle) and place keyframes there. Don't add intermediate keyframes unless the easing is genuinely insufficient to interpolate naturally between them.

### Anti-pattern

A scale animation with 12 keyframes between value 0 and value 100, all linear, trying to manually create an ease curve. Use 2 keyframes with proper easing tangents instead.

## 5. Follow-through and overlapping action

When something stops moving, parts of it continue briefly. A flag whips after the pole stops. A character's coat tail lags their motion. Different elements move at different rates, overlapping in time.

This is **the** principle that separates polished motion graphics from amateur. Almost every animation gets better when you apply it.

### Lottie technique

#### Overlapping action (multiple elements)

Stagger the keyframe times of sibling elements by 3–8 frames:

```
dot_0: scales up frames 0–18
dot_1: scales up frames 3–21
dot_2: scales up frames 6–24
dot_3: scales up frames 9–27
```

The result feels like a wave rather than a synchronized snap.

#### Follow-through (single element with parts)

If you have a shape with multiple components — say, a logo with a "main mark" and a "tagline" — animate the tagline 4–8 frames *behind* the main mark, so it appears to "catch up" or "trail" the primary motion.

#### Follow-through within a single property

Add a small overshoot at the end of a motion, settling 4–8 frames after the apparent end:

```
frame 0:  scale = [0, 0]
frame 20: scale = [110, 110]   ← overshoot
frame 28: scale = [97, 97]     ← undershoot
frame 36: scale = [100, 100]   ← final settle
```

The motion *appears* to land at frame 20, but actually settles at frame 36. This is what makes things feel "alive" rather than "stamped down".

## 6. Slow in and slow out (easing)

Motion in nature accelerates and decelerates — never instant constant velocity. Easing curves model this. Linear interpolation in Lottie is the dead giveaway of generated-without-thought animation.

### Lottie technique

See [`easing.md`](easing.md) for the full reference. Quick rules:

- **Entrances**: ease-out (object starts fast, decelerates into position)
- **Exits**: ease-in (object starts slow, accelerates away)
- **Between two static states**: ease-in-out
- **Continuous loops**: linear is acceptable (rotation, pulsing)

### Diagnosing missing easing

If an animation feels stiff or robotic and you can't put your finger on why, 90% of the time it's missing or wrong easing. Open the JSON and look for keyframes that have no `i`/`o` tangents, or where tangents are linear (`o: {x: [1], y: [1]}`, `i: {x: [0], y: [0]}`).

Run `validate_lottie.py` — it warns when a property has only linear easing.

## 7. Arcs

Natural motion follows curved paths, not straight lines. A thrown ball arcs. A swinging arm sweeps. Motion in straight lines reads as mechanical.

### Lottie technique

When animating position between two non-aligned points, instead of using two keyframes with eased timing (which produces a straight-line motion with eased speed), use three keyframes with a midpoint offset perpendicular to the direct path:

```
frame 0:  position = [100, 400]
frame 15: position = [256, 320]    ← arc apex (above the straight line)
frame 30: position = [412, 400]
```

For position properties, you can also use spatial tangents (`ti` and `to` on position keyframes) to make the motion path itself curve — but this is fiddly to write by hand. The midpoint-keyframe approach is more reliable.

### When NOT to use

- UI elements that should move along grid axes (a sliding panel, a slide-up modal)
- Purely vertical or horizontal motion (already on an axis)

## 8. Secondary action

Supporting motion that reinforces but doesn't compete with the primary action. A walking character's arms swing. A face shows expression while the body moves. In motion graphics, secondary action keeps the focal element from feeling static during long primary motions.

### Lottie technique

During a long primary animation (e.g., a logo sliding in over 24 frames), add a subtle secondary animation that reads as supporting:

- Slight opacity pulse on the logo's drop shadow
- Slow rotation of a decorative element behind it
- A glow that intensifies as the logo settles

The secondary action should be **subtler** in amplitude and **slower** in tempo than the primary, so it adds richness without distracting.

## 9. Timing

The number of frames between keyframes determines the perceived speed and weight of motion. Fast = light/snappy. Slow = heavy/deliberate.

### Lottie timing references (at 60fps)

| Motion type | Frames |
|---|---|
| UI microinteraction (button tap response) | 8–16 |
| Standard transition (entrance, exit) | 18–30 |
| Hero animation (logo reveal) | 30–60 |
| Loop cycle (loader, idle) | 60–120 |
| Long-form motion graphics | 120+ |

### Frame rate choice

- **60fps**: smoothest motion, larger file size, all modern renderers handle it.
- **30fps**: smaller file, looks fine for most UI animation, "video-like" feel.
- **24fps**: cinematic feel, deliberate frame steps. Use for character/illustrative animation.

If you import an existing Lottie at one fps and add new keyframes, **keep the existing fps**. Adding 60fps keyframes to a 30fps composition causes timing math to break.

## 10. Exaggeration

Push past realism for impact. A character "stretches" beyond what bones allow. A logo "lands" with more squash than physics would dictate. The exaggeration sells the action.

### Lottie technique

This shows up as:
- **Larger overshoots than realistic** in scale/position settles (115% peak before settling to 100%, not 102%)
- **Stronger easing curves** (cubic or quart out rather than ease)
- **More dramatic anticipation** (8 frames of pre-motion, not 2)

Don't go past the point where it reads as broken — but most generated animations err far in the conservative direction. If your animation feels timid, the fix is usually more exaggeration, not less.

## 11. Solid drawing

In hand-drawn animation, this means understanding 3D form so characters don't go flat. In Lottie this translates to:

- **Consistent volume**: when you scale, scale uniformly unless intentionally squashing.
- **Proper anchor points**: rotations and scales should pivot from sensible points (centers for symmetric shapes, base for grounded things).
- **No accidental skew**: a shape that's supposed to rotate around its center shouldn't accidentally drift due to anchor offset.

These show up as: scaling and rotation that feels "right" rather than vaguely wrong-looking. See [SKILL.md § Correct anchor points](../SKILL.md#2-correct-anchor-points).

## 12. Appeal

Design quality. Color choices, shape language, composition. This is the hardest to automate but the most important to consider.

For Lottie specifically:

- **Color palettes**: stick to 3–5 colors max. Use color theory (analogous, complementary, triadic).
- **Shape language consistency**: don't mix harsh angular shapes with soft rounded ones unless the contrast is intentional.
- **Negative space**: don't fill the entire canvas. Compositions need breathing room.
- **Motion personality**: aggressive bouncy motion vs. smooth elegant motion vs. snappy precise motion — pick one and stick with it for the whole animation.

If the user gives you a brand reference, mirror its visual language in the animation's color, timing, and easing personality. A "neon glassmorphism" brand should have ease-out-back entrances with subtle overshoot and glow secondary animations. A "corporate minimal" brand should have material-standard easings and no overshoot.

---

## Applying the principles: a quick mental checklist

Before declaring an animation done, ask:

1. **Is there easing on every meaningful keyframe?** (Slow in/slow out)
2. **Does any hero motion have anticipation?** (Anticipation)
3. **Are sibling elements staggered, not synchronized?** (Overlapping action)
4. **Is there a clear focal point at every moment?** (Staging)
5. **Do entrances overshoot and settle, rather than stamping flat?** (Follow-through)
6. **Are arcs used where motion isn't axis-aligned?** (Arcs)
7. **Is there subtle secondary motion during long primary motions?** (Secondary action)
8. **Does the timing match the intended feel** (snappy/heavy/elegant)? (Timing)

If you can answer "yes" to 5+ of these, the animation will read as polished. If you can answer "yes" to all 8, you have professional-grade work.
