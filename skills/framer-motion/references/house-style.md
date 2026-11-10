# House Style — Opinionated Defaults

This is the opinionated layer. The foundation references (`design-principles.md`, `motion-react.md`, `reanimated.md`) teach the tools. This file is "what to do when no one asked, on StewMore-flavored projects." Use these as starting points; override per-component when intent calls for it.

The style summary: **confident but not loud, springy but not bouncy, fast but not jittery.** Suited for design-driven product UI with glassmorphism, soft neon accents, and a sense of polish without theatrics.

## Table of contents

1. The StewMore preset
2. Spring presets
3. Tween curves
4. Choreography defaults
5. Reduced motion overrides
6. Glassmorphism & neon interactions
7. Token-friendly configuration
8. Anti-patterns to avoid

---

## 1. The StewMore preset

Drop this at the top of any project as the baseline. Override per-component when motion needs to express something specific.

```ts
// motion-presets.ts
export const motionPresets = {
  // Springs — for anything moving (translate, scale, rotate)
  spring: {
    snappy:    { type: "spring", stiffness: 420, damping: 30, mass: 0.8 } as const,
    confident: { type: "spring", stiffness: 260, damping: 28, mass: 0.9 } as const,
    gentle:    { type: "spring", stiffness: 180, damping: 26, mass: 1.0 } as const,
    floaty:    { type: "spring", stiffness: 140, damping: 22, mass: 1.0 } as const,
  },

  // Tweens — for fades, color shifts, blur, anything non-positional
  tween: {
    instant:   { duration: 0.12, ease: [0.32, 0.72, 0, 1] as const } as const,
    standard:  { duration: 0.24, ease: [0.32, 0.72, 0, 1] as const } as const,
    deliberate:{ duration: 0.4,  ease: [0.32, 0.72, 0, 1] as const } as const,
    soft:      { duration: 0.6,  ease: [0.4, 0, 0.2, 1] as const } as const,
  },

  // Stagger
  stagger: {
    tight:  { staggerChildren: 0.04, delayChildren: 0.02 },
    normal: { staggerChildren: 0.06, delayChildren: 0.04 },
    loose:  { staggerChildren: 0.1,  delayChildren: 0.05 },
  },
};
```

Usage:

```tsx
import { motion } from "motion/react";
import { motionPresets as m } from "@/lib/motion-presets";

<motion.div
  initial={{ opacity: 0, y: 12 }}
  animate={{ opacity: 1, y: 0 }}
  transition={m.spring.confident}
/>
```

## 2. Spring presets — when to use which

**`snappy`** — anything tap-driven. Button press, toggle, hover state. The user did something and the UI is responding instantly.

**`confident`** — the default. Modal enter, drawer slide, card transitions, magic move. 90% of moves want this.

**`gentle`** — large moves where you want the user to track the motion. Page transitions, full-screen hero reveals, shared element transitions across significant distance.

**`floaty`** — special-purpose only. Decorative reveals (logo entrance, splash sequences). Rare, and never on functional UI — too slow for that.

**Custom on demand.** The presets are starting points, not commandments. If a specific component reads wrong with `confident`, dial it up or down. Document the override with a comment so it doesn't look like a typo.

## 3. Tween curves — when to use which

**`instant`** (120ms) — hover state changes, focus rings, tap feedback. Anything that should feel like a state change rather than a transition.

**`standard`** (240ms) — most fades, color shifts, opacity-only transitions. The default tween.

**`deliberate`** (400ms) — full-screen fades, backdrop appearance, modal background opacity, larger crossfades.

**`soft`** (600ms) — image reveals, hero crossfades, anything where the slowness is part of the effect. Uses Material's standard curve because the soft-confident curve gets too gentle at this duration.

### The "soft confident" curve

`cubic-bezier(0.32, 0.72, 0, 1)` is used in `instant`, `standard`, and `deliberate`. It's a fast-launch, gentle-settle curve — feels assured and polished without being aggressive. This is the curve that reads as "design-driven product" rather than "default browser transition."

## 4. Choreography defaults

When animating multiple things together, default to these:

