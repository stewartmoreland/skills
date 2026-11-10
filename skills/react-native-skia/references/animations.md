# Animations, gestures, and rendering modes

Detailed reference for everything that moves. Read this when wiring Reanimated, building per-frame logic, dealing with gestures, or deciding whether to use retained or immediate mode.

> **Mobile / UI-thread only.** Everything in this file assumes Reanimated on a live UI thread —
> `useSharedValue`, `useClock`, `withTiming`, gesture handlers. None of that runs in an
> **offline / frame-driven** host (Remotion, server-side stills, the CanvasKit/WASM render
> path), where you're handed a frame number instead of a clock. There, drive every value from
> `frame / fps` + `interpolate`/trig, and manage object lifetime by hand. See
> `references/offline-rendering.md` — it's the frame-driven counterpart to this file.

## Reanimated integration — the core idea

Skia's React renderer reads `SharedValue` props on the UI thread directly. No `createAnimatedComponent`, no `useAnimatedProps` — you just pass the shared value as the prop.

```tsx
import { Canvas, Circle, Group } from "@shopify/react-native-skia";
import {
  useDerivedValue,
  useSharedValue,
  withRepeat,
  withTiming,
} from "react-native-reanimated";
import { useEffect } from "react";

export const Pulse = () => {
  const size = 256;
  const r = useSharedValue(0);
  const c = useDerivedValue(() => size - r.value);
  useEffect(() => {
    r.value = withRepeat(withTiming(size * 0.33, { duration: 1000 }), -1);
  }, [r, size]);
  return (
    <Canvas style={{ flex: 1 }}>
      <Group blendMode="multiply">
        <Circle cx={r} cy={r} r={r} color="cyan" />
        <Circle cx={c} cy={r} r={r} color="magenta" />
        <Circle cx={size / 2} cy={c} r={r} color="yellow" />
      </Group>
    </Canvas>
  );
};
```

`r` and `c` are shared values; passing them directly is the entire integration. The animation runs entirely on the UI thread; the React tree never re-renders.

## Requires Reanimated v3+

Older Reanimated versions (1.x, 2.x) won't work cleanly. Make sure the project has `react-native-reanimated@^3` installed and configured (Babel plugin in `babel.config.js`).

## Color interpolation

**Reanimated's `interpolateColor` does not work with Skia colors.** Skia stores colors in a different format. Use `interpolateColors` (note the plural) imported from `@shopify/react-native-skia`:

```tsx
import { interpolateColors, Canvas, Fill, LinearGradient, vec } from "@shopify/react-native-skia";
import { useDerivedValue, useSharedValue, withRepeat, withTiming } from "react-native-reanimated";
import { useEffect } from "react";

const startPalette = ["rgba(34,193,195,0.4)", "rgba(63,94,251,1)", "rgba(253,29,29,0.4)"];
const endPalette   = ["rgba(0,212,255,0.4)",  "rgba(252,70,107,1)", "rgba(252,176,69,0.4)"];

export const AnimatedGradient = () => {
  const i = useSharedValue(0);
  useEffect(() => {
    i.value = withRepeat(withTiming(startPalette.length - 1, { duration: 4000 }), -1, true);
  }, []);
  const colors = useDerivedValue(() => [
    interpolateColors(i.value, [0, 1, 2], startPalette),
    interpolateColors(i.value, [0, 1, 2], endPalette),
  ]);
  return (
    <Canvas style={{ flex: 1 }}>
      <Fill>
        <LinearGradient start={vec(0, 0)} end={vec(360, 640)} colors={colors} />
      </Fill>
    </Canvas>
  );
};
```

Note that `colors` is passed as a derived value containing an array — the gradient component accepts that form natively.

## Skia-specific animation hooks

These hooks live alongside Reanimated and exist because some animation patterns are awkward to express purely in derived values.

### `usePathValue`

The standard way to mutate a path on every frame. Takes a base path and a worklet that mutates it; returns a Reanimated `SharedValue<SkPath>` you pass to `<Path>`.

