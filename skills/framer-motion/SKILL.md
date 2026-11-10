---
name: framer-motion
description: Build, refine, or debug animations in any React or React Native codebase. Triggers on Framer Motion, Motion, motion/react, AnimatePresence, layout animations, magic move, shared element transitions, variants, useScroll, useTransform, useMotionValue, React Native Reanimated, react-native-worklets, useSharedValue, useAnimatedStyle, withSpring, withTiming, gesture handlers, microinteractions, hover/tap states, page or route transitions, scroll-linked animations, parallax, reveal-on-scroll, drag-to-reorder, list animations, SVG path animation, animated icons, choreography, stagger, easing, springs, prefers-reduced-motion, useReducedMotion, or any time a UI element on a React surface needs to move smoothly. Use this whenever the user is touching animation code in React or React Native, asks for help making something feel polished, debugs why an animation looks off, or wants to decide between Motion, CSS, and Reanimated — even if they don't name a specific library.
---

# Motion Design for React & React Native

This skill is for building animations in React (web) and React Native that feel intentional and polished. It covers two libraries plus the design discipline that ties them together:

- **Motion** (formerly Framer Motion) — for React on the web. Package: `motion`, import from `motion/react`. Current major: 12.
- **React Native Reanimated** — for React Native. Current major: 4, requires the New Architecture, ships worklets as a separate `react-native-worklets` package.

Both have similar conceptual models (declarative animation, gesture-driven state, layout magic) but very different APIs. This file gives the mental models and decision rules. Deep API surface, copy-paste recipes, and design theory live in `references/`. **Read the matching reference file before writing real code on a task** — the references prevent the most common rework patterns.

## Library state of play (2026)

Two things to internalize before writing any code:

1. **Framer Motion → Motion.** The library was renamed when it became an independent project in 2025. The package on npm is `motion`, and React imports come from `motion/react`. The old `framer-motion` package still works as an alias, so don't aggressively rewrite imports in existing code unless asked. New files should use `motion/react`.

2. **Reanimated 4 split out worklets.** On Reanimated 4+, `react-native-worklets` is a peer dependency and the Babel plugin is `react-native-worklets/plugin` (not `react-native-reanimated/plugin`). Reanimated 4 requires the New Architecture (default in RN 0.76+, mandatory after RN 0.82). Apps still on old arch are stuck on Reanimated 3. Several APIs were renamed in v4: `useScrollViewOffset` → `useScrollOffset`, `executeOnUIRuntimeSync` → `runOnUISync` (from `react-native-worklets`), and `useAnimatedGestureHandler` was removed in favor of Gesture Handler 2's `Gesture` API.

When a task touches one of these libraries, open the corresponding reference once:
- `references/motion-react.md` — Motion for React (web)
- `references/reanimated.md` — Reanimated 4 + Gesture Handler 2

## When to reach for what

Animation decisions split along three axes: **platform**, **interaction model**, and **complexity**. Use this as a starting point, not a rule.

**Pure web, small effect** (hover, focus, a single two-state transition with no gesture chain): plain CSS transitions are often enough. Don't reach for Motion just to fade-in a button.

**Web, anything choreographed** (multiple elements coordinated, enter/exit, gesture-driven, scroll-linked, layout magic, shared elements): Motion. CSS can't compose these cleanly.

**Web, scroll-driven hero / parallax / scroll-progress UI**: Motion's `useScroll` + `useTransform`. CSS scroll-driven animations are landing in browsers but coverage is uneven — Motion's JS implementation is more reliable across targets today.

**Native, anything beyond `LayoutAnimation.configureNext()`**: Reanimated. The legacy `Animated` API runs on the JS thread by default and drops frames the moment anything contentious happens. Reanimated worklets run on the UI thread.

**Native, gestures**: Reanimated + Gesture Handler 2. The two are designed together — every gesture callback is a worklet, so it can write shared values without crossing threads.

