# Reanimated v4 API Reference

Lookup reference for v4 hooks, animation functions, utilities, and worklet primitives. Each entry includes signature, key params, return type, and a minimal usage example. Load this when you need to verify an API's exact shape or check whether it exists in v4.

## Table of contents

1. Core hooks
2. Animation functions (`withX`)
3. Scroll APIs
4. Layout animation primitives
5. Utility functions
6. Advanced APIs (frame callbacks, reactions, measure)
7. Device APIs (sensor, keyboard, reduced motion)
8. Worklet primitives (from `react-native-worklets`)
9. Removed / renamed in v4

---

## 1. Core hooks

### `useSharedValue<T>(initial: T): SharedValue<T>`

Creates a value that lives on both threads. Read/write via `.value`. Writes from the UI thread (inside a worklet) are synchronous; writes from the JS thread are scheduled.

```ts
const x = useSharedValue(0);
// In a worklet:
x.value = 100;
// In JS code:
x.value = 50; // async — won't be readable immediately
```

The hook also returns `.get()` and `.set()` methods that are functionally equivalent to `.value` access; `.value` is the idiomatic style.

### `useAnimatedStyle(updater: () => Style, deps?: DependencyList): AnimatedStyle`

Returns a style object whose properties are computed in a worklet from shared values. Reanimated re-runs the updater whenever any shared value it reads changes.

```ts
const style = useAnimatedStyle(() => ({
  transform: [{ translateX: x.value }],
  opacity: x.value > 0 ? 1 : 0.5,
}));
```

Must return one plain object. Don't return arrays. Don't put logic with side effects in the updater.

### `useAnimatedProps(updater: () => Props, deps?: DependencyList): AnimatedProps`

Like `useAnimatedStyle` but for non-style props (e.g., SVG `d` attribute, `text` content of a `TextInput`, `stroke`). Pair with `Animated.createAnimatedComponent` for third-party components.

```ts
const animatedProps = useAnimatedProps(() => ({ text: `${counter.value}` }));
return <AnimatedTextInput animatedProps={animatedProps} editable={false} />;
```

### `useDerivedValue<T>(updater: () => T, deps?: DependencyList): SharedValue<T>`

Creates a read-only shared value derived from other shared values. Recomputes whenever its dependencies change. Use this instead of reading `.value` outside a worklet when you need a value computed from others.

```ts
const progress = useSharedValue(0);
const percent = useDerivedValue(() => Math.round(progress.value * 100));
```

### `useAnimatedRef<T>(): AnimatedRef<T>`

A ref that can be passed to `useScrollOffset`, `measure`, `scrollTo`, etc. Attach to scroll views and animated components that need worklet-accessible references.

```ts
const ref = useAnimatedRef<Animated.ScrollView>();
return <Animated.ScrollView ref={ref}>{...}</Animated.ScrollView>;
```

### `createAnimatedComponent(Component)`

Wraps a regular component so it accepts animated styles/props. Built-in `Animated.View`, `Animated.Text`, `Animated.Image`, `Animated.ScrollView`, `Animated.FlatList` already exist — only reach for this for third-party or custom components.

```ts
const AnimatedPressable = Animated.createAnimatedComponent(Pressable);
```

### `cancelAnimation(sharedValue)`

Stops any running animation on a shared value at its current position. Use in cleanup effects to halt looping animations.

```ts
useEffect(() => () => cancelAnimation(rotation), []);
```

---

## 2. Animation functions

All of these are worklets that produce animated values. They go on the right-hand side of a shared-value assignment, never called bare.

### `withTiming(toValue, config?, callback?)`

Linear or eased interpolation to a target.

```ts
x.value = withTiming(100, { duration: 300, easing: Easing.out(Easing.cubic) });
```

Config: `duration` (ms, default 300), `easing` (default `Easing.inOut(Easing.quad)`), `reduceMotion` (`ReduceMotion.System` | `Always` | `Never`).