```tsx
import { Canvas, Path, Skia, usePathValue, processTransform3d } from "@shopify/react-native-skia";
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import { useSharedValue } from "react-native-reanimated";

const rrct = Skia.PathBuilder.Make()
  .addRRect(Skia.RRectXY(Skia.XYWHRect(0, 0, 100, 100), 10, 10))
  .build();

export const FrostedCard = () => {
  const rotateY = useSharedValue(0);
  const gesture = Gesture.Pan().onChange((e) => { rotateY.value -= e.changeX / 300; });

  const path = usePathValue(
    () => { "worklet"; },                        // optional pre-step
    rrct,                                        // base path
    (p) => {                                     // mutator
      "worklet";
      return p.transform(
        processTransform3d([
          { translate: [50, 50] },
          { perspective: 300 },
          { rotateY: rotateY.value },
          { translate: [-50, -50] },
        ])
      );
    }
  );

  return (
    <GestureDetector gesture={gesture}>
      <Canvas style={{ flex: 1 }}>
        <Path path={path} />
      </Canvas>
    </GestureDetector>
  );
};
```

Both callbacks need the `"worklet";` directive or the hook silently won't update.

### `usePathInterpolation`

Smoothly interpolates between paths based on a progress shared value.

```tsx
const path = usePathInterpolation(
  progress,             // SharedValue<number>
  [0, 0.5, 1],          // input range
  [pathA, pathB, pathC] // SkPaths — same command structure
);
```

