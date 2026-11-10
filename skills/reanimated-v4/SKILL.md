---
name: reanimated-v4
description: Use this skill for any animation work in React Native with react-native-reanimated v4.x. Triggers on mentions of Reanimated, useSharedValue, useAnimatedStyle, withTiming, withSpring, worklets, runOnJS, gesture-driven animations, CSS animations in React Native (animationName, transitionProperty), layout animations (entering/exiting, LinearTransition), shared element transitions, scroll-driven effects, parallax, drag-and-drop, swipeable cards, accordions, FABs, bottom sheets, or any request to make a React Native UI animate, slide, fade, scale, rotate, spring, bounce, shake, or otherwise move. Also triggers when migrating from Reanimated 3 to 4, debugging "JS thread blocked" or "worklet not found" errors, debugging animations that don't run on the New Architecture, or choosing between CSS animations and worklets. Use this skill whenever React Native animation is involved, even if the user doesn't explicitly say "Reanimated" — it is the de facto standard library for React Native motion.
---

# React Native Reanimated v4

A guide for producing correct, performant, idiomatic Reanimated v4 animation code in React Native. Reanimated v4 is a meaningful evolution: it introduces CSS-style animations and transitions, requires the New Architecture, and splits the worklet runtime into its own package. Most stale knowledge about Reanimated (and most code on the web) is v2/v3, so be deliberate about using v4 patterns.

## When to use this skill

Whenever the task involves motion in a React Native app: gesture-driven interactions, scroll effects, layout changes, micro-interactions, loading indicators, bottom sheets, swipeable rows, parallax headers, transitions between states. Also use this skill for debugging stutter, "JS thread blocked" warnings, missing worklet errors, or "animation doesn't run" issues after upgrading to RN 0.76+/New Architecture.

If the user is on Reanimated 3.x and can't migrate (e.g., still on the legacy renderer Paper), most of the patterns here still apply — the worklet/shared value model is unchanged — but the CSS animation and CSS transition layers are v4-only. Call that out explicitly when relevant.

## Mental model — three animation layers

Reanimated v4 gives you three different layers for animating. Picking the right one is the single most important decision and the thing this skill exists to get right. They compose freely; you can mix them on the same component.

**Layer 1 — CSS Animations & Transitions (declarative, v4-only).** Use when the animation is state-driven with known start/end values: a card that expands when tapped, a button that pulses while loading, a modal that fades in. No `useSharedValue`, no `useAnimatedStyle` — you set `transitionProperty` + `transitionDuration` (or `animationName` + `animationDuration`) directly in the style object and let component state drive the change. This is the right default for ~80% of "I want this to animate when X happens" requests because it's the least code and the easiest to read.

**Layer 2 — Layout Animations (declarative, mount/unmount/reorder).** Use when items appear, disappear, or change position in a list. Pass `entering`, `exiting`, or `layout` props on `Animated.View` with preset animations like `FadeIn`, `SlideInRight`, `LinearTransition`. The library handles the mount/unmount lifecycle for you.

**Layer 3 — Worklets + Shared Values (imperative, gesture/scroll/frame-driven).** Use when the animation responds continuously to a gesture, scroll position, sensor value, or per-frame computation. This is the original Reanimated model: `useSharedValue` for state that lives on the UI thread, `useAnimatedStyle` to derive styles from it, `withSpring`/`withTiming`/`withDecay` to animate it, Gesture Handler to drive it. Pricier in code but the only choice when values flow continuously from input.

The decision tree below operationalizes this. Walk it top to bottom; the first match wins.

## Decision tree — which layer for which task