### `withSpring(toValue, config?, callback?)`

Physics-based spring. Defaults feel like iOS UISpring; tweak `damping`, `stiffness`, `mass` for snappier/softer feel. v4 changed the stop threshold to an energy-based test — small-feel differences from v3.

```ts
x.value = withSpring(0, { damping: 12, stiffness: 180, mass: 1 });
```

Common configs:
- Snappy UI: `damping: 20, stiffness: 250`
- Bouncy: `damping: 8, stiffness: 100`
- Soft / heavy: `damping: 30, mass: 2`

### `withDecay(config, callback?)`

Momentum animation — value continues with velocity and decelerates. The natural pair to a pan-gesture release.

```ts
x.value = withDecay({
  velocity: event.velocityX,
  deceleration: 0.997,
  clamp: [0, screenWidth],
  rubberBandEffect: true,
});
```

### `withSequence(...animations)`

Chain animations one after another.

```ts
scale.value = withSequence(
  withTiming(1.1, { duration: 120 }),
  withTiming(1.0, { duration: 120 }),
);
```

### `withRepeat(animation, numberOfReps?, reverse?, callback?)`

Repeats an animation. `numberOfReps = -1` for infinite. `reverse = true` alternates direction (yo-yo).

```ts
rotation.value = withRepeat(withTiming(360, { duration: 1500 }), -1);
```

### `withDelay(delayMs, animation)`

Delays the start.

```ts
opacity.value = withDelay(200, withTiming(1));
```

### `withClamp({ min?, max? }, animation)`

Constrains an animation's output range. Useful for spring overshoots you want to bound.

```ts
y.value = withClamp({ min: 0, max: 300 }, withSpring(target));
```

---

## 3. Scroll APIs

### `useScrollOffset(animatedRef): SharedValue<number>`

The v4 name for what was `useScrollViewOffset` in v3. Returns the live scroll Y offset as a shared value. `useScrollViewOffset` still works as an alias but is deprecated.

```ts
const scrollRef = useAnimatedRef<Animated.ScrollView>();
const scrollY = useScrollOffset(scrollRef);
```

### `useAnimatedScrollHandler(handlers)`

For when you need more than just the offset — access to velocity, content size, begin/end events.

```ts
const handler = useAnimatedScrollHandler({
  onScroll: (event) => { y.value = event.contentOffset.y; },
  onBeginDrag: () => { /* ... */ },
  onEndDrag: (event) => { /* ... */ },
  onMomentumEnd: () => { /* ... */ },
});
return <Animated.ScrollView onScroll={handler} scrollEventThrottle={16}>{...}</Animated.ScrollView>;
```

### `scrollTo(animatedRef, x, y, animated)`

A worklet — scroll a referenced ScrollView from the UI thread. Useful for "snap to next item" after a gesture release.

```ts
const onSnap = () => {
  'worklet';
  scrollTo(scrollRef, 0, targetY, true);
};
```

---

## 4. Layout animation primitives

Import from `react-native-reanimated`. Pass on `Animated.View` via `entering`, `exiting`, or `layout`.

### Entering presets

`FadeIn`, `FadeInUp`, `FadeInDown`, `FadeInLeft`, `FadeInRight`,
`SlideInUp`, `SlideInDown`, `SlideInLeft`, `SlideInRight`,
`ZoomIn`, `ZoomInRotate`, `ZoomInEasyDown`, `ZoomInEasyUp`,
`BounceIn`, `BounceInUp`, `BounceInDown`, `BounceInLeft`, `BounceInRight`,
`FlipInEasyX`, `FlipInEasyY`, `FlipInXDown`, `FlipInYRight`,
`LightSpeedInLeft`, `LightSpeedInRight`,
`PinwheelIn`, `RollInLeft`, `RollInRight`, `RotateInDownLeft`, `RotateInUpRight`,
`StretchInX`, `StretchInY`.

Each accepts chainable modifiers:

