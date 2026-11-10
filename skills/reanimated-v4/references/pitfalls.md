# Pitfalls & Debugging

A symptom-keyed reference for things that commonly go wrong with Reanimated v4 code. When the user reports "this doesn't work" or shows you an error, scan this file for the matching entry. Each one pairs a symptom with the cause and the fix.

## Installation & build-time issues

### "Reanimated 2 failed to create a worklet, maybe you forgot to add Reanimated's Babel plugin?"

**Cause:** The Babel plugin isn't configured, or Metro bundler is using stale cache after an install.

**Fix:** Verify `babel.config.js` lists `react-native-worklets/plugin` **last**:

```js
module.exports = {
  presets: ['module:@react-native/babel-preset'],
  plugins: [
    // ... other plugins
    'react-native-worklets/plugin', // MUST be last
  ],
};
```

The plugin must be last because it transforms function bodies and needs to run after other plugins have done their work. Then clear Metro cache: `npx react-native start --reset-cache` (or `expo start -c`).

### "Reanimated requires the New Architecture"

**Cause:** Reanimated v4 doesn't support the legacy renderer (Paper).

**Fix:** Enable Fabric. For bare RN, set `newArchEnabled=true` in `gradle.properties` and use the appropriate iOS Podfile flag. For Expo, set `"newArchEnabled": true` in `app.json` under the platform-specific keys. Requires RN 0.76+. If migration isn't feasible, stay on Reanimated 3.x.

### "Native module RNWorklets not found" or similar native module errors

**Cause:** `react-native-worklets` isn't installed, or pods/gradle weren't re-synced after install.

**Fix:** `npm install react-native-worklets`, then `cd ios && pod install` for iOS, and rebuild from scratch (not a Metro restart — a full native rebuild). For Expo dev clients, run `npx expo prebuild --clean` then rebuild.

### Worklets transformed with old plugin version

Error mentions outdated Reanimated Babel plugin.

**Cause:** A dependency was pre-built with an old version of the plugin embedded.

**Fix:** Reset Metro cache first. If that fails, find the offending library (error usually names a file path) and check its docs for a v4-compatible release.

---

## Runtime errors

### `ReanimatedError: Tried to synchronously call a non-worklet function on the UI thread`

**Cause:** A worklet (gesture handler, `useAnimatedStyle`, etc.) called a regular JS function directly.

**Fix:** Wrap with `runOnJS`:

```ts
// ❌ Wrong
const pan = Gesture.Pan().onEnd(() => {
  setIsOpen(true); // JS function called on UI thread
});

// ✅ Right
const pan = Gesture.Pan().onEnd(() => {
  runOnJS(setIsOpen)(true);
});
```

Common offenders: `setState`, navigation calls, alert/toast triggers, console.log in some setups, third-party SDK calls (haptics, analytics).

### "Reading from `_value` during component render is not supported"

**Cause:** A shared value's `.value` was accessed during render, not inside a callback.

**Fix:** Move the read into `useAnimatedStyle`, `useDerivedValue`, or an event handler. If you need the current value reactively in React state, use `useAnimatedReaction` + `runOnJS(setState)`.

```ts
// ❌ Wrong
function Component() {
  const sv = useSharedValue(0);
  return <Text>{sv.value}</Text>; // read during render
}

// ✅ Right — use animated props
const animatedProps = useAnimatedProps(() => ({ text: `${sv.value}` }));
return <AnimatedTextInput animatedProps={animatedProps} editable={false} />;
```

### "Tried to modify key `prop` of an object which has been already passed to a worklet"

**Cause:** A plain JS object was captured by closure into a worklet, then mutated on the JS side later. The worklet snapshot is immutable after creation.

**Fix:** Use a shared value for any object that needs to be mutated and observed from a worklet.

```ts
// ❌ Wrong
const config = { speed: 1 };
function worklet() { 'worklet'; return config.speed; }
config.speed = 2; // warning

// ✅ Right
const config = useSharedValue({ speed: 1 });
function worklet() { 'worklet'; return config.value.speed; }
config.value = { ...config.value, speed: 2 };
```

