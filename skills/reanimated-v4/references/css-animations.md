# CSS Animations & Transitions in Reanimated v4

The biggest v4 feature. Familiar web syntax, runs natively on the UI thread, requires no worklets or shared values. This is the right tool whenever the animation is **declarative and state-driven** — the user changes state, the style animates.

## When to choose CSS over worklets

Use CSS animations/transitions when:

- The animation has known start and end states (toggle expand, fade in on mount, color shift on hover)
- It runs continuously without input (spinner, shimmer, breathing dot)
- It's triggered by a discrete state change in React (a boolean flipping, props updating)

Stay with worklets when:

- The animation tracks a continuous input (gesture, scroll position, sensor)
- Per-frame logic is needed
- You need to coordinate multiple animated values with non-trivial math

The two layers compose. You can have CSS transitions on most properties and a `useAnimatedStyle`-driven transform on the same element if the transform follows a drag while everything else fades.

---

## CSS Transitions

A transition tells Reanimated: "when *this style property* changes, don't snap — interpolate over time."

### The five properties

| Property | What it controls | Values |
|---|---|---|
| `transitionProperty` | Which style props animate | string or string[] — `'all'`, `'opacity'`, `['width', 'backgroundColor']` |
| `transitionDuration` | Length | ms number, string `'300ms'` or `'0.3s'`, or array per property |
| `transitionDelay` | Wait before starting | ms, string, or array |
| `transitionTimingFunction` | Easing curve | `'ease'`, `'linear'`, `'ease-in'`, `'ease-out'`, `'ease-in-out'`, `cubic-bezier(...)`, `steps(n)`, or array |
| `transitionBehavior` | Discrete value handling | `'normal'` (default — discrete values snap) or `'allow-discrete'` (animate discrete-property changes, e.g., `display`) |

### Single-property transition

```tsx
<Animated.View
  style={{
    opacity: visible ? 1 : 0,
    transitionProperty: 'opacity',
    transitionDuration: 200,
  }}
/>
```

### Multi-property transition with per-property durations

```tsx
<Animated.View
  style={{
    width: open ? 280 : 60,
    backgroundColor: open ? '#1d4ed8' : '#94a3b8',
    transitionProperty: ['width', 'backgroundColor'],
    transitionDuration: [240, 400],
    transitionTimingFunction: ['ease-out', 'ease-in-out'],
  }}
/>
```

### `transitionProperty: 'all'`

Animates every animatable property change. Convenient but blunt — every style change in the array animates with the same duration/timing, which can lead to surprises if you add a new prop later. Prefer explicit property lists for production code.

### Triggering transitions

The transition fires whenever the style value changes. Source of the change is irrelevant — it can be `useState`, props, context, a derived value from a query. There is no "play" or "stop"; it's purely reactive.

### Disabling

Remove `transitionProperty` (or set duration to 0) to make changes snap again. Useful when reduced motion is on:

```tsx
const reducedMotion = useReducedMotion();
<Animated.View style={{
  opacity: visible ? 1 : 0,
  transitionProperty: reducedMotion ? undefined : 'opacity',
  transitionDuration: 200,
}}/>
```

---

## CSS Animations (keyframes)

Animations are keyframe-driven and self-driving — they start running as soon as `animationName` is set and a duration is provided.

### Defining keyframes

Declare a keyframes object. Reanimated exports the `CSSAnimationKeyframes` type. Keys are percentage strings (`'0%'`, `'50%'`, `'100%'`) or the special `from` / `to` aliases. Values are partial style objects.

```ts
import { type CSSAnimationKeyframes } from 'react-native-reanimated';

const shimmer: CSSAnimationKeyframes = {
  from: { transform: [{ translateX: -200 }] },
  to:   { transform: [{ translateX: 200 }] },
};

const bounce: CSSAnimationKeyframes = {
  '0%':   { transform: [{ translateY: 0 }] },
  '40%':  { transform: [{ translateY: -30 }] },
  '60%':  { transform: [{ translateY: -15 }] },
  '100%': { transform: [{ translateY: 0 }] },
};
```

Define keyframes **outside the component body** when possible — they're plain data that doesn't need to be recreated each render.

### The eight properties

| Property | Purpose | Values |
|---|---|---|
| `animationName` | Which keyframes to run | object, or string name if defined globally; `'none'` to stop |
| `animationDuration` | How long one iteration takes | ms or string |
| `animationDelay` | Wait before starting | ms or string |
| `animationTimingFunction` | Easing within each iteration | same set as `transitionTimingFunction` |
| `animationDirection` | Playback direction | `'normal'`, `'reverse'`, `'alternate'`, `'alternate-reverse'` |
| `animationIterationCount` | Number of loops | integer or `'infinite'` |
| `animationFillMode` | What style applies before/after | `'none'`, `'forwards'`, `'backwards'`, `'both'` |
| `animationPlayState` | Play/pause | `'running'`, `'paused'` |