```
Is the animation tied to a continuous user gesture (drag, pan, pinch, swipe)?
  → Layer 3 (worklets). Gesture Handler + useSharedValue + useAnimatedStyle.
    Use withSpring/withDecay for the release.

Is the animation driven by scroll position (parallax, sticky header, fade-on-scroll)?
  → Layer 3 (worklets). useAnimatedRef + useScrollOffset + useAnimatedStyle + interpolate.

Are items entering, leaving, or reordering in a list?
  → Layer 2 (layout animations). entering={FadeIn}, exiting={FadeOut}, layout={LinearTransition}.

Is the animation continuous/looping with no input (spinner, shimmer, pulse, breathing)?
  → Layer 1 CSS animation. animationName with keyframes + animationIterationCount: 'infinite'.

Is the animation a one-shot response to a state change with known start/end (expand on tap, fade in on mount)?
  → Layer 1 CSS transition. transitionProperty + transitionDuration on the changing style.

Does it need frame-by-frame logic (physics, custom curves outside what withSpring offers)?
  → Layer 3 (worklets). useFrameCallback.

Shared element transition between screens?
  → Shared Element Transitions (experimental in v4.2+, feature-flagged). Use only if user opts in.
```

When two layers could plausibly fit, prefer the higher-level one. CSS > Layout > Worklets in code volume, readability, and maintenance cost.

## Setup checks before writing code

Before producing any Reanimated v4 code, verify these. If they're missing or you can't tell, mention them in the response so the user knows to check:

- **New Architecture is on.** Reanimated v4 only runs on Fabric. Old Architecture (Paper) is not supported. RN 0.76+ with `newArchEnabled: true` (or Expo SDK that bundles it).
- **`react-native-worklets` is installed alongside `react-native-reanimated`.** In v4 the worklet runtime is its own package. The user needs both.
- **Babel plugin is `react-native-worklets/plugin`, not the old `react-native-reanimated/plugin`.** Must be the last plugin in the list. The old plugin name still works for now but is deprecated.
- **Gesture-driven code requires `react-native-gesture-handler`** and the app must be wrapped in `<GestureHandlerRootView>` at the root.
- **Animated components.** Only `Animated.View`, `Animated.Text`, `Animated.Image`, `Animated.ScrollView`, `Animated.FlatList` etc. respond to Reanimated animations. For other components (including third-party), wrap with `Animated.createAnimatedComponent(Component)`.

## Core patterns — the 80% case

These cover most real-world requests. For deeper API details, gesture composition, layout animations, recipes, and pitfalls, consult the reference files listed at the bottom.

### Pattern 1 — CSS transition (state-driven micro-interaction)

When state flips, the style change animates automatically. This is the new v4 default for simple toggles.

```tsx
import { useState } from 'react';
import { Pressable, Text } from 'react-native';
import Animated from 'react-native-reanimated';

export function ExpandingCard() {
  const [open, setOpen] = useState(false);
  return (
    <Pressable onPress={() => setOpen(o => !o)}>
      <Animated.View
        style={{
          width: open ? 260 : 160,
          height: 160,
          backgroundColor: open ? '#6ee7b7' : '#a7f3d0',
          borderRadius: 16,
          padding: 16,
          transitionProperty: ['width', 'backgroundColor'],
          transitionDuration: 300,
          transitionTimingFunction: 'ease-out',
        }}
      >
        <Text>Tap me</Text>
      </Animated.View>
    </Pressable>
  );
}
```

No shared values, no worklets. The presence of `transitionProperty` on an `Animated.*` component tells Reanimated to animate any change to those properties.

### Pattern 2 — CSS keyframe animation (looping or one-shot continuous)

For loaders, shimmers, pulses, attention grabbers.

```tsx
import Animated, { type CSSAnimationKeyframes } from 'react-native-reanimated';

const pulse: CSSAnimationKeyframes = {
  '0%': { transform: [{ scale: 1 }], opacity: 1 },
  '50%': { transform: [{ scale: 1.1 }], opacity: 0.7 },
  '100%': { transform: [{ scale: 1 }], opacity: 1 },
};

export function PulseDot() {
  return (
    <Animated.View
      style={{
        width: 24,
        height: 24,
        borderRadius: 12,
        backgroundColor: '#ef4444',
        animationName: pulse,
        animationDuration: 1200,
        animationIterationCount: 'infinite',
        animationTimingFunction: 'ease-in-out',
      }}
    />
  );
}
```