### Animation runs but value never updates after one or two frames

**Cause:** Mutating a shared value's object/array contents directly. Reanimated detects writes to `.value` (replacement), not internal mutations.

**Fix:** Replace the whole value, or use `.modify()`:

```ts
// ❌ Wrong
positions.value.push({ x, y });

// ✅ Right — replace
positions.value = [...positions.value, { x, y }];

// ✅ Also right — modify
positions.modify((v) => {
  'worklet';
  v.push({ x, y });
  return v;
});
```

---

## "It just doesn't animate"

### Style change but no animation

**Cause:** The component isn't an animated component.

**Fix:** Use `Animated.View`, not `View`. For third-party components, wrap with `Animated.createAnimatedComponent`.

### CSS transition declared but property snaps

**Cause:** Either the property isn't in `transitionProperty`, the value isn't actually changing (React bailed out of the re-render), or the property isn't animatable.

**Fix:** Verify `transitionProperty` lists the exact property name (and matches camelCase: `backgroundColor`, not `background-color`). Add `transitionProperty: 'all'` temporarily to confirm the property is animatable. Verify the style value is genuinely different across renders (`console.log` the style at render time).

### Layout animation never fires

**Cause:** The view's on-screen rectangle isn't actually changing. Layout animations only respond to layout-driven position/size changes, not transforms.

**Fix:** Confirm that something the layout engine sees is changing — siblings added, padding/margin shifting, flex weights altering. If you want movement triggered by your own logic, use a worklet-driven transform instead, or change actual layout properties (height, width, marginTop).

### Entering animation fires on every list scroll

**Cause:** FlatList virtualizes — items mount/unmount as they scroll into and out of view, re-firing `entering`.

**Fix:** Remove `entering` from FlatList rows. Use `itemLayoutAnimation` on `Animated.FlatList` instead, or accept that virtualized rows don't get enter animations.

### Animation doesn't run on first mount (only on subsequent updates)

**Cause:** The initial shared value already equals the target.

**Fix:** Initialize with a "starting" value and animate to the destination:

```ts
// ❌ Wrong — opacity starts at 1, animating to 1 is a no-op
const opacity = useSharedValue(1);
useEffect(() => { opacity.value = withTiming(1); }, []);

// ✅ Right
const opacity = useSharedValue(0);
useEffect(() => { opacity.value = withTiming(1); }, []);
```

For mount animations, prefer `entering={FadeIn}` over manual shared values — less code and handles this automatically.

---

## Performance issues

### "JS thread blocked for ~500ms" / spinner stutters on screen mount

**Cause:** Reading `.value` from the JS thread (component body, useEffect deps, useCallback deps). Each read is a synchronous bridge call.

**Fix:** Don't read `.value` outside worklets. If you need the value on JS, derive it via `useDerivedValue` and read that derived value through `useAnimatedReaction` → `runOnJS(setState)` only when it actually changes.

```ts
// ❌ Wrong
useEffect(() => {
  if (translateX.value > 100) doThing();
}, [translateX.value]); // reads .value on every render

// ✅ Right
useAnimatedReaction(
  () => translateX.value > 100,
  (passed, prev) => { if (passed && !prev) runOnJS(doThing)(); },
);
```

### Frame drops during long lists with layout animations

**Cause:** Each row running a `layout` transition + every row re-measuring on scroll.

**Fix:** Use `itemLayoutAnimation` on `Animated.FlatList` (single coordinator). Consider FlashList. Disable layout transitions on rows that don't actually reorder.

### Animation feels janky on Android only

**Cause:** A few common offenders:
- `shadowOpacity`/elevation animations are expensive on Android — minimize or remove
- Animating `width`/`height` triggers per-frame layout — switch to transform-based scaling where possible
- Hermes is required; legacy JSC is not supported in v4

**Fix:** Audit the animated styles. Transform-only animations (translate, scale, rotate, opacity) are the cheapest and most consistent across platforms.