**Lists** (table rows, cards in a grid, items in a sidebar):
- `staggerChildren: 0.06` — 60ms between siblings
- `delayChildren: 0.04` — small lead-in so the parent moves first
- Per-item duration: spring `confident`
- Per-item motion: opacity + 12–16px Y translate

**Featured sequences** (hero + subhead + CTA, multi-step reveals):
- `staggerChildren: 0.08–0.12` — slightly longer, each element gets its moment
- `delayChildren: 0.05`
- Per-item: spring `gentle` for the hero, `confident` for everything else

**Tight clusters** (icon + label, avatar + name):
- Don't stagger. They're one thing.
- Animate as a single unit.

**Page-level reveals**:
- Top-to-bottom stagger by default
- Header in `gentle`, body content `confident`, CTA last

## 5. Reduced motion overrides

When `useReducedMotion()` returns true:

```ts
const reduce = useReducedMotion();

const transition = reduce
  ? { duration: 0.12, ease: "linear" }
  : motionPresets.spring.confident;

const variants = reduce
  ? { hidden: { opacity: 0 }, show: { opacity: 1 } }
  : { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };
```

Reduced motion rules in this house style:
- Replace all translate/scale/rotate with opacity transitions
- Cut durations to **120ms** universally (no need for spring-length durations when nothing's moving)
- Disable all stagger
- Replace parallax with static backgrounds
- Disable infinite/pulse animations entirely
- Keep magic-move *position* but skip the *scale curve* (instant snap to new size, animate position only)

Wrap your app once with `<MotionConfig reducedMotion="user">` and let the OS setting drive globally. Then override per-component for cases that need explicit reduced-motion handling beyond the global default.

## 6. Glassmorphism & neon interactions

These patterns are specific to design-driven UI with frosted-glass surfaces and accent glows. They look generic without these details and great with them.

### Layer hover-lift on glass

When a glass card lifts on hover, the lift needs to *feel* like it's leaving the surface, not just translating. A spring with slight overshoot helps:

```ts
{
  type: "spring",
  stiffness: 320,
  damping: 22,   // slightly lower damping = ~3% overshoot
  mass: 0.9,
}
```

Combine with a shadow that grows as the card lifts:

```tsx
<motion.div
  whileHover={{
    y: -6,
    boxShadow: "0 24px 48px -12px rgb(0 0 0 / 0.35), 0 0 0 1px rgb(255 255 255 / 0.1)",
  }}
  transition={{ type: "spring", stiffness: 320, damping: 22, mass: 0.9 }}
/>
```

### Backdrop-filter blur animation

Animating `backdropFilter` works in Motion but has performance caveats. Default to animating the underlying background opacity instead and only animate blur when the user has explicitly opted in or it's a featured moment.

```tsx
// Reliable across browsers:
<motion.div
  initial={{ backgroundColor: "rgb(15 23 42 / 0)" }}
  animate={{ backgroundColor: "rgb(15 23 42 / 0.6)" }}
  transition={{ duration: 0.3 }}
  style={{ backdropFilter: "blur(20px)" }}  // static, applied via CSS
/>

// When you specifically want the blur to fade in:
<motion.div
  initial={{ backdropFilter: "blur(0px)" }}
  animate={{ backdropFilter: "blur(20px)" }}
  transition={{ duration: 0.4, ease: [0.32, 0.72, 0, 1] }}
/>
```

### Neon glow on focus or hover

For accent glows on interactive elements:

```tsx
<motion.button
  className="relative"
  whileHover={{
    boxShadow: "0 0 0 1px rgb(34 211 238 / 0.5), 0 0 24px rgb(34 211 238 / 0.4)",
  }}
  whileTap={{
    boxShadow: "0 0 0 2px rgb(34 211 238 / 0.8), 0 0 32px rgb(34 211 238 / 0.6)",
  }}
  transition={{ duration: 0.15 }}
>
  {children}
</motion.button>
```

The two-stage shadow (inner 1px ring + outer glow) is what gives neon its convincing look. Don't try to do this with a single shadow.

### Animated gradient borders

A common StewMore pattern — a glass card with an animated gradient edge:

```tsx
<motion.div
  className="relative rounded-2xl p-[1px] overflow-hidden"
  style={{
    background: "linear-gradient(var(--gradient-angle), #22d3ee, #8b5cf6, #22d3ee)",
  }}
  animate={{ "--gradient-angle": ["0deg", "360deg"] } as any}
  transition={{ duration: 6, ease: "linear", repeat: Infinity }}
>
  <div className="rounded-2xl bg-card/80 backdrop-blur-xl p-6">
    {children}
  </div>
</motion.div>
```

The `--gradient-angle` CSS variable is animated via Motion. Requires `@property` declaration in CSS for older browsers to interpolate correctly:

```css
@property --gradient-angle {
  syntax: "<angle>";
  initial-value: 0deg;
  inherits: false;
}
```

## 7. Token-friendly configuration

For projects using design tokens (Tailwind theme, Radix tokens, custom design system), wire animation tokens the same way:

```ts
// tokens/motion.ts
export const motion = {
  duration: {
    instant: "120ms",
    fast: "200ms",
    standard: "240ms",
    deliberate: "400ms",
    soft: "600ms",
  },
  ease: {
    soft: [0.32, 0.72, 0, 1] as const,
    material: [0.4, 0, 0.2, 1] as const,
    out: [0, 0, 0.2, 1] as const,
    in: [0.4, 0, 1, 1] as const,
  },
  spring: {
    snappy: { stiffness: 420, damping: 30, mass: 0.8 },
    confident: { stiffness: 260, damping: 28, mass: 0.9 },
    gentle: { stiffness: 180, damping: 26, mass: 1.0 },
  },
  stagger: {
    tight: 0.04,
    normal: 0.06,
    loose: 0.1,
  },
};
```

Then in Tailwind config, expose the durations and curves as utilities so CSS-driven transitions match:

```ts
// tailwind.config.ts
theme: {
  extend: {
    transitionDuration: {
      instant: "120ms",
      fast: "200ms",
      standard: "240ms",
      deliberate: "400ms",
      soft: "600ms",
    },
    transitionTimingFunction: {
      soft: "cubic-bezier(0.32, 0.72, 0, 1)",
      material: "cubic-bezier(0.4, 0, 0.2, 1)",
    },
  },
},
```

Now any CSS transition (`transition-standard ease-soft`) and any Motion config share the same source of truth. This is the single biggest "looks designed" upgrade for a codebase.

## 8. Anti-patterns to avoid

Common patterns that look fine in isolation but degrade the overall feel:

**Default Motion springs everywhere.** Motion's defaults are tuned for general use; they're slightly bouncier than ideal for design-driven product UI. Use the `confident` preset as your default.

**`ease-in-out` on everything.** It's the lazy choice. Use `ease-out` for entering and `ease-in` for exiting; reserve `ease-in-out` for genuine round trips.

**Long durations on small moves.** A 400ms hover state feels broken. Hover transitions should be 120–180ms.

**No stagger on lists.** Lists where all items appear at the same instant look like a hard cut. Always stagger.

**Decorative parallax.** Subtle parallax (~30%) on hero images is fine. Parallax on every section of the page makes the user feel motion-sick and signals "designer who just discovered scroll triggers."

**Backdrop-filter blur on every glass surface during scroll.** Performance death. Apply blur statically; animate background opacity to suggest the blur effect intensifying.

**Auto-play loops without an off switch.** Pulses, spinning rings, animated gradients — fine in moderation, never more than one per visible region, and always disabled under reduced motion.

**Spring `damping` below 12.** Anything below 12 oscillates more than a polished UI ever should. If you want playfulness, use `damping: 14–18` with higher `stiffness`. The result is "responsive and energetic" rather than "wobbly toy."

**Animating `width`/`height` instead of `transform: scale`.** Layout-triggering properties drop frames. Use `scaleX`/`scaleY` with adjusted `transformOrigin` instead, then either accept the slight visual difference or pair with `layout` if you need true layout-aware sizing.

**Reduced-motion as an afterthought.** Don't write the motion-rich version first and then add a `useReducedMotion` patch at the end. Design the reduced-motion version as a parallel baseline — it forces clarity about what each animation is *for*.