```ts
FadeIn.duration(300).delay(100).easing(Easing.out(Easing.exp))
SlideInRight.springify().damping(15)
```

### Exiting presets

Same names with `Out` instead of `In`: `FadeOut`, `SlideOutLeft`, `ZoomOut`, `BounceOut`, etc.

### Layout transitions

`LinearTransition`, `FadingTransition`, `SequencedTransition`, `JumpingTransition`, `CurvedTransition`, `EntryExitTransition`. Modifiers: `.duration()`, `.springify()`, `.damping()`, `.stiffness()`.

```ts
<Animated.View layout={LinearTransition.springify().damping(18)} />
```

### `Keyframe`

For custom entering/exiting animations defined by keyframes:

```ts
const customEnter = new Keyframe({
  0:   { opacity: 0, transform: [{ scale: 0.5 }] },
  50:  { opacity: 0.8, transform: [{ scale: 1.05 }] },
  100: { opacity: 1, transform: [{ scale: 1 }] },
}).duration(400);

<Animated.View entering={customEnter} />
```

---

## 5. Utility functions

### `interpolate(value, inputRange, outputRange, extrapolation?)`

Maps a value from one range to another. Worklet-only — call inside `useAnimatedStyle`/`useDerivedValue`.

```ts
const opacity = interpolate(scrollY.value, [0, 100], [1, 0], Extrapolation.CLAMP);
```

Extrapolation options: `Extrapolation.EXTEND` (default), `CLAMP`, `IDENTITY`. Can be specified per-edge: `{ extrapolateLeft: 'clamp', extrapolateRight: 'extend' }`.

### `interpolateColor(value, inputRange, colorRange, colorSpace?, options?)`

Like `interpolate` but for colors. Accepts hex, rgb, hsl strings.

```ts
const bg = interpolateColor(progress.value, [0, 1], ['#fee2e2', '#dc2626']);
```

Color space defaults to `'RGB'`; `'HSV'` for more vivid transitions through saturated mids.

### `clamp(value, min, max)`

Worklet helper. Clamps a value between bounds.

```ts
const safe = clamp(translateX.value, -100, 100);
```

### `getRelativeCoords(animatedRef, x, y)`

Converts screen coords to coords relative to a referenced component. Worklet.

### `Easing`

Standard easing functions: `Easing.linear`, `Easing.ease`, `Easing.quad`, `Easing.cubic`, `Easing.bezier(x1, y1, x2, y2)`, `Easing.in(fn)`, `Easing.out(fn)`, `Easing.inOut(fn)`, `Easing.bounce`, `Easing.elastic(bounciness)`, `Easing.exp`, `Easing.sin`, `Easing.circle`, `Easing.back(s)`, `Easing.steps(n)`.

```ts
withTiming(100, { easing: Easing.bezier(0.25, 0.1, 0.25, 1) });
```

---

## 6. Advanced APIs

### `useAnimatedReaction(prepare, react, deps?)`

Subscribes to changes in computed values. Runs `react(current, previous)` whenever `prepare()` returns a new value. Use when you need to fire side effects (including bridging back to JS) when a shared value crosses a threshold.

```ts
useAnimatedReaction(
  () => translateY.value > THRESHOLD,
  (passed, prev) => {
    if (passed && !prev) runOnJS(onPullToRefresh)();
  },
);
```

### `useFrameCallback(callback, autostart?)`

Runs a worklet on every frame. For physics, manual interpolation, custom timing not expressible with `withTiming`/`withSpring`.

```ts
useFrameCallback((info) => {
  // info.timeSincePreviousFrame, info.timeSinceFirstFrame, info.timestamp
  x.value += velocity.value * (info.timeSincePreviousFrame ?? 0) / 1000;
});
```

Returns `{ start, stop, setActive, isActive }` for manual control.

### `measure(animatedRef): Measured`

Synchronously measures a component from the UI thread. Returns `{ x, y, width, height, pageX, pageY }`. Worklet only.