**Native, layout / entering / exiting**: Reanimated's layout animations (`FadeIn`, `SlideInDown`, `Layout.springify()`). Far better than `LayoutAnimation`.

**Either platform, "should I animate this at all?"** — see `references/design-principles.md`. Animation directs attention, signals causation, and softens change. Animation as decoration is noise.

## Motion for React — core mental model

Motion's API is built on five primitives. Once these click, the rest is composition.

**1. `motion.*` components.** Every HTML and SVG element has a `motion` counterpart that accepts animation props: `<motion.div>`, `<motion.button>`, `<motion.path>`. For any other component (e.g. shadcn primitives that forward refs), wrap it: `const MotionCard = motion.create(Card)`.

**2. The four animation props.** `initial`, `animate`, `exit`, and `transition`. The first three are *target states* — where to start, where to land, where to leave to. `transition` defines *how* the move happens: type, duration, ease, stiffness, damping. Defaults to a snappy spring.

```tsx
<motion.div
  initial={{ opacity: 0, y: 8 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, y: -8 }}
  transition={{ type: "spring", stiffness: 300, damping: 30 }}
/>
```

**3. Variants.** Named animation states declared once and referenced by string. They propagate from parent to children, which is what makes staggered orchestration trivial.

```tsx
const list = {
  hidden: { opacity: 0 },
  show:   { opacity: 1, transition: { staggerChildren: 0.06 } },
};
const item = {
  hidden: { opacity: 0, y: 12 },
  show:   { opacity: 1, y: 0 },
};

<motion.ul variants={list} initial="hidden" animate="show">
  {items.map(i => <motion.li key={i.id} variants={item}>{i.label}</motion.li>)}
</motion.ul>
```

Variants compose more cleanly than per-element timing because the parent owns the choreography. Always prefer variants for any animation involving more than one element.

**4. `AnimatePresence`.** Required for exit animations, because React unmounts components synchronously and Motion needs a moment to play the `exit` state. Wrap any conditional render whose exit you care about. Modes matter:
- `mode="sync"` (default) — incoming and outgoing animate together
- `mode="wait"` — outgoing fully exits before incoming enters (best for full-screen transitions)
- `mode="popLayout"` — outgoing is taken out of layout flow so siblings reflow immediately (best for list deletions)

**5. The `layout` prop and `layoutId`.** Adding `layout` to a component tells Motion to animate any layout change that happens to it — size, position, flex/grid reordering. Adding `layoutId="hero"` to two components in different parts of the tree makes Motion animate between them as if they were the same element (shared element transitions, magic move). This is the single feature most worth knowing.

Beyond these five: gesture props (`whileHover`, `whileTap`, `whileFocus`, `whileDrag`, `whileInView`), motion values (`useMotionValue`, `useTransform`, `useSpring`, `useScroll`), imperative animation (`useAnimate`), the `<Reorder>` API for drag-to-sort, and SVG-specific props like `pathLength`. Full surface in `references/motion-react.md`.

### Next.js App Router note

Any component using `motion/react` must be a client component — add `"use client"` at the top. For route transitions, wrap children in `AnimatePresence` inside a client component layout, keyed on `usePathname()`, usually with `mode="wait"`. Pattern in `references/recipes.md`.

## Reanimated — core mental model

Reanimated runs animations on the UI thread via **worklets** — JavaScript functions that the Babel plugin transforms to execute in a separate runtime. This is why animations stay smooth under JS-thread contention. The cost is a slightly less obvious mental model than Motion.

**1. Shared values.** `useSharedValue(initial)` returns an object with a `.value` property that lives on the UI thread. Reading or writing `.value` from JS works but is a bridge crossing; reading or writing inside a worklet is instant.

**2. Animated styles.** `useAnimatedStyle(() => ({ ... }))` is a worklet that returns a style object derived from shared values. When any shared value it reads changes, the style recomputes on the UI thread and the view updates without re-entering JS.

