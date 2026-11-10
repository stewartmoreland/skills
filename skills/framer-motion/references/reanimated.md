# React Native Reanimated — Full API Reference

This is the deep dive on Reanimated for React Native. Read the relevant section before writing real code for any animation task on mobile.

Current major: **Reanimated 4**. Requires the React Native New Architecture. Worklets ship in a separate package: `react-native-worklets`.

## Table of contents

1. Setup & installation
2. The worklet model
3. Shared values
4. Animated styles
5. Animation primitives (withSpring, withTiming, etc.)
6. Interpolation & derived values
7. Gesture Handler 2 integration
8. Layout animations
9. Scroll handlers
10. Shared element transitions
11. Cross-thread bridges (runOnJS / runOnUI)
12. v3 → v4 migration map
13. Performance & debugging
14. Edge cases & gotchas

---

## 1. Setup & installation

```bash
npm install react-native-reanimated react-native-worklets react-native-gesture-handler
```

**Babel config** (`babel.config.js`):
```js
module.exports = {
  presets: ['module:metro-react-native-babel-preset'],
  plugins: [
    'react-native-worklets/plugin',  // must be LAST in the plugins array
  ],
};
```

**Important:** `react-native-worklets/plugin` replaces the old `react-native-reanimated/plugin`. If you upgraded from v3 and the build breaks, this is usually why.

**Expo:** the plugin is auto-configured via the `react-native-worklets` config plugin. Run `npx expo prebuild` to update native code after installing.

**Architecture requirement:** Reanimated 4 only works on the New Architecture. Verify with:
```
npx react-native config | grep newArchEnabled
```
Apps still on old arch must stay on Reanimated 3.x.

**Gesture Handler root** — wrap your app's root once:
```tsx
import { GestureHandlerRootView } from 'react-native-gesture-handler';
<GestureHandlerRootView style={{ flex: 1 }}>{children}</GestureHandlerRootView>
```

## 2. The worklet model

A worklet is a JavaScript function that the Babel plugin transforms so it can run on a separate JS runtime — the UI thread runtime. This lets animations and gesture callbacks update views without crossing the bridge to the main JS thread.

**Implicit worklets:** functions passed to `useAnimatedStyle`, `useDerivedValue`, gesture callbacks (`Gesture.Pan().onUpdate(...)`), and scroll handlers are automatically tagged as worklets.

**Explicit worklets:** any function can be marked with the `'worklet'` directive:

```ts
function clamp(value: number, min: number, max: number) {
  'worklet';
  return Math.min(Math.max(value, min), max);
}
```

You can call worklets from within other worklets without crossing threads. Calling a non-worklet JS function from inside a worklet requires `runOnJS()` (see section 11).

