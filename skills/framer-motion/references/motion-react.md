# Motion for React — Full API Reference

This file is the deep dive on Motion (formerly Framer Motion) for the web. Read the relevant section before writing real code for any task that goes beyond the basics covered in `SKILL.md`.

Package: `motion` on npm. Imports: `motion/react`. Current major: 12.

## Table of contents

1. Setup & installation
2. Motion components
3. Animation props in depth
4. Transitions reference
5. Variants
6. AnimatePresence
7. Layout animations & shared elements
8. Gestures
9. Motion values & scroll
10. Imperative animation (useAnimate)
11. Reorder API
12. SVG animation
13. LazyMotion & bundle size
14. Edge cases & gotchas

---

## 1. Setup & installation

```bash
npm install motion
```

```tsx
import { motion, AnimatePresence } from "motion/react";
```

The `framer-motion` package still works as an alias and resolves to the same code — don't aggressively rewrite legacy imports unless that's the task. For new files, use `motion/react`.

**Next.js App Router:** any component using Motion must be a client component. Either add `"use client"` to the top of the file or extract motion-using parts into a child client component imported by a server component.

**SSR:** motion components render their `initial` state on the server. If `initial` and `animate` differ for first-mount visibility, the user may see a flash. Set `initial={false}` to skip the initial animation, or render the final state on the server and animate in only on the client.

## 2. Motion components

Every HTML and SVG element has a motion equivalent:

```tsx
<motion.div />
<motion.button />
<motion.section />
<motion.svg />
<motion.path />
<motion.circle />
// ...etc
```

For custom components (including shadcn primitives), wrap with `motion.create()`:

```tsx
import { motion } from "motion/react";
import { Button } from "@/components/ui/button";

const MotionButton = motion.create(Button);
// The wrapped component must forward refs.
```

`motion.create()` requires that the underlying component forwards refs and spreads HTML props to a single DOM node. shadcn/Radix primitives do this correctly.

## 3. Animation props in depth

The four animation props:

```tsx
<motion.div
  initial={{ opacity: 0, y: 8, scale: 0.96 }}   // starting state
  animate={{ opacity: 1, y: 0, scale: 1 }}      // target state
  exit={{ opacity: 0, y: -8 }}                   // when removed (needs AnimatePresence)
  transition={{ duration: 0.24, ease: "easeOut" }}
/>
```

All four accept:
- An **object** of style properties to animate
- A **variant name** (string) referencing a variants object
- An **array of variant names** for sequenced states
- `false` (only on `initial`) to skip the initial animation

Animatable properties include `x`, `y`, `z`, `rotate`, `rotateX/Y/Z`, `scale`, `scaleX/Y`, `skewX/Y`, `opacity`, `color`, `backgroundColor`, `borderRadius`, `width`, `height`, `top`, `left`, `right`, `bottom`, `padding*`, `margin*`, SVG attributes (`pathLength`, `pathOffset`, `cx`, `cy`, `r`), CSS variables (must be prefixed in the style: `"--my-var"`), and filter properties (`blur`, `brightness`, etc.).

**Transforms are special.** `x`, `y`, `scale`, `rotate` map to `translate3d`/`scale`/`rotate` on a single composited transform — hardware-accelerated, no layout. Prefer them over `top`/`left`/`width`/`height` for performance.

## 4. Transitions reference

The `transition` prop controls *how* the move happens.

### Spring (default for transforms)

```tsx
transition={{
  type: "spring",
  stiffness: 260,    // higher = faster
  damping: 28,       // higher = less oscillation
  mass: 0.9,         // higher = heavier feel
  restDelta: 0.001,  // when to consider settled (rarely needed)
  velocity: 0,       // initial velocity
}}
```

Alternative spring spec (often easier to reason about):

```tsx
transition={{
  type: "spring",
  duration: 0.6,
  bounce: 0.2,       // 0 = no overshoot, 0.5 = lots
}}
```

### Tween

```tsx
transition={{
  type: "tween",
  duration: 0.24,
  ease: "easeOut",                       // or "linear" | "easeIn" | "easeInOut" | "circIn" | etc.
  // or a cubic-bezier array:
  ease: [0.32, 0.72, 0, 1],
}}
```

### Inertia (for drag-end)