```tsx
const offset = useSharedValue(0);
const style = useAnimatedStyle(() => ({
  transform: [{ translateY: offset.value }],
  opacity: interpolate(offset.value, [0, 100], [1, 0]),
}));

return <Animated.View style={style} />;
```

**3. Animation primitives.** `withSpring`, `withTiming`, `withSequence`, `withDelay`, `withRepeat`, `withDecay`. Assign one of these to `.value` and Reanimated drives the value on the UI thread.

```tsx
offset.value = withSpring(100, { damping: 18, stiffness: 200 });
```

**4. Gesture Handler 2.** Reanimated pairs with `react-native-gesture-handler` v2's `Gesture` API. Gesture callbacks are worklets, so they can write shared values without crossing threads.

```tsx
const pan = Gesture.Pan()
  .onUpdate((e) => { offset.value = e.translationY; })
  .onEnd(() => { offset.value = withSpring(0); });

return (
  <GestureDetector gesture={pan}>
    <Animated.View style={style} />
  </GestureDetector>
);
```

**5. Layout animations.** Drop-in entering/exiting props on `Animated.View`:

```tsx
<Animated.View entering={FadeInDown} exiting={FadeOutUp} layout={Layout.springify()} />
```

Full API surface — `useDerivedValue`, `useAnimatedScrollHandler`, `runOnJS` / `runOnUI`, interpolation modes, shared element transitions under Fabric, the v3 → v4 migration map — lives in `references/reanimated.md`.

## Animation design — the essentials

These apply to both libraries and matter more than any specific API. Full treatment in `references/design-principles.md`; the high-leverage rules are here.

**Timing taxonomy.** Most UI animations fit one of these durations:
- **80–150ms** — instant feedback (tap, hover, focus). Below ~100ms reads as a state change rather than a transition, which is what fast feedback should feel like.
- **200–350ms** — standard moves (drawer, modal, card expand). Most common bucket; default to ~250ms.
- **400–600ms** — full-screen transitions, hero reveals, shared element moves. Longer is fine when the move is large.
- **>600ms** — almost always a mistake. Either you're showing off, or the user is waiting.

**Easing vs springs.** Default to springs. Springs respond to context — faster moves feel snappier, slower moves feel weightier — which is what makes animation feel alive. Reach for cubic-bezier curves when you need a specific *look*: `ease-out` for entering, `ease-in` for exiting, `ease-in-out` for round trips.

**Choreography.** When multiple things move at once, stagger them. 50–80ms between siblings reads as "intentional sequence" rather than "everything moved together." For lists, this is the difference between professional and amateur.

**Direction encodes meaning.** Down = appearing, settling. Up = leaving, dismissing. Right = forward. Left = back. Breaking these conventions confuses users even when they can't articulate why.

**Don't animate what doesn't need attention.** Every motion in the UI is a claim on the user's attention. If a fade isn't telling them something, cut it.

## Accessibility — not optional

Both libraries make this easy; do it every time. Skipping it means breaking the experience for users with vestibular disorders, motion sensitivity, or simply a preference for less motion — and that preference is set system-wide.

**Motion (web):**

```tsx
import { useReducedMotion, MotionConfig } from "motion/react";

// Per-component:
const reduce = useReducedMotion();
<motion.div animate={{ x: reduce ? 0 : 100 }} />

// Globally — wrap your app:
<MotionConfig reducedMotion="user">{children}</MotionConfig>
```

`reducedMotion="user"` honors the OS setting. `"always"` forces simplified animations. `"never"` ignores the preference — don't.

**Reanimated:**

```tsx
import { useReducedMotion } from "react-native-reanimated";

const reduce = useReducedMotion();
offset.value = reduce ? 0 : withSpring(100);
```

The general rule: when reduced motion is on, replace movement with opacity changes or instant snaps. Keep the meaning, drop the motion.