The paths **must be interpolatable**: same number and types of commands. For arbitrary morphs, pre-process with [flubber](https://github.com/veltman/flubber) to generate interpolatable command structures.

### `useClock`

Returns a shared value containing milliseconds since the hook activated. Useful for ambient animations that don't need explicit timing functions.

```tsx
const t = useClock();
const tx = useDerivedValue(() => Math.sin(t.value / 1000) * 100);
return <Circle cx={tx} cy={100} r={40} color="cyan" />;
```

### `useRectBuffer` and `useRSXformBuffer`

For animating large arrays of rectangles or rotate-scale transforms — used with the `<Atlas>` API for hundreds-of-sprites scenes with a single draw call.

```tsx
const rects = useRectBuffer(100, (rect, i) => {
  "worklet";
  rect.setXYWH((i * 10) % width, Math.floor(i / (width / 10)) * 10, 10, 10);
});

const xforms = useRSXformBuffer(100, (val, i) => {
  "worklet";
  const r = Math.atan2(pos.value.y, pos.value.x);
  val.set(Math.cos(r), Math.sin(r), 0, 0);
});
```

The buffer mutators run on the UI thread per frame — `"worklet"` is required.

## Gestures

Use `react-native-gesture-handler` for everything. Wrap the `<Canvas>` in a `<GestureDetector>` and drive shared values from the gesture callbacks.

```tsx
import { Canvas, Circle, Fill } from "@shopify/react-native-skia";
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import { useSharedValue, withDecay } from "react-native-reanimated";

const Slider = () => {
  const x = useSharedValue(100);
  const gesture = Gesture.Pan()
    .onChange((e) => { x.value += e.changeX; })
    .onEnd((e) => {
      x.value = withDecay({
        velocity: e.velocityX,
        clamp: [0, 300],
      });
    });
  return (
    <GestureDetector gesture={gesture}>
      <Canvas style={{ flex: 1 }}>
        <Fill color="white" />
        <Circle cx={x} cy={40} r={20} color="#3E7CB1" />
      </Canvas>
    </GestureDetector>
  );
};
```

All gesture types work: `Pan`, `Tap`, `LongPress`, `Pinch`, `Rotation`, `Fling`, plus composed gestures via `Gesture.Race(...)` / `Gesture.Simultaneous(...)` / `Gesture.Exclusive(...)`.

### Element tracking (per-element gestures)

The `<Canvas>` itself is the only thing gesture-handler sees. To attach gestures to a specific drawing inside, overlay an invisible `<Animated.View>` on top of it with matching transforms:

```tsx
import { View } from "react-native";
import { Canvas, Circle, Fill } from "@shopify/react-native-skia";
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import Animated, { useSharedValue, useAnimatedStyle } from "react-native-reanimated";

const radius = 30;

const Draggable = () => {
  const x = useSharedValue(100);
  const y = useSharedValue(100);

  const style = useAnimatedStyle(() => ({
    position: "absolute",
    top: -radius,
    left: -radius,
    width: radius * 2,
    height: radius * 2,
    transform: [{ translateX: x.value }, { translateY: y.value }],
  }));

  const gesture = Gesture.Pan().onChange((e) => {
    x.value += e.changeX;
    y.value += e.changeY;
  });

  return (
    <View style={{ flex: 1 }}>
      <Canvas style={{ flex: 1 }}>
        <Fill color="white" />
        <Circle cx={x} cy={y} r={radius} color="cyan" />
      </Canvas>
      <GestureDetector gesture={gesture}>
        <Animated.View style={style} />
      </GestureDetector>
    </View>
  );
};
```

The animated view is invisible but receives gestures. Any transforms applied to the canvas element must also be applied to the animated view to keep hit-testing accurate.

This same overlay technique gives you accessibility for canvas elements — put real `<View>` with `accessibilityLabel` on top.

## Retained mode vs immediate mode

Two ways to express a Skia scene. They compose freely inside one Canvas.

### Retained mode (default)

You declare the scene as a tree of React components. Skia compiles it to a display list once; per-frame updates only change the display list slots tied to shared values. Near-zero FFI cost.

```tsx
const Pulse = () => {
  const r = useSharedValue(50);
  useEffect(() => { r.value = withSpring(100); }, []);
  return (
    <Canvas style={{ flex: 1 }}>
      <Circle cx={128} cy={128} r={r} color="cyan" />
    </Canvas>
  );
};
```

Use retained mode for:
- UI with animated properties
- Charts and data visualization
- Fixed-count sprites (combine with `<Atlas>`)
- Anything where the *structure* is stable and only *properties* animate

### Immediate mode

You issue drawing commands directly to a canvas inside a worklet, every frame. The output is wrapped in `<Picture>`.

```tsx
import { Canvas, Picture, Skia } from "@shopify/react-native-skia";
import { useDerivedValue, useSharedValue, withRepeat, withTiming } from "react-native-reanimated";
import { useEffect } from "react";

const size = 256;
const recorder = Skia.PictureRecorder();
const paint = Skia.Paint();

const Particles = () => {
  const progress = useSharedValue(0);
  useEffect(() => {
    progress.value = withRepeat(withTiming(1, { duration: 2000 }), -1, true);
  }, []);

  const picture = useDerivedValue(() => {
    "worklet";
    const canvas = recorder.beginRecording(Skia.XYWHRect(0, 0, size, size));
    const count = Math.floor(progress.value * 20);
    for (let i = 0; i < count; i++) {
      paint.setColor(Skia.Color(`rgba(0,122,255,${(i + 1) / 20})`));
      canvas.drawCircle(size / 2, size / 2, (i + 1) * 6, paint);
    }
    return recorder.finishRecordingAsPicture();
  });

  return (
    <Canvas style={{ flex: 1 }}>
      <Picture picture={picture} />
    </Canvas>
  );
};
```

Use immediate mode for:
- Particle systems
- Games with dynamic entity counts
- Procedural/generative art where the draw-call count varies per frame
- Anything where the *structure* changes from frame to frame

### Mixing them

Both modes share the same `<Canvas>`. Common pattern: game world in immediate mode, HUD/UI in retained mode.

```tsx
<Canvas style={{ flex: 1 }}>
  <Picture picture={gameWorldPicture} />     {/* immediate */}
  <Group transform={[{ translateY: 20 }]}>    {/* retained */}
    <Rect x={0} y={0} width={300} height={60} color="rgba(0,0,0,0.4)" />
    <Paragraph paragraph={scoreParagraph} x={20} y={30} width={260} />
  </Group>
</Canvas>
```

## Textures — running React rendering on the UI thread

A "texture" in this context is an `SkImage` (or `SharedValue<SkImage | null>`) you generate ahead of drawing it. Useful when:
- A subtree is expensive to draw and rarely changes — pre-rasterize once, then draw the bitmap.
- You want to keep complex draw logic out of the React lifecycle.
- You're working in immediate mode and want to bake a sub-scene into a texture.

### `useTexture`

Renders a React element to an off-screen surface, returns the resulting `SkImage` shared value.

```tsx
const texture = useTexture(
  <Group>
    <Fill color="cyan" />
    <Circle cx={50} cy={50} r={40} color="white" />
  </Group>,
  { width: 100, height: 100 }
);
return (
  <Canvas style={{ flex: 1 }}>
    <Image image={texture} rect={{ x: 0, y: 0, width: 100, height: 100 }} />
  </Canvas>
);
```

### `useImageAsTexture`

Loads an image and uploads it to the GPU. Useful for very large images you'll use as shader inputs.

```tsx
const tex = useImageAsTexture(require("./bg.png"));
```

### `usePictureAsTexture`

Bakes an `SkPicture` into a texture.

```tsx
const rec = Skia.PictureRecorder();
const canvas = rec.beginRecording();
canvas.drawColor(Skia.Color("cyan"));
const picture = rec.finishRecordingAsPicture();

const tex = usePictureAsTexture(picture, { width, height });
```

### Manual UI-thread rendering with `runOnUI`

For full control, use Reanimated's `runOnUI` to render to an offscreen surface and stash the result in a shared value:

```tsx
import { runOnUI, useSharedValue } from "react-native-reanimated";
import { Skia } from "@shopify/react-native-skia";
import type { SharedValue } from "react-native-reanimated";
import type { SkImage } from "@shopify/react-native-skia";

const createTexture = (image: SharedValue<SkImage | null>) => {
  "worklet";
  const surface = Skia.Surface.MakeOffscreen(200, 200)!;
  const canvas = surface.getCanvas();
  canvas.drawColor(Skia.Color("cyan"));
  surface.flush();
  image.value = surface.makeImageSnapshot();
};

const Demo = () => {
  const image = useSharedValue<SkImage | null>(null);
  useEffect(() => { runOnUI(createTexture)(image); }, []);
  return (
    <Canvas style={{ flex: 1 }}>
      <Image image={image} x={0} y={0} width={200} height={200} />
    </Canvas>
  );
};
```

The surface and canvas live on the UI thread. The image shared value is `null` until the worklet completes, so guard the `<Image>` if it matters.

## Performance heuristics

When the user reports jank or you suspect performance issues:

- **Move logic out of React renders.** If a `useDerivedValue` is triggering re-renders, refactor so the value is consumed only by Skia props (which don't trigger renders).
- **Pre-build expensive paths.** `Skia.PathBuilder.Make()...build()` once at module scope or in `useMemo`, not on every render.
- **Cache rasterized subtrees with `useTexture`.** Static or rarely-changing layers shouldn't redraw on every frame.
- **Use `<Atlas>` for hundreds of similar elements.** It's one draw call regardless of count.
- **Move loops into immediate mode.** A for-loop that creates 200 `<Circle>` elements is 200 retained-mode entries. The same loop inside `usePictureAsTexture` is one draw command list.
- **Avoid `androidWarmup` on animated canvases.** It can cause first-frame artifacts.
- **Watch shader uniform churn.** Re-creating a `uniforms` object on every JS render forces a UI-thread re-eval. Wrap in `useDerivedValue` so the object is only built once and updated by shared values.
- **Drop to `<Picture>` for variable-count scenes.** A retained tree where `.map()` length changes per frame is the wrong tool.

## Quick reference

| Need | Tool |
| --- | --- |
| Animate a numeric prop | `useSharedValue` + `withTiming`/`withSpring`/`withDecay` |
| Combine shared values | `useDerivedValue(() => ...)` |
| Animate colors | `interpolateColors` from RN Skia (not Reanimated) |
| Animate paths | `usePathValue` / `usePathInterpolation` |
| Ambient time-driven animation | `useClock` |
| Pan / pinch / rotate | `Gesture.Pan/Pinch/Rotation` + `GestureDetector` |
| Per-element gestures | Overlay `Animated.View` matching transforms |
| Many similar sprites | `<Atlas>` + `useRectBuffer` / `useRSXformBuffer` |
| Variable-count draws per frame | `<Picture>` + `Skia.PictureRecorder` (immediate mode) |
| Cache an expensive subtree | `useTexture` |
| Render to bitmap outside React | `runOnUI(...)` + `Skia.Surface.MakeOffscreen` |