### Looping animation

```tsx
<Animated.View
  style={{
    width: 24, height: 24, borderRadius: 12, backgroundColor: '#ef4444',
    animationName: pulse,
    animationDuration: 1200,
    animationIterationCount: 'infinite',
    animationTimingFunction: 'ease-in-out',
  }}
/>
```

### One-shot animation that holds its end state

`animationFillMode: 'forwards'` retains the final keyframe's values after the animation ends.

```tsx
<Animated.View
  style={{
    animationName: slideUpAndStay,
    animationDuration: 400,
    animationFillMode: 'forwards',
  }}
/>
```

### Pausing without resetting

```tsx
<Animated.View
  style={{
    animationName: spin,
    animationDuration: 1500,
    animationIterationCount: 'infinite',
    animationPlayState: paused ? 'paused' : 'running',
  }}
/>
```

### Switching animations

Setting `animationName` to a different keyframes object swaps animations immediately (the current animation is interrupted). Setting it to `'none'` stops the animation; the element snaps to its base style (unless `fillMode: 'forwards'` is in effect, in which case it stays at the end frame).

```tsx
animationName: state === 'loading' ? spin : state === 'error' ? shake : 'none'
```

### Per-iteration variation

`animationDirection: 'alternate'` runs forward on odd iterations and reverse on even, useful for yo-yo effects without writing the reverse keyframes:

```tsx
{
  animationName: { from: { opacity: 0.4 }, to: { opacity: 1 } },
  animationDuration: 800,
  animationIterationCount: 'infinite',
  animationDirection: 'alternate',
}
```

---

## Multiple simultaneous animations

You can declare multiple animation names by passing arrays for all of the animation properties. Each index lines up across arrays.

```tsx
{
  animationName: [pulse, slowDrift],
  animationDuration: [800, 6000],
  animationIterationCount: ['infinite', 'infinite'],
  animationTimingFunction: ['ease-in-out', 'linear'],
}
```

Different keyframes targeting different properties layer cleanly. If two animations target the same property, the later one wins for that property's value (last-write).

---

## Picking values that animate cleanly

Not every style change interpolates by default. Some quick guidance:

- **Transforms (`translateX`, `scale`, `rotate`)** — best. Cheap on the GPU; no layout work.
- **`opacity`** — very cheap; almost free.
- **`backgroundColor`, `borderColor`, color** — interpolate smoothly via `interpolateColor` semantics internally.
- **`width`, `height`, padding, margin** — work, but trigger layout each frame. Acceptable for small or short animations; avoid on large lists.
- **`shadowOpacity`, `shadowRadius`, `boxShadow` (4.2+)** — work; can be expensive on Android. Test on a real device.
- **`borderRadius`** — works.
- **`display`** — needs `transitionBehavior: 'allow-discrete'`. The change is discrete; the transition only animates the surrounding properties to coordinate appearance.

If something doesn't appear to animate, the most common cause is that it's not on the v4 supported-properties list yet, or it's not on an `Animated.*` component.

---

## Worklet ↔ CSS interop

You can mix them on the same element. A common pattern: drag (worklet) + visual feedback (CSS transition).

```tsx
const translateX = useSharedValue(0);
const isPressed = useSharedValue(false);

const dragStyle = useAnimatedStyle(() => ({
  transform: [{ translateX: translateX.value }],
}));

return (
  <Animated.View
    style={[
      {
        backgroundColor: pressed ? '#1d4ed8' : '#3b82f6', // React state
        transitionProperty: 'backgroundColor',
        transitionDuration: 150,
      },
      dragStyle, // worklet-driven transform
    ]}
  />
);
```

The transform follows the gesture in real time (worklet), while the color change on press uses a CSS transition.

---

## Type safety

Reanimated v4 ships TypeScript types:

```ts
import Animated, {
  type CSSAnimationKeyframes,
  type CSSAnimationProperties,
  type CSSTransitionProperties,
} from 'react-native-reanimated';

const fadeUp: CSSAnimationKeyframes = {
  from: { opacity: 0, transform: [{ translateY: 20 }] },
  to:   { opacity: 1, transform: [{ translateY: 0 }] },
};
```

Using these types catches typos in property names and invalid value shapes at compile time, which matters because CSS-property typos fail silently at runtime (the animation just doesn't run).