Animation also does not absolve you of ARIA. Modal exit animations should not delay focus restoration — set focus first, then animate. Long animations on focus targets strand keyboard users.

## Performance — the short version

**Web (Motion):**
- Animate `transform` and `opacity` when possible. They're hardware-accelerated. `width`, `height`, `top`, `left` trigger layout every frame.
- Use `layout` deliberately. It's magical but forces a measurement pass. Don't put `layout` on every item in a long list.
- `LazyMotion` + `domAnimation` (or `domMax`) ships a smaller bundle by loading only the features you use.
- Avoid expensive `useTransform` math repeated in long lists; derive once via chained motion values.

**Native (Reanimated):**
- Keep work inside worklets. `runOnJS` crosses the bridge — every call has a cost.
- Use `useDerivedValue` for chained computations; it stays on the UI thread.
- For long lists, animate per-item with `entering` / `exiting` rather than recomputing styles for every item.
- New Architecture is non-negotiable for Reanimated 4. Old arch apps are on Reanimated 3.

## House style — opinionated defaults

For this user's projects (glassmorphism, neon accents, confident timing), these are starting points; override per-component when intent calls for it. Full set in `references/house-style.md`.

**Default spring** (softer than Motion's default, settles cleanly):
```ts
const spring = { type: "spring", stiffness: 260, damping: 28, mass: 0.9 };
```

**Default tween** (for fades where spring overshoot is undesirable):
```ts
const fade = { duration: 0.24, ease: [0.32, 0.72, 0, 1] };
```

**Stagger** for lists: `staggerChildren: 0.06`, `delayChildren: 0.04`.

**Reduced motion fallback:** opacity-only, 120ms.

**Glassmorphism-aware patterns:** animate `backdrop-filter` blur only where supported; fall back to background opacity. Layer reveals work best with springs that overshoot ~3–5% (`damping: 22`) so glass-on-glass feels lifted, not glued.

## Where to go deeper

When working on a specific task, open the matching reference before writing code — these contain patterns that prevent rework:

- **`references/motion-react.md`** — Full Motion for React API: motion values, useScroll, useAnimate, Reorder, SVG animation, LazyMotion, the long tail of gotchas
- **`references/reanimated.md`** — Full Reanimated 4 API: worklets, interpolation, layout transitions, shared elements, scroll handlers, v3 → v4 migration map
- **`references/design-principles.md`** — Deep treatment of timing, easing, choreography, accessibility, when not to animate
- **`references/recipes.md`** — Copy-paste patterns: page transitions, scroll progress, parallax, reveal-on-scroll, magic move, drag-to-reorder, animated SVG path drawing, hover-tilt cards, list reorder, modal sheets
- **`references/house-style.md`** — Opinionated defaults: spring configs, timing curves, glassmorphism interactions, the "StewMore preset"

## Common gotchas

- **Motion exit animations never play.** Missing `AnimatePresence` around the conditional render, or the `key` changed in a way Motion can't detect.
- **`layout` jumps instead of animating.** A parent is constraining size in a way that prevents measurement (e.g. `display: contents`). Or you're animating to/from `display: none` — use `AnimatePresence` instead.
- **Stagger does nothing.** Children need their own `variants` matching the parent's variant names. The parent's `staggerChildren` orchestrates; each child still needs the state to play.
- **Next.js hydration warnings around motion components.** Add `"use client"` to the file. Don't use Motion in server components.
- **Reanimated: "tried to synchronously call function from a different thread."** You called a JS function from inside a worklet without `runOnJS`. Wrap the call.
- **Reanimated 4 build failures after upgrade from 3.** You forgot to install `react-native-worklets` and update the Babel plugin name to `react-native-worklets/plugin`.
- **Animations feel "off" but you can't say why.** Almost always one of: (a) duration is wrong for the move size, (b) easing is linear when it should be a spring, (c) nothing is staggered, (d) you're animating layout-triggering properties.

That's the foundation. Pick the right reference, read it, build.