```tsx
transition={{
  type: "inertia",
  velocity: 50,
  power: 0.8,
  timeConstant: 700,
  bounceStiffness: 500,
  bounceDamping: 10,
}}
```

### Per-property transitions

Different timings for different properties on the same animation:

```tsx
transition={{
  default: { type: "spring", stiffness: 300, damping: 30 },
  opacity: { duration: 0.2 },
  scale:   { type: "spring", stiffness: 500, damping: 20 },
}}
```

### Orchestration

```tsx
transition={{
  delay: 0.1,
  delayChildren: 0.04,        // delay before children start
  staggerChildren: 0.06,      // gap between each child
  staggerDirection: 1,        // 1 = first-to-last, -1 = last-to-first
  when: "beforeChildren",     // or "afterChildren" — for entry/exit ordering
  repeat: 2,                  // or Infinity
  repeatType: "loop",         // "loop" | "reverse" | "mirror"
  repeatDelay: 0.5,
}}
```

## 5. Variants

Variants are the single most useful Motion feature for non-trivial animation.

```tsx
const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.05 },
  },
};

const item = {
  hidden: { opacity: 0, y: 12 },
  show:   { opacity: 1, y: 0 },
};

<motion.ul variants={container} initial="hidden" animate="show">
  {data.map((d) => (
    <motion.li key={d.id} variants={item}>{d.label}</motion.li>
  ))}
</motion.ul>
```

**Propagation:** when a parent has variants and changes state, every child with matching variant names also plays that state. Children don't need their own `animate` prop; they inherit from the parent.

**Variants can be functions:**

```tsx
const item = {
  hidden: (i: number) => ({ opacity: 0, x: i % 2 === 0 ? -20 : 20 }),
  show: { opacity: 1, x: 0 },
};

<motion.li variants={item} custom={index} />
```

The `custom` prop is passed to the function, enabling per-item variation without a separate variants object per item.

**Multiple variants at once:**

```tsx
<motion.div animate={["hover", "active"]} />
```

## 6. AnimatePresence

Required for exit animations. Wraps conditional renders.

```tsx
<AnimatePresence mode="wait">
  {isOpen && (
    <motion.div
      key="panel"                                  // important — see below
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
    />
  )}
</AnimatePresence>
```

**Keys matter.** Motion uses the `key` prop on children of `AnimatePresence` to detect what's exiting. Without explicit keys, behavior is unreliable.

**Modes:**
- `mode="sync"` (default): old and new render at the same time, transitions overlap
- `mode="wait"`: old fully exits before new mounts (full-screen route transitions)
- `mode="popLayout"`: old is removed from layout immediately so siblings reflow (list deletions)

**Skipping the initial mount animation:** `<AnimatePresence initial={false}>` — incoming children skip their first mount animation, useful for tabs and conditional UI that shouldn't animate-in on first render.

**Custom prop forwarding for exit:** if exit animation depends on direction (e.g. a carousel), pass `custom`:

```tsx
<AnimatePresence custom={direction}>
  <motion.div key={page} custom={direction} variants={slideVariants} />
</AnimatePresence>
```

## 7. Layout animations & shared elements

The `layout` prop animates any layout change. The `layoutId` prop animates between elements that share the same ID.

### Self-layout animation

```tsx
<motion.div layout>
  {expanded ? <LongContent /> : <ShortContent />}
</motion.div>
```

Anything that changes the layout of this element — content swaps, flex/grid reflows, size changes — gets animated.

Constrain what gets animated with `layout="position"` (only position) or `layout="size"` (only size). The default is both.

### Shared element transitions (magic move)

Give two motion elements the same `layoutId`. When one unmounts and the other mounts, Motion animates between them.

```tsx
{selected ? (
  <motion.div layoutId="card-hero" className="full-screen-view" />
) : (
  <motion.div layoutId="card-hero" className="thumbnail" />
)}
```

This is the "hero" pattern from native mobile apps. Critical for polished product UI.

**LayoutGroup** scopes shared element matching:

```tsx
<LayoutGroup id="cards">
  {/* multiple cards each with layoutId="hero" but unique within this group */}
</LayoutGroup>
```

### Performance notes for layout animations

- `layout` forces a measurement pass on every render. Don't put it on every item in a 1000-item list — only on the few items that actually transition.
- `layout` doesn't work across `display: none` boundaries; use `AnimatePresence` instead.
- For best results pair `layout` with the `LayoutGroup` parent so siblings re-measure in coordination.

