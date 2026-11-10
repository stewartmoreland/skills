# Gestures & Worklets

The imperative side of Reanimated. Use this layer when an animation must follow a continuous input — a finger drag, scroll position, sensor reading, or per-frame calculation. Pairs `react-native-gesture-handler` (gestures) with Reanimated (animated values and styles).

The modern Gesture Handler v2+ API replaces the older `useAnimatedGestureHandler` from Reanimated v2 entirely. If you see `useAnimatedGestureHandler` in code, that's a v2 pattern — rewrite it.

## Setup

```tsx
// Root of the app — typically App.tsx or _layout.tsx
import { GestureHandlerRootView } from 'react-native-gesture-handler';

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      {/* rest of the tree */}
    </GestureHandlerRootView>
  );
}
```

Without `GestureHandlerRootView` at the root, gestures will silently not fire on Android.

## The mental model

A gesture is built with `Gesture.<Type>()`, attached to a tree node via `<GestureDetector gesture={...}>`, and configured with worklet callbacks like `.onChange()`, `.onEnd()`. Inside those callbacks, you write to shared values; a `useAnimatedStyle` elsewhere reads them and updates the view. The whole loop runs on the UI thread — no JS-thread roundtrips per frame.

```
User finger → GestureHandler (native) → worklet callback (UI thread)
  → updates SharedValue (UI thread, sync)
  → useAnimatedStyle re-evaluates (UI thread)
  → view updates (UI thread)
```

JS-thread state stays out of the hot loop entirely. That's why this approach is smooth even when JS is busy.

## Gesture types

| Type | Use for |
|---|---|
| `Gesture.Pan()` | Drag, swipe, pull-down-to-refresh, dismissible cards |
| `Gesture.Tap()` | Tap with feedback animation |
| `Gesture.LongPress()` | Press-and-hold interactions, context menus |
| `Gesture.Pinch()` | Two-finger zoom |
| `Gesture.Rotation()` | Two-finger rotate |
| `Gesture.Fling()` | Quick directional flick |
| `Gesture.ForceTouch()` | iOS 3D Touch (rarely needed now) |
| `Gesture.Manual()` | Build a custom recognizer from raw events |
| `Gesture.Hover()` | Pointer hover (web, iPad with trackpad/cursor) |

## Anatomy of a Pan gesture

```tsx
const offset = useSharedValue({ x: 0, y: 0 });
const start = useSharedValue({ x: 0, y: 0 });

const pan = Gesture.Pan()
  .onBegin(() => {
    // Touch down — save the starting offset
    start.value = { x: offset.value.x, y: offset.value.y };
  })
  .onUpdate((e) => {
    // Each frame of movement; relative to start of gesture
    offset.value = {
      x: start.value.x + e.translationX,
      y: start.value.y + e.translationY,
    };
  })
  .onEnd((e) => {
    // Lift — animate to rest with momentum
    offset.value = {
      x: withDecay({ velocity: e.velocityX, clamp: [-200, 200] }),
      y: withDecay({ velocity: e.velocityY, clamp: [-400, 400] }),
    };
  });
```

Note: you can't assign `withDecay` to an object property like that directly — you'd actually do two separate shared values for x and y, or apply `withDecay` to the wrapping useDerivedValue. See pattern below.

### Cleaner two-axis pan

```tsx
const x = useSharedValue(0);
const y = useSharedValue(0);

const pan = Gesture.Pan()
  .onChange((e) => {
    // .onChange gives delta since last frame; doesn't need a "start" capture
    x.value += e.changeX;
    y.value += e.changeY;
  })
  .onEnd(() => {
    x.value = withSpring(0);
    y.value = withSpring(0);
  });

const style = useAnimatedStyle(() => ({
  transform: [{ translateX: x.value }, { translateY: y.value }],
}));
```

`.onChange` is usually simpler than `.onUpdate` because it gives per-frame deltas (`changeX`, `changeY`) instead of total translation from gesture start.

## Common gesture callbacks

| Callback | Fires when |
|---|---|
| `.onBegin(handler)` | Touch lands and the gesture is recognized as a candidate |
| `.onStart(handler)` | Gesture is officially started (after activation criteria met) |
| `.onUpdate(handler)` | Every frame while active; full event with cumulative translation |
| `.onChange(handler)` | Every frame while active; deltas (`changeX`, `changeY`) since last frame |
| `.onEnd(handler)` | Released after activation — animate to rest here |
| `.onFinalize(handler)` | Always fires at end, even on cancel — use for cleanup |
| `.onTouchesDown/Up/Move/Cancelled` | Lower-level multi-touch info |

All callbacks are auto-workletized. You do not need the `'worklet'` directive.

## Gesture configuration

Pan gestures have activation thresholds. Tune these to avoid stealing the parent ScrollView's touches:

```tsx
Gesture.Pan()
  .minDistance(10)               // px before activation
  .activeOffsetX([-20, 20])      // only activate after this horizontal range
  .failOffsetY([-10, 10])        // fail (don't activate) if vertical movement exceeds this
  .averageTouches(true)
  .enableTrackpadTwoFingerGesture(true)
```