To stop the animation, set `animationName: 'none'` (or conditionally swap it). To pause without resetting, use `animationPlayState: 'paused'`.

### Pattern 3 — Gesture-driven drag (worklets)

The canonical Reanimated pattern. Track gesture state in shared values; let `useAnimatedStyle` read them.

```tsx
import { GestureDetector, Gesture } from 'react-native-gesture-handler';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
} from 'react-native-reanimated';

export function DraggableBox() {
  const translateX = useSharedValue(0);
  const translateY = useSharedValue(0);

  const pan = Gesture.Pan()
    .onChange((event) => {
      translateX.value += event.changeX;
      translateY.value += event.changeY;
    })
    .onEnd(() => {
      translateX.value = withSpring(0);
      translateY.value = withSpring(0);
    });

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: translateX.value },
      { translateY: translateY.value },
    ],
  }));

  return (
    <GestureDetector gesture={pan}>
      <Animated.View
        style={[
          { width: 100, height: 100, backgroundColor: '#3b82f6', borderRadius: 12 },
          animatedStyle,
        ]}
      />
    </GestureDetector>
  );
}
```

Key rules: gesture callbacks (`onChange`, `onEnd`, etc.) are worklets — they run on the UI thread automatically. Inside them, `translateX.value = X` writes synchronously. On release, wrap with `withSpring`/`withTiming` to animate to the rest state. Never call regular React setState from inside these callbacks — use `runOnJS(setStateFn)(value)` if you must touch JS-thread code.

### Pattern 4 — Scroll-driven animation (worklets)

For sticky headers, parallax, fade-on-scroll, scroll-snap effects.

```tsx
import Animated, {
  useAnimatedRef,
  useScrollOffset,
  useAnimatedStyle,
  interpolate,
  Extrapolation,
} from 'react-native-reanimated';

const HEADER_MAX = 240;
const HEADER_MIN = 80;

export function ParallaxHeader() {
  const scrollRef = useAnimatedRef<Animated.ScrollView>();
  const scrollY = useScrollOffset(scrollRef);

  const headerStyle = useAnimatedStyle(() => ({
    height: interpolate(
      scrollY.value,
      [0, HEADER_MAX - HEADER_MIN],
      [HEADER_MAX, HEADER_MIN],
      Extrapolation.CLAMP,
    ),
    opacity: interpolate(
      scrollY.value,
      [0, HEADER_MAX - HEADER_MIN],
      [1, 0.6],
      Extrapolation.CLAMP,
    ),
  }));

  return (
    <>
      <Animated.View style={[{ backgroundColor: '#1e293b' }, headerStyle]} />
      <Animated.ScrollView ref={scrollRef} scrollEventThrottle={16}>
        {/* content */}
      </Animated.ScrollView>
    </>
  );
}
```

Note: `useScrollOffset` is the v4 name. `useScrollViewOffset` still works but is deprecated. Use the new name in new code.

### Pattern 5 — Layout animations (list items appear/disappear/reorder)

For todo lists, chat messages, animated removal of cards, animated additions to a feed.

```tsx
import Animated, {
  FadeIn,
  FadeOut,
  LinearTransition,
} from 'react-native-reanimated';

export function AnimatedList({ items }: { items: Item[] }) {
  return (
    <>
      {items.map((item) => (
        <Animated.View
          key={item.id}
          entering={FadeIn.duration(200)}
          exiting={FadeOut.duration(150)}
          layout={LinearTransition.springify()}
        >
          {/* row content */}
        </Animated.View>
      ))}
    </>
  );
}
```

`entering`/`exiting` animate the mount/unmount; `layout` animates position changes when surrounding items add/remove. This works inside FlatList too, but with caveats — see `references/layout-animations.md`.

## Critical worklet & shared-value rules

These are the most common sources of broken animations. Internalize them.

1. **`'worklet'` directive is required on any function meant to run on the UI thread.** Hook callbacks (`useAnimatedStyle`, `useAnimatedReaction`, gesture handlers) auto-inject it. Standalone functions need it explicitly as the first line.