## 8. Gestures

Motion handles four gesture states via dedicated props:

```tsx
<motion.button
  whileHover={{ scale: 1.04 }}
  whileTap={{ scale: 0.96 }}
  whileFocus={{ outline: "2px solid var(--ring)" }}
  whileInView={{ opacity: 1, y: 0 }}
  initial={{ opacity: 0, y: 12 }}
  viewport={{ once: true, amount: 0.5 }}   // for whileInView
/>
```

`viewport` config:
- `once: true` — only animate first time it enters
- `amount: 0.5` — fraction visible before triggering (0 to 1, or "some" | "all")
- `margin: "0px 0px -100px 0px"` — like IntersectionObserver rootMargin
- `root: ref` — scope to a custom scroll container

### Drag

```tsx
<motion.div
  drag                                       // or "x" | "y"
  dragConstraints={{ left: -100, right: 100 }}
  dragElastic={0.2}                          // resistance past constraints (0 = hard stop, 1 = no resist)
  dragMomentum={true}                        // momentum after release
  dragSnapToOrigin                           // snap back to start on release
  onDragStart={(e, info) => {}}
  onDragEnd={(e, info) => {}}
  onDrag={(e, info) => {}}
/>
```

`info` includes `offset`, `velocity`, `point`, `delta` — useful for swipe-to-dismiss and similar.

**Constraints via ref:**

```tsx
const containerRef = useRef(null);
<div ref={containerRef}>
  <motion.div drag dragConstraints={containerRef} />
</div>
```

**Programmatic drag:**

```tsx
const controls = useDragControls();
<motion.div drag dragControls={controls} dragListener={false} />
<button onPointerDown={(e) => controls.start(e)}>Drag handle</button>
```

## 9. Motion values & scroll

Motion values are subscribable primitives that don't trigger React re-renders. They're how scroll-linked animations stay smooth.

```tsx
const x = useMotionValue(0);
// Read: x.get()
// Write: x.set(100) or x.set(prev => prev + 10)
// Subscribe: useMotionValueEvent(x, "change", (v) => console.log(v))
// Transform: const y = useTransform(x, [0, 100], [0, 200])
// Smooth: const smoothX = useSpring(x, { stiffness: 200, damping: 30 })
```

Pass motion values directly to motion component props:

```tsx
<motion.div style={{ x }} />
```

### useScroll

The workhorse for scroll-driven UI:

```tsx
const { scrollY, scrollYProgress } = useScroll();
// scrollY: pixel offset from page top
// scrollYProgress: 0 to 1 across page

// Element-relative:
const ref = useRef(null);
const { scrollYProgress } = useScroll({
  target: ref,
  offset: ["start end", "end start"], // when target's start hits viewport end, until target's end hits viewport start
});
```

**Offset strings** describe alignment: `"start end"` means "target's start edge aligned with container's end edge." Common offsets:
- `["start end", "end start"]` — full scroll-through of the element
- `["start start", "end end"]` — element pinned for its full height
- `["start end", "start start"]` — element entering the viewport
- `["end end", "end start"]` — element leaving the viewport

### Common scroll pattern: parallax

```tsx
const ref = useRef(null);
const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
const y = useTransform(scrollYProgress, [0, 1], [-100, 100]);

<div ref={ref}>
  <motion.div style={{ y }}>Parallax content</motion.div>
</div>
```

### Common scroll pattern: progress bar

```tsx
const { scrollYProgress } = useScroll();
const scaleX = useSpring(scrollYProgress, { stiffness: 100, damping: 30 });
<motion.div style={{ scaleX, transformOrigin: "0%" }} className="fixed top-0 left-0 right-0 h-1 bg-primary" />
```

## 10. Imperative animation (useAnimate)

For animations triggered by code rather than props:

```tsx
const [scope, animate] = useAnimate();

const playSequence = async () => {
  await animate(scope.current, { opacity: 1 }, { duration: 0.3 });
  await animate("li", { x: 0 }, { delay: stagger(0.1) });
};

<ul ref={scope}>
  <li>...</li>
</ul>
```

`scope.current` is the root; CSS selectors like `"li"` are scoped to it. `stagger()` is a delay helper for arrays of targets.