### `scrollEventThrottle` not set on Animated.ScrollView

**Cause:** Without `scrollEventThrottle={16}`, the scroll handler fires at native cadence which may be too coarse for smooth interpolation.

**Fix:** Always set `scrollEventThrottle={16}` (60fps target) or `1` (max frequency) on `Animated.ScrollView`/`Animated.FlatList` when using scroll-driven animations.

---

## Logical / API mistakes

### `useAnimatedStyle` returning an array

**Cause:** Returned an array of style objects.

**Fix:** Return a single object. Compose multiple animated styles in the component using `style={[base, animated1, animated2]}`.

```ts
// ❌ Wrong
useAnimatedStyle(() => [{ opacity: o.value }, { transform: [...] }]);

// ✅ Right
const opacityStyle = useAnimatedStyle(() => ({ opacity: o.value }));
const transformStyle = useAnimatedStyle(() => ({ transform: [...] }));
return <Animated.View style={[styles.base, opacityStyle, transformStyle]} />;
```

### Destructuring a shared value

```ts
// ❌ Wrong — captures current value, loses reactivity
const { value } = sv;
return <Text>{value}</Text>;

// ✅ Right — keep the reference
return <AnimatedDisplay sv={sv} />;
```

### `useAnimatedGestureHandler` usage

**Cause:** v2-era API. Removed/deprecated in v4 even though it may technically still work.

**Fix:** Rewrite with the modern Gesture Handler API:

```ts
// ❌ Old
const handler = useAnimatedGestureHandler({
  onActive: (event, ctx) => { x.value = ctx.startX + event.translationX; },
  onStart: (_, ctx) => { ctx.startX = x.value; },
});
return <PanGestureHandler onGestureEvent={handler}>...</PanGestureHandler>;

// ✅ New
const startX = useSharedValue(0);
const pan = Gesture.Pan()
  .onBegin(() => { startX.value = x.value; })
  .onUpdate((e) => { x.value = startX.value + e.translationX; });
return <GestureDetector gesture={pan}>...</GestureDetector>;
```

### Calling withTiming/withSpring outside a shared value assignment

```ts
// ❌ Wrong — return value is ignored
const animate = () => { withTiming(100); };

// ✅ Right
const animate = () => { x.value = withTiming(100); };
```

### Calling a worklet directly from JS

```ts
// ❌ Wrong
function myWorklet() { 'worklet'; /* ... */ }
myWorklet(); // throws or behaves unexpectedly

// ✅ Right
runOnUI(myWorklet)();
```

---

## Web target issues

### Animation works on iOS/Android but not web

**Cause:** Reanimated on web is a separate implementation. Some APIs have partial coverage.

**Fix:** Check the v4 web-support docs for the specific API. As a fallback, gate web-only code paths with `Platform.OS === 'web'` and use simpler animations there.

### Worklets warnings on web

**Cause:** On web there's no UI thread; worklets become plain JS functions. The `'worklet'` directive is still needed (the Babel plugin uses it to capture deps) but warnings about "running on JS thread" are expected.

---

## How to debug systematically

When an animation isn't behaving and the error isn't obvious:

1. **Confirm the animation is even running.** Add a quick `console.log` in a `useAnimatedReaction` or `runOnJS(log)` from a gesture callback. Worklets that look like they're firing might not be.
2. **Strip to the minimum.** Comment out everything except a single property animating. Once that works, add back layer by layer.
3. **Check the Animated.X wrapper.** A surprising number of "not animating" cases are caused by a plain `<View>` slipping in.
4. **Try the CSS-layer equivalent.** If a `useAnimatedStyle` is misbehaving for a state-driven case, swap in a CSS transition and see if it works. Often it does, and the original code was overcomplicated.
5. **Test on a real device, not just simulator.** Simulator timing can mask perf issues that show up on hardware.
6. **Reset Metro cache.** When in doubt, `--reset-cache` and restart. The Babel plugin's transforms are cache-sensitive.