```ts
const onLongPress = () => {
  'worklet';
  const m = measure(boxRef);
  if (m) { /* use m.width, m.pageY, etc. */ }
};
```

---

## 7. Device APIs

### `useReducedMotion(): boolean`

Returns the system Reduce Motion setting. Use to gate decorative animations.

```ts
const reducedMotion = useReducedMotion();
const style = useAnimatedStyle(() => ({
  transform: [{ scale: reducedMotion ? 1 : withSpring(target.value) }],
}));
```

### `ReducedMotionConfig`

A component that lets you override system reduced motion behavior for a subtree.

### `useAnimatedSensor(sensorType, config?)`

Subscribes to device motion sensors. `SensorType.ACCELEROMETER`, `GYROSCOPE`, `GRAVITY`, `MAGNETIC_FIELD`, `ROTATION`.

```ts
const sensor = useAnimatedSensor(SensorType.GYROSCOPE, { interval: 16 });
// sensor.sensor.value.x / .y / .z available in worklets
```

### `useAnimatedKeyboard()`

Deprecated in v4 — use the keyboard APIs from `react-native-keyboard-controller` for current work. Still functional for backward compat.

---

## 8. Worklet primitives (`react-native-worklets`)

In v4 these moved out of `react-native-reanimated` and into `react-native-worklets`. Most code doesn't need to import from worklets directly because the directive (`'worklet'`) is enough, but for cross-thread calls you'll touch these.

### `runOnJS(jsFunction)`

From inside a worklet, returns a JS-thread-callable wrapper. Use to call React setState, navigate, fire haptics, etc.

```ts
const pan = Gesture.Pan().onEnd((event) => {
  if (Math.abs(event.translationX) > 100) {
    runOnJS(onDismiss)();
  }
});
```

Import from `react-native-reanimated` (re-exported) or `react-native-worklets`.

### `runOnUI(workletFn)`

From JS, schedule a worklet on the UI thread.

```ts
const startUiWork = () => runOnUI(() => {
  'worklet';
  console.log('on UI thread');
})();
```

### `scheduleOnUI(workletFn)`

Lower-level alternative to `runOnUI`. Prefer `runOnUI` unless you have a specific reason.

### The `'worklet'` directive

The first line of a function. Tells the Babel plugin to make it serializable to the UI runtime.

```ts
function clampPositive(n: number) {
  'worklet';
  return n < 0 ? 0 : n;
}
```

Hook callbacks (`useAnimatedStyle`, `useAnimatedReaction`, gesture handlers) automatically inject this — you only need it for standalone helpers.

---

## 9. Removed / renamed in v4

- `useAnimatedGestureHandler` — removed/deprecated. Use the modern Gesture Handler v2+ API (`Gesture.Pan()`, `GestureDetector`).
- `useScrollViewOffset` → renamed to `useScrollOffset`. Old name is a deprecated alias.
- `react-native-reanimated/plugin` (Babel) → renamed to `react-native-worklets/plugin`. Old name still works for now.
- Legacy Architecture (Paper) support — dropped. New Architecture (Fabric) only.
- `react-native-v8` engine — dropped. Hermes only.
- Several rarely-used helpers from v2/v3 era have been removed or replaced with no-ops; the official migration guide (https://docs.swmansion.com/react-native-reanimated/docs/guides/migration-from-3.x) is the authoritative list.

### New in v4

- CSS Animations: `animationName`, `animationDuration`, `animationDelay`, `animationTimingFunction`, `animationDirection`, `animationIterationCount`, `animationFillMode`, `animationPlayState`. See `css-animations.md`.
- CSS Transitions: `transitionProperty`, `transitionDuration`, `transitionDelay`, `transitionTimingFunction`, `transitionBehavior`. See `css-animations.md`.
- `withClamp` — bounds the output range of a wrapped animation.
- Shared Element Transitions on Fabric (4.2+, experimental, behind a feature flag). Not yet production-ready.
- New CSS-style transforms and filters (4.2+).