**What you cannot do in a worklet:**
- Use closures over non-shared JS state safely (the value is captured at worklet creation time and won't update)
- Call most React APIs (setState, hooks, etc.)
- Use `console.log` reliably (it works in dev but crosses threads)
- Use most JS module imports that aren't pure functions

**What you can do in a worklet:**
- Math, basic JS operations, shared-value reads/writes
- Call other worklets
- Use `runOnJS` to schedule JS-thread work
- Use approved Reanimated helpers (`interpolate`, `withSpring`, etc.)

## 3. Shared values

`useSharedValue(initial)` returns an object with a `.value` property that lives on the UI thread.

```tsx
const offset = useSharedValue(0);

// Read/write from JS:
offset.value = 100;
console.log(offset.value);

// Read/write from a worklet (preferred):
const style = useAnimatedStyle(() => ({
  transform: [{ translateX: offset.value }],
}));
```

**Shared values for non-numeric data:**
```tsx
const config = useSharedValue({ x: 0, y: 0, scale: 1 });
config.value = { ...config.value, x: 100 };  // create a new object — Reanimated checks for reference equality
```

**Triggering animations:** assigning a `withSpring`/`withTiming`/etc. result to `.value` starts the animation.
```tsx
offset.value = withSpring(100);
```

**Reading from JS without subscribing to changes:** `offset.value` is always the current value. There's no React subscription — UI updates happen because `useAnimatedStyle` is also on the UI thread.

## 4. Animated styles

`useAnimatedStyle(() => ({ ... }))` is a worklet that returns a style object. It re-runs on the UI thread whenever any shared value it reads changes, and applies the result without re-entering JS.

```tsx
const offset = useSharedValue(0);

const animatedStyle = useAnimatedStyle(() => {
  return {
    transform: [
      { translateY: offset.value },
      { scale: interpolate(offset.value, [0, 200], [1, 1.2]) },
    ],
    opacity: interpolate(offset.value, [0, 100], [1, 0.5], Extrapolation.CLAMP),
  };
});

return <Animated.View style={[styles.box, animatedStyle]} />;
```

**Rules:**
- Must return a style object (or array of objects via spread)
- All transforms go inside the `transform` array; can't have multiple top-level transform props
- Reading a shared value subscribes the style to that value
- Conditional reads (`if (foo) { return { x: bar.value } }`) only subscribe to whatever the worklet actually reads on the current run — if `foo` flips later, the new dependency is subscribed

**Animated.View, Animated.Text, Animated.Image, Animated.ScrollView:** the pre-wrapped components that accept animated styles. For other components, wrap with `Animated.createAnimatedComponent(Component)`.

## 5. Animation primitives

Assign one of these to a shared value's `.value` to start an animation.

### withSpring

```ts
offset.value = withSpring(100, {
  damping: 18,
  stiffness: 200,
  mass: 1,
  velocity: 0,
  overshootClamping: false,
  restDisplacementThreshold: 0.01,
  restSpeedThreshold: 2,
});

// Or the duration-based spring (often easier):
offset.value = withSpring(100, {
  duration: 600,
  dampingRatio: 0.7,  // 1.0 = critically damped (no overshoot), <1 = bouncy
});
```

### withTiming

```ts
offset.value = withTiming(100, {
  duration: 300,
  easing: Easing.bezier(0.32, 0.72, 0, 1),  // or Easing.out(Easing.ease) | Easing.linear | etc.
});
```

### withSequence — chain animations

```ts
offset.value = withSequence(
  withTiming(100, { duration: 200 }),
  withSpring(0, { damping: 12 }),
);
```

### withDelay — delay an animation

```ts
offset.value = withDelay(150, withSpring(100));
```

### withRepeat — repeat N times or forever

```ts
offset.value = withRepeat(
  withTiming(100, { duration: 500 }),
  3,           // count, -1 = infinite
  true,        // reverse on each iteration
);
```

### withDecay — momentum (for drag-end)

```ts
offset.value = withDecay({
  velocity: 500,
  deceleration: 0.998,
  clamp: [-200, 200],
  rubberBandEffect: true,
  rubberBandFactor: 0.6,
});
```

### Animation callbacks

Most animation primitives accept a callback as the last argument:

```ts
offset.value = withSpring(100, {}, (finished) => {
  if (finished) {
    runOnJS(handleComplete)();
  }
});
```

The callback runs on the UI thread; use `runOnJS` to call back into JS-thread code (e.g. setting React state).

### Cancelling animations

Assign a plain number to overwrite an in-flight animation:
```ts
offset.value = 0;  // hard snap
```
Or use `cancelAnimation`:
```ts
cancelAnimation(offset);
```

## 6. Interpolation & derived values

### interpolate

```ts
import { interpolate, Extrapolation } from 'react-native-reanimated';

const opacity = interpolate(
  scrollY.value,
  [0, 100, 200],
  [1, 0.5, 0],
  Extrapolation.CLAMP,    // EXTEND (default) | CLAMP | IDENTITY
);
```

Map an input range to an output range. Used heavily in scroll-driven animations.

### interpolateColor

```ts
import { interpolateColor } from 'react-native-reanimated';

const bg = interpolateColor(
  progress.value,
  [0, 1],
  ['#0f172a', '#22d3ee'],
);
```

Interpolates between color strings (hex, rgb, rgba, hsl). Returns a color string usable in styles.

### useDerivedValue

A shared value computed from other shared values. Stays on the UI thread.

```tsx
const angle = useDerivedValue(() => {
  return Math.atan2(y.value, x.value);
});

// Use angle.value in another animated style:
const style = useAnimatedStyle(() => ({
  transform: [{ rotateZ: `${angle.value}rad` }],
}));
```

Use this for chained math that would otherwise cross threads.

## 7. Gesture Handler 2 integration

Reanimated 4 pairs with `react-native-gesture-handler` v2's `Gesture` API. Callbacks are worklets by default.

```tsx
import { Gesture, GestureDetector } from 'react-native-gesture-handler';

const offset = useSharedValue(0);
const start = useSharedValue(0);

const pan = Gesture.Pan()
  .onStart(() => {
    start.value = offset.value;
  })
  .onUpdate((e) => {
    offset.value = start.value + e.translationY;
  })
  .onEnd((e) => {
    offset.value = withDecay({ velocity: e.velocityY, clamp: [-300, 300] });
  });

const style = useAnimatedStyle(() => ({
  transform: [{ translateY: offset.value }],
}));

return (
  <GestureDetector gesture={pan}>
    <Animated.View style={[styles.box, style]} />
  </GestureDetector>
);
```

**Gesture types:** `Gesture.Pan()`, `Gesture.Tap()`, `Gesture.LongPress()`, `Gesture.Pinch()`, `Gesture.Rotation()`, `Gesture.Fling()`, `Gesture.Hover()` (RN 0.71+), `Gesture.Native()`.

**Composing gestures:**
- `Gesture.Race(g1, g2)` — first to activate wins
- `Gesture.Simultaneous(g1, g2)` — both can run together (pinch + pan for image viewer)
- `Gesture.Exclusive(g1, g2)` — g2 only activates if g1 fails

**Important:** the old `useAnimatedGestureHandler` from Reanimated 3 is **removed in v4**. All gesture code must use the `Gesture` API.

## 8. Layout animations

Reanimated layout animations are entering/exiting/layout props on `Animated.*` components.

### Pre-built entries/exits

```tsx
import Animated, {
  FadeIn, FadeOut,
  SlideInDown, SlideOutUp,
  ZoomIn, ZoomOut,
  BounceIn, BounceOut,
  Layout,
} from 'react-native-reanimated';

<Animated.View
  entering={FadeInDown.duration(400).springify()}
  exiting={SlideOutUp.duration(300)}
  layout={Layout.springify()}
/>
```

**Modifiers:** `.duration(ms)`, `.delay(ms)`, `.springify()`, `.easing(fn)`, `.withCallback(cb)`.

**Layout transitions** (`layout={Layout.springify()}`) animate any layout change on the element — list reorders, size changes, parent flex changes. The element does not need to mount/unmount.

### Custom entries/exits

```tsx
const customEnter = (values: EntryAnimationsValues) => {
  'worklet';
  const animations = {
    opacity: withTiming(1, { duration: 400 }),
    transform: [{ translateY: withSpring(0) }],
  };
  const initialValues = {
    opacity: 0,
    transform: [{ translateY: 50 }],
  };
  return { initialValues, animations };
};

<Animated.View entering={customEnter} />
```

### Stagger via initial delay

For list animations, give each item a delay based on its index:

```tsx
{items.map((item, i) => (
  <Animated.View
    key={item.id}
    entering={FadeInDown.delay(i * 60).springify()}
  />
))}
```

## 9. Scroll handlers

`useAnimatedScrollHandler` runs on the UI thread and feeds shared values.

```tsx
const scrollY = useSharedValue(0);

const scrollHandler = useAnimatedScrollHandler({
  onScroll: (event) => {
    scrollY.value = event.contentOffset.y;
  },
});

return <Animated.ScrollView onScroll={scrollHandler} scrollEventThrottle={16}>...</Animated.ScrollView>;
```

`useScrollOffset(animatedRef)` — read scroll offset from a ref:
```tsx
const scrollRef = useAnimatedRef<Animated.ScrollView>();
const scrollY = useScrollOffset(scrollRef);
```

(In Reanimated 3 this was called `useScrollViewOffset` — renamed in v4.)

## 10. Shared element transitions

Reanimated 4 reintroduced Shared Element Transitions under Fabric. Pair components across screens with `sharedTransitionTag`:

```tsx
// Screen A
<Animated.Image source={photo} sharedTransitionTag="photo-1" />

// Screen B
<Animated.Image source={photo} sharedTransitionTag="photo-1" />
```

When navigating from A to B (with React Navigation native stack on Fabric), the matched tags animate.

Custom shared transitions via `SharedTransition`:
```tsx
const customTransition = SharedTransition.custom((values) => {
  'worklet';
  return {
    width: withSpring(values.targetWidth),
    height: withSpring(values.targetHeight),
  };
});

<Animated.View sharedTransitionTag="x" sharedTransitionStyle={customTransition} />
```

This feature is platform-sensitive — verify on iOS and Android separately when shipping.

## 11. Cross-thread bridges

### runOnJS — call JS-thread code from a worklet

```ts
import { runOnJS } from 'react-native-worklets';

const pan = Gesture.Pan().onEnd((e) => {
  if (e.translationX > 100) {
    runOnJS(handleSwipeRight)();  // function reference, then call
  }
});
```

Use for: setting React state, calling navigation, triggering haptics, anything that's a normal JS function.

### runOnUI — schedule worklet code from JS

```ts
import { runOnUI } from 'react-native-worklets';

const reset = () => {
  runOnUI(() => {
    'worklet';
    offset.value = withSpring(0);
  })();
};
```

Less common — most of the time, assigning to a shared value from JS already schedules UI-thread work.

### runOnUISync — synchronous variant (rare)

```ts
import { runOnUISync } from 'react-native-worklets';
```

Renamed in v4 from `executeOnUIRuntimeSync`. Avoid unless you have a specific reason — it blocks the JS thread.

## 12. v3 → v4 migration map

Most upgrades from Reanimated 3 to 4 hit the same issues. Here's the map:

| v3 | v4 |
|----|----|
| `react-native-reanimated/plugin` (Babel) | `react-native-worklets/plugin` |
| `useAnimatedGestureHandler` | **Removed.** Use Gesture Handler 2's `Gesture` API |
| `useScrollViewOffset` | `useScrollOffset` (old name deprecated, still works) |
| `executeOnUIRuntimeSync` | `runOnUISync` from `react-native-worklets` |
| `runOnJS`, `runOnUI` from `react-native-reanimated` | Same functions, now from `react-native-worklets` (both imports work) |
| Old architecture | Not supported — stay on v3 or migrate to New Arch |
| react-native-v8 engine | Not supported — use Hermes |

**Build failure after upgrade?** 90% of the time: missing `react-native-worklets` install, or you forgot to update `babel.config.js`.

## 13. Performance & debugging

**Profiling:**
- Hermes Sampling Profiler — record a trace, open in Chrome DevTools, find flame graph spikes
- React DevTools Profiler — for component re-render issues
- For native frame drops, use Flipper or Xcode Instruments / Android Studio Profiler

**Common perf wins:**
- Move work into worklets. Every `runOnJS` is a cost; batch them when possible.
- Use `useDerivedValue` for chained shared-value math. Don't recompute inside multiple `useAnimatedStyle` calls.
- For long lists, use `FlashList` (replaces `FlatList` in 2026 perf-oriented stacks) and per-item `entering` animations rather than animating from a parent shared value.
- Don't subscribe to a shared value in `useAnimatedStyle` if you don't read it — every subscription costs.
- Avoid animating layout-triggering properties (`width`, `height`, padding/margin on items in a list). Prefer `transform` + `scale`.

**Debugging worklets:**
- `console.log` works in dev but is bridged — don't leave in production
- For values, use a `useDerivedValue` that exposes the value to `useAnimatedStyle` and inspect the resulting style in React DevTools
- Crash with "tried to synchronously call function from a different thread" = JS function called from worklet without `runOnJS`

## 14. Edge cases & gotchas

**"tried to synchronously call function from a different thread."** A JS function was called inside a worklet without `runOnJS`. Find the call, wrap with `runOnJS(fn)()`.

**Worklet captures stale state.** Closure variables in worklets are captured by value at worklet creation. If you reference a React state in a worklet, it'll be the value at the time the worklet was defined. Move the state into a shared value, or recompute inside the worklet from a shared value.

**Animation doesn't start when assigning to `.value`.** You assigned a plain number or the wrong type. `withSpring(100)` is required; bare `offset.value = 100` is an instant snap.

**Gestures don't fire on Android but work on iOS.** Missing `GestureHandlerRootView` wrapper at the app root, or a `View` between the gesture target and the root is intercepting touches.

**Spring oscillates forever / never settles.** `damping` is too low or thresholds are too tight. Raise damping, or switch to duration-based: `withSpring(100, { duration: 400, dampingRatio: 0.7 })`.

**Layout animation doesn't play.** The element isn't actually mounting/unmounting from React's view. With `entering`, the component needs a stable key and must be newly mounted. For `layout` (transitions on existing elements), the element's parent must be measurable.

**FlatList items don't animate on remount.** `FlatList` recycles cells; layout animations don't fire on virtualized lists reliably. Use `FlashList` with item keys or animate scroll position instead.

**Reanimated upgrade broke gesture handling.** Old `useAnimatedGestureHandler` was removed in v4. Migrate to `Gesture.Pan()` / `Gesture.Tap()` etc. wrapped in `<GestureDetector>`.

**Strict-mode double-render breaks shared values.** Shared values are stable across renders — create them via `useSharedValue`, never inline. If you see weird values in dev, check whether you're recreating shared values on every render.

**`useScrollOffset` returns 0 forever.** The ref must be from `useAnimatedRef`, not `useRef`. And it must be attached to an `Animated.ScrollView` or `Animated.FlatList`, not a plain `ScrollView`.