For a card swipeable left/right inside a vertically scrolling list, `activeOffsetX([-20, 20]).failOffsetY([-10, 10])` is the recipe — the swipe only takes over when motion is clearly horizontal.

## Composing gestures

Multiple gestures on the same element with different relationships:

```tsx
// Simultaneous: both can be active at once (pan AND pinch on an image)
const combined = Gesture.Simultaneous(panGesture, pinchGesture);

// Race: whichever activates first wins (tap OR long-press)
const tapOrHold = Gesture.Race(tapGesture, longPressGesture);

// Exclusive: try in order; later ones only if earlier fail
const exclusive = Gesture.Exclusive(doubleTap, singleTap);
```

Pass the composed gesture to `<GestureDetector gesture={combined}>`.

## Bridging back to React (`runOnJS`)

Gesture callbacks run on the UI thread. To trigger React state updates, navigation, haptics, or any JS-thread side effect, wrap the JS function with `runOnJS`:

```tsx
import { runOnJS } from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';

const haptic = () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

const pan = Gesture.Pan()
  .onEnd((e) => {
    if (Math.abs(e.translationX) > DISMISS_THRESHOLD) {
      runOnJS(haptic)();
      runOnJS(onDismiss)();
    } else {
      translateX.value = withSpring(0);
    }
  });
```

`runOnJS(fn)(arg1, arg2)` — note the curried call. The arguments are serialized across threads, so they must be primitives or plain objects (no functions, no class instances).

## Worklets — the deeper rules

A worklet is a JavaScript function that runs in a separate UI-thread runtime. The Worklets Babel plugin (`react-native-worklets/plugin`) transforms any function with `'worklet'` as its first line into a serializable form that can be sent to the UI runtime.

```ts
function clampPositive(n: number) {
  'worklet';
  return n < 0 ? 0 : n;
}
```

Functions used inside hook callbacks (`useAnimatedStyle`, `useAnimatedReaction`, gesture handlers) are auto-workletized — you don't add the directive yourself. You only need it for standalone helpers you want to call from a worklet.

### Closure capture

Worklets capture variables from their lexical scope and copy them to the UI runtime when they're created. After the copy, the UI-thread version cannot see updates to JS-thread variables.

```ts
let multiplier = 2;  // JS-thread variable
function double() {
  'worklet';
  return value.value * multiplier;
}
runOnUI(double)();
multiplier = 3;       // UI-thread copy still sees 2
```

If you need the worklet to read live state, put it in a shared value:

```ts
const multiplier = useSharedValue(2);
function double() {
  'worklet';
  return value.value * multiplier.value; // always live
}
```

This is the single most common worklet pitfall. When in doubt, use a shared value.

### Calling JS functions from worklets

Only via `runOnJS`. A direct call will throw `Tried to synchronously call a non-worklet function on the UI thread`.

### Calling worklets from JS

`runOnUI(worklet)()`. Don't call worklets directly from JS code — they need to be scheduled.

### Reading shared values on JS thread

`sv.value` from JS is a synchronous bridge call. Cheap when occasional, expensive in hot loops (render functions, `useEffect` deps, etc.). If you need to react to changes on JS, use `useAnimatedReaction` + `runOnJS` instead of polling `.value`.

## `useAnimatedReaction`

When a UI-thread condition should trigger JS-thread work — for example, fire `onDismiss` when translation crosses a threshold.

```ts
useAnimatedReaction(
  () => Math.abs(translateX.value) > DISMISS_THRESHOLD,
  (passed, prev) => {
    if (passed && !prev) {
      runOnJS(onDismiss)();
    }
  },
);
```

The `prepare` function (first arg) runs on every change to its dependencies; the `react` function (second arg) runs only when the value it returned changed. This avoids spamming `runOnJS`.

## `useFrameCallback` — per-frame control

For animations that can't be expressed with `withTiming`/`withSpring`/`withDecay` — custom physics, manual interpolation against external state, etc.

```ts
const x = useSharedValue(0);
const velocity = useSharedValue(100); // px/sec

useFrameCallback((info) => {
  const dt = (info.timeSincePreviousFrame ?? 0) / 1000;
  x.value += velocity.value * dt;
  velocity.value *= 0.98; // simple drag
  if (Math.abs(velocity.value) < 0.5) velocity.value = 0;
});
```

Returns `{ start, stop, setActive, isActive }`. Call `setActive(false)` to pause; doing so is much cheaper than leaving it running and gating internally.

## Gesture + worklet hygiene

- Keep gesture callbacks lean. They run every frame. Heavy logic (especially calls to non-worklet utilities) belongs in `runOnJS` or precomputed shared values.
- For "throw a card off-screen" animations, prefer `withDecay` with `clamp` + a velocity threshold over manual integration. The library's physics are tuned and consistent.
- For two-axis gestures, two separate shared values are usually cleaner than one object shared value. `.modify()` is needed for object updates and adds friction.
- When debugging, add `runOnJS(console.log)('label', sharedValue.value)` inside gesture callbacks. Don't `console.log` directly — it works but is silently inconsistent across runtimes.