2. **Don't read `.value` during render.** Reading a shared value on the JS thread is a sync bridge call that can block. Inside `useAnimatedStyle` it's fine (that's the UI thread). In a regular component body or `useEffect` deps, avoid it — use `useDerivedValue` or `useAnimatedReaction` instead.

3. **Mutate object/array shared values with `.modify()`, not `.value.push()`.** Direct mutation breaks reactivity. Either replace the whole value (`sv.value = [...sv.value, x]`) or use `sv.modify(v => { 'worklet'; v.push(x); return v; })`.

4. **Cross the thread boundary with `runOnJS` / `runOnUI`.** From a worklet, call back into JS-thread code with `runOnJS(myFn)(arg)`. From JS, invoke a worklet on the UI thread with `runOnUI(myWorklet)()`. Don't try to mix threads directly — you'll see `ReanimatedError: Tried to synchronously call a non-worklet function on the UI thread` or similar.

5. **Animated components only.** `withTiming(myValue)` applied to a regular `<View>` does nothing. The component must be `Animated.View` or wrapped with `createAnimatedComponent`.

6. **`useAnimatedStyle` must return a style object directly.** Don't return arrays, don't return conditionally — return one object whose properties may use conditionals.

7. **Don't destructure shared values.** `const { value } = sv` captures the current value, loses the live reference, and breaks reactivity.

The `references/pitfalls.md` file has a longer list with the failure mode each one produces — load it whenever debugging "this animation doesn't work" complaints.

## When to load which reference

`references/` contains deeper material organized by topic. Load the relevant file(s) when the task moves beyond the patterns above:

- **`api-reference.md`** — Need signatures, params, return types, or to verify a hook/function exists in v4. Load whenever using an API not shown in the patterns above.
- **`css-animations.md`** — Working with CSS transitions/keyframes beyond the basic pulse/expand patterns. Multi-property transitions, animation direction, fill modes, complex keyframes.
- **`gestures.md`** — Composing gestures (simultaneous, exclusive, race), pinch/rotation, momentum scrolling, gesture-to-state bridging via `runOnJS`. Load for any non-trivial gesture work.
- **`layout-animations.md`** — Entering/exiting presets, custom layout animations, `Keyframe` API, list-specific gotchas (FlatList, masonry, virtualization), skip-on-mount config.
- **`patterns.md`** — Full recipes for common UI: swipeable rows, accordion, FAB with sub-actions, bottom sheet, animated tab bar, image carousel, skeleton loaders, shake-to-error, snap-to-grid. Load when the request matches a named pattern.
- **`pitfalls.md`** — Debugging. Each entry pairs a symptom (error message or visible misbehavior) with cause and fix.

## Output guidance

- **Match the user's stack signals.** If they're using TypeScript (which the codebase usually indicates), write TS. If they import from `@/components/...`, match that import style. Reanimated's TS types are good — use them (`SharedValue<number>`, `CSSAnimationKeyframes`, `AnimatedStyle`).
- **Prefer the simplest layer that works.** A `transitionDuration` is better than three shared values for a thing that just needs to fade. Don't reach for worklets reflexively.
- **Tune defaults to feel native.** Spring defaults are good for snappy UI. For ambient/decorative motion use longer durations (300–600ms) and softer easing. For high-frequency interactions (tap feedback) keep durations short (120–200ms).
- **Wire up cleanup.** Looping animations driven by shared values should cancel on unmount: `useEffect(() => () => cancelAnimation(sv), [])`. CSS animations clean up automatically.
- **Respect reduced motion.** If the animation is decorative or could cause vestibular issues, gate it on `useReducedMotion()` and fall back to an instant state change.
- **Don't reproduce v3 patterns.** Avoid `useAnimatedGestureHandler` (deprecated; use the modern `Gesture.Pan()` API from Gesture Handler v2+). Don't import worklet utilities from `react-native-reanimated` if they live in `react-native-worklets` in v4.