**Sequences:**

```tsx
animate([
  [scope.current, { opacity: 1 }, { duration: 0.3 }],
  ["li", { x: 0 }, { delay: stagger(0.1) }],
  [".cta", { scale: 1 }, { at: "-0.2" }],   // overlap with previous
]);
```

The `at` keyword controls segment timing: `"<"` = parallel with previous start, number = absolute time, `"-0.2"` = 0.2s before previous end.

## 11. Reorder API

For drag-to-sort lists:

```tsx
import { Reorder } from "motion/react";

const [items, setItems] = useState(initialItems);

<Reorder.Group axis="y" values={items} onReorder={setItems}>
  {items.map((item) => (
    <Reorder.Item key={item.id} value={item}>
      {item.label}
    </Reorder.Item>
  ))}
</Reorder.Group>
```

`axis` is `"x"` or `"y"`. Each `Reorder.Item` is draggable along that axis. `values` and `onReorder` are required — you own the array. Items must have stable `key` props matching their `value`.

For drag handles, set `dragListener={false}` on the item and use `useDragControls()` on a child element inside.

## 12. SVG animation

SVG-specific props that aren't on HTML elements:

```tsx
<motion.path
  d="M 10 10 L 100 100"
  pathLength={0}       // 0 = invisible, 1 = full path drawn
  pathOffset={0}       // shift the visible portion along the path
  pathSpacing={1}      // gaps when pathLength < 1
  initial={{ pathLength: 0 }}
  animate={{ pathLength: 1 }}
  transition={{ duration: 1.5, ease: "easeInOut" }}
/>
```

`pathLength` makes "draw-in" line animations trivial. Works on `<path>`, `<line>`, `<polyline>`, `<polygon>`, `<circle>`, `<rect>`.

For animated icon morphs, animate the `d` attribute between path strings. Motion interpolates between paths with the same number of commands; if paths have different command counts, use `flubber` to normalize.

## 13. LazyMotion & bundle size

Motion's `motion.*` components include all features. To ship a smaller bundle, use the lightweight `m.*` components and load features explicitly:

```tsx
import { LazyMotion, domAnimation, m } from "motion/react";

<LazyMotion features={domAnimation}>
  <m.div animate={{ x: 100 }} />
</LazyMotion>
```

Features:
- `domAnimation` (~25kb) — animations, variants, gestures
- `domMax` (~32kb) — adds drag, layout animations, scroll

Replace `motion.*` with `m.*` inside the `LazyMotion` boundary. The full `motion.*` is fine for prototyping; switch to `m.*` for production bundles when size matters.

## 14. Edge cases & gotchas

**Exit animations not playing.** Missing `AnimatePresence` wrapper, or no `key` on the child. Or you're using `mode="wait"` and the previous child never fully exited because some animation property doesn't have an `exit` value.

**`layout` causes a jump on first render.** The element measured at one size, then measured again after a CSS class flip. Either delay the class change until after mount, or set `initial={false}` to skip the first transition.

**Spring overshoots when you don't want it to.** Either raise `damping` or switch `type: "tween"`. Or use the `bounce: 0` form: `transition={{ type: "spring", duration: 0.4, bounce: 0 }}`.

**`useTransform` outputs wrong values in StrictMode.** Motion values are stable across re-renders, but if you're recreating them inside a render (no `useMotionValue` wrapper), StrictMode's double-render will produce stale subscriptions. Always create motion values inside hooks, never inline.

**Reorder items snap to wrong positions on drop.** The `value` prop on each item must be the same reference as the corresponding entry in `values`. Don't pass `{...item}` — pass `item`.

**Variant doesn't propagate to a child.** The child is wrapped in a non-motion component that breaks the variant context. Either lift the child up or wrap the intermediate with `motion.create()`.

**`whileHover` triggers on touch devices.** Touch starts trigger hover on iOS Safari. Pair `whileHover` with `whileTap` and consider `@media (hover: hover)` for desktop-only hover-as-decoration cases.

**Server-rendered initial state flashes.** Motion renders `initial` on the server. If `initial` differs visually from `animate`, the user sees the initial state briefly. Either match initial to animate visually (animate from current state) or skip with `initial={false}`.

**Animations are choppy under React state churn.** Use motion values or refs to drive animations rather than state. State changes cause re-renders; motion values don't.
