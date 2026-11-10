---
name: react-native-skia
description: Guide for building production-quality graphics, animations, charts, and visual effects in React Native using @shopify/react-native-skia. Use this skill whenever the user mentions React Native Skia, RNSkia, `@shopify/react-native-skia`, react-native-graph, or Victory Native XL, or asks in a React Native context for custom 2D graphics — line/area charts, stock or crypto price graphs, sparklines, a scrubbable chart cursor, animated range switching (1D/1W/1Y), gradients beyond `expo-linear-gradient`, animated paths, glassmorphism, frosted glass, neumorphism, shaders/SKSL, mesh gradients, image filters, Skottie, particles, ripples, progress rings, splash animations, generative art, or any visual a plain View cannot deliver. Also use when integrating Skia with Reanimated, gesture-handler, or Expo. Prefer this skill over guesswork — Skia has its own renderer, paint-inheritance model, and Reanimated integration that agents routinely get wrong.
---

# React Native Skia

A guide for building components with `@shopify/react-native-skia` — Shopify's React Native binding for Google's Skia graphics engine. Skia powers Chrome, Android, and Flutter; in React Native it gives you a declarative, GPU-accelerated 2D canvas that drives at 60–120 fps on the UI thread.

This skill is written for AI coding agents working on real codebases. It encodes patterns the official docs spread across a dozen pages, the gotchas that aren't obvious from reading those docs, and the decision points where agents tend to write working-but-wrong code.

## Mental model — read this first

Three ideas that, once internalized, make everything else click:

**1. Skia is its own React renderer.** `<Canvas>` is a portal into a parallel React tree. Inside it, components like `<Circle>`, `<Path>`, `<Image>`, `<Shader>` are *drawing instructions*, not views. They don't accept `style`, they don't accept `onPress`, they don't compose with `<View>`. Outside the Canvas, you compose normally. The boundary is sharp.

**2. Reanimated values are first-class props.** This is the single biggest departure from how animation works elsewhere in React Native. You do **not** need `createAnimatedComponent`, you do **not** need `useAnimatedProps`. You pass a `SharedValue<number>` directly as a prop:

```tsx
const r = useSharedValue(0);
return <Circle cx={100} cy={100} r={r} color="cyan" />;
```

Skia reads the shared value on the UI thread. No JS-thread round-trips per frame. This is why Skia animations are smooth.

**3. Paint is inherited through Groups.** Drawing components have paint attributes (color, style, strokeWidth, opacity, blendMode) and accept paint *children* (shaders, image filters, color filters, path effects). A `<Group>` applies its paint attributes to all descendants — like CSS cascade but for canvas drawing. A `<Group>` is also the unit of transforms, clipping, and layer effects.

**4. There are two API surfaces, not one.** Everything above is the *declarative* JSX tree.
Running underneath it is a parallel *imperative* `Skia.*` factory API — `Skia.Paint()`,
`Skia.RRectXY(...)`, `effect.makeShaderWithChildren(...)`, `createPicture(...)` — where you
draw onto an `SkCanvas` and build objects by hand. You reach for it when recording
`SkPicture` command lists, precomputing geometry, or rendering **offline / frame-driven**
(Remotion, server-side stills, the CanvasKit/WASM build), where Reanimated and backdrop
filters aren't available. If that's your context, read `references/offline-rendering.md`
first — the rest of this skill assumes the mobile UI-thread happy path.

Everything else in Skia is a variation on these ideas.

## When to reach for Skia (and when not to)

Reach for Skia when:
- You need custom drawing that a `<View>` with borderRadius/shadows/gradients can't produce — irregular shapes, animated paths, mesh gradients, blur over content, displacement, fragment shaders.
- You need 60+ fps animation of visual properties that would jank through the JS bridge — radii sweeping with a gesture, hundreds of particles, a path that morphs on every frame.
- You're building a chart (line, area, sparkline, scrubbable price graph — see `references/charts.md`), a progress meter, a generative pattern, a custom slider track, a video editor scrubber, a backdrop blur, a Lottie-like animation player (use Skottie), or a complex visual effect.
- You want a single graphics API that ships pixel-identical output on iOS, Android, and Web.

Don't reach for Skia for static layout, text-heavy UI, basic gradients that `expo-linear-gradient` handles, or anything where a `<View>` plus `react-native-svg` would suffice. Skia adds ~4–6 MB to bundle size and isn't worth it for trivial decoration.

## Workflow for building a Skia component

When the user asks for a Skia component, follow this sequence:

1. **Verify install.** Confirm `@shopify/react-native-skia` is in dependencies. Check version compatibility: requires `react-native >= 0.79` and `react >= 19`; for older RN/React, pin to `@shopify/react-native-skia@1.12.4` or below. iOS 14+ and Android API 21+ are required (API 26+ for video). Expo users can `npx create-expo-app my-app -e with-skia` for a template.
2. **Decide retained vs immediate mode.** Default to retained (declarative React tree). Switch to immediate mode (the `Picture` API with `Skia.PictureRecorder`) only when the number of drawing commands changes per frame — particle systems, generative art, games. See `references/animations.md` for the breakdown.
3. **Decide on canvas sizing.** For full-screen or flex-fill canvases, use `useCanvasSize()` (JS thread) or the `onSize` shared value prop (UI thread, preferred when sizing drives animations). For fixed dimensions, hard-code them and skip the hook.
4. **Compose: Canvas → Groups → Drawings.** Wrap shared paint or transforms in `<Group>`. Put effects (shaders, filters) as children of the group or drawing.
5. **Wire animation.** Use Reanimated `useSharedValue` + `useDerivedValue`. Pass shared values directly as props. For path animations, prefer `usePathValue` / `usePathInterpolation` over manual derived values.
6. **Wire gestures.** Use `react-native-gesture-handler` (`GestureDetector` + `Gesture.Pan()` etc.) wrapping the `<Canvas>`. For per-element gestures, overlay an `<Animated.View>` on top of the canvas element — see `references/animations.md` § Element Tracking.

## Critical gotchas — these are the bugs AI agents ship

These are the patterns that look correct, compile, and produce broken output. Memorize them.

**1. Use Skia's `interpolateColors`, not Reanimated's `interpolateColor`.** Reanimated's version returns its own encoding — a string on web, a packed ARGB number on native — so passing it straight to a Skia color prop gives wrong or platform-dependent colors (the official Wallet example has to unpack the integer by hand). `interpolateColors` (with an `s`) from `@shopify/react-native-skia` returns a Skia color on every platform:

```tsx
// ❌ Wrong — platform-dependent encoding, wrong colors
import { interpolateColor } from "react-native-reanimated";

// ✅ Right
import { interpolateColors } from "@shopify/react-native-skia";
```

**2. The default origin of transforms is top-left, not center.** In React Native `<View>`, `transform: [{ rotate }]` rotates around the center. In Skia, it rotates around `(0, 0)` of the group. To rotate around an element's center, set `origin={{ x, y }}` on the `<Group>` — and remember `origin` is *not* inherited by children. Also: **all rotations are in radians**, not degrees. Use `Math.PI` math, not `'45deg'` strings.

**3. `<Picture>`, `<SVG>`, and `<Paragraph>` ignore group paint properties.** A `<Group color="red">` does not tint these three. To apply effects (blur, color matrix, etc.) to them, you need a *layer effect*: pass a `<Paint>` element to the group's `layer` prop. See `references/core-api.md` § Layer Effects.

**4. `useImage` returns `null` while loading.** Always guard the render:

```tsx
const image = useImage(require("./logo.png"));
if (!image) return null; // or a placeholder
return <Image image={image} ... />;
```

This applies to network URLs and bundled assets equally.

**5. SKSL is not GLSL.** Skia's shading language looks like GLSL but has differences (no `gl_FragCoord`, different built-ins). Test shaders at https://shaders.skia.org/ before porting from Shadertoy. The conversion notes are at https://github.com/google/skia/tree/main/src/sksl#readme. See `references/shaders.md` for the patterns that translate cleanly.

**6. Paint children vs paint props are different APIs that overlap.** You can write `<Circle color="red" />` (prop) *or* `<Circle><Paint color="red" /></Circle>` (child). The child form lets you stack multiple paints — e.g., a fill plus two strokes on one circle. Don't mix them carelessly; if a `<Paint>` child is present, it takes precedence for that paint operation.

**7. Don't put `<Canvas>` inside a `ScrollView` without explicit dimensions.** A flex-1 Canvas inside a ScrollView with no height collapses to zero. Either give it a fixed `style={{ width, height }}`, or make sure its parent has bounded dimensions.

**8. Worklet directive is required in path-builder callbacks.** Hooks like `usePathValue`, `useRectBuffer`, `useRSXformBuffer` take callbacks that run on the UI thread. Forget `"worklet";` and the hook silently doesn't update.

**9. Web requires a separate setup step.** Skia on web loads a WASM bundle (CanvasKit). If targeting React Native Web, follow https://shopify.github.io/react-native-skia/docs/getting-started/web — don't assume `npm install` is sufficient.

**10. Imperatively-created CanvasKit objects are not garbage-collected.** `Skia.Paint()`, shaders, images, surfaces, `MaskFilter`, and pictures hold WASM heap that must be freed with `.ref.delete()`. In a short mobile session this rarely bites, but a long/offline render that allocates per frame climbs in memory until it crashes (observed ~frame 500). Dispose per-frame objects — chiefly the per-frame **pictures** (and any `Surface`/`Image`), which is what actually prevents the crash. Don't try to `del()` individual paints/shaders *inside* a `createPicture` callback (easy to mis-order against the draw; the picture is the right unit of cleanup). Also note the module-scope "dispose previous frame" cursor is single-instance only — for Studio/multi-mount use a `useRef` + `useEffect` cleanup. See `references/offline-rendering.md`.

**11. On CanvasKit/web, a runtime shader can't be a backdrop filter, and per-frame rasterization leaks.** The `<BackdropBlur>`/`<BackdropFilter filter={<Shader/>}>` glassmorphism recipe won't carry a runtime effect on CanvasKit, and the workaround of snapshotting a layer (`readPixels` / `makeImageSnapshot` / offscreen `Surface`) per frame leaks the heap. Record the content as an `SkPicture` and sample it with `picture.makeShader()` fed into the effect instead — no pixels materialized. See `references/offline-rendering.md` § 4–6.

**12. `SkPath` is immutable in Skia ≥ 2.14 — build paths with `Skia.PathBuilder`.** 2.14.0 (Oct 2026) removed `moveTo`/`lineTo`/`cubicTo`/`close` and the other mutators from `SkPath`. Earlier 2.x releases (at least 2.6–2.13) only printed a one-time `console.warn` ("SkPath.moveTo() is deprecated…", migration guide: https://shopify.github.io/react-native-skia/docs/shapes/path-migration) — easy to miss, and the types never carried `@deprecated`. If you see that warning, fix it before upgrading. Code that does `const p = Skia.Path.Make(); p.moveTo(…)` or `path.copy().lineTo(…)` throws "moveTo is not a function" at runtime. Use `Skia.PathBuilder.Make().moveTo(…).cubicTo(…).build()`, and `Skia.PathBuilder.MakeFromPath(path)` to extend an existing path. Much code online — including the stable **react-native-graph 1.4.0** release, whose peer deps don't constrain Skia — still mutates paths; pin Skia `~2.13`, patch it, try its `1.4.0-alpha.1` prerelease (rebuilt on `Skia.Path.MakeFromCmds`), or hand-roll (see `references/charts.md` §1).

**13. Charts: don't let the curve lie, and don't rebuild per frame.** Smoothing with a B-spline (react-native-graph, the Wallet's `"bezier"` mode) renders peaks lower than the data — use a monotone curve where users read values, and show the scrub label from the nearest *datum*, not the curve's y. Build paths and `toCmds()` once per data change on the JS thread; on the UI thread only `interpolate`, `getYForX`, and move the cursor. Morphing between ranges needs identical command structure — resample every range to the same point count. All of this is packaged in `assets/chartMath.ts`.

**14. Offline / frame-driven hosts have no Reanimated clock.** In Remotion, server-side stills, or snapshot pipelines there is no UI-thread loop — `useSharedValue`/`useClock`/`withTiming` don't run. Drive every value from a frame number (`frame / fps` → `interpolate`/trig). The Reanimated patterns in `animations.md` are mobile-only; `references/offline-rendering.md` is the frame-driven counterpart.

## Component decision table

| You want… | Use | Notes |
| --- | --- | --- |
| Circle, rect, rounded rect, line, oval | `<Circle>`, `<Rect>`, `<RoundedRect>`, `<Line>`, `<Oval>` | Top-level drawing components |
| Star, polygon, arbitrary 2D outline | `<Path path="M..." />` or `Skia.PathBuilder` | SVG path notation supported; use `start`/`end` props to animate trim |
| Static SVG file | `<ImageSVG svg={useSVG(...)} />` | Subject to layer-effect rule — see gotcha #3 |
| Bitmap image (PNG/JPG/GIF) | `<Image image={useImage(...)} fit="contain" .../>` | `fit` values: contain, cover, fill, fitHeight, fitWidth, scaleDown, none |
| Animated GIF / WebP | `<Image>` + `useAnimatedImageValue` | See animated-images docs |
| Video frame painting | `<Image image={frame}>` + `useVideo` | Android API 26+ required |
| Lottie playback | `<Skottie>` | Native Lottie via Skia |
| Text with full typography | `<Paragraph>` | Subject to layer-effect rule |
| Gradient fill | `<LinearGradient>`, `<RadialGradient>`, `<SweepGradient>`, `<TwoPointConicalGradient>` | Pass as child of drawing or group |
| Drop shadow | `<Shadow>` as child of drawing | More flexible than View's `shadowColor` |
| Blur the content behind something | `<BackdropBlur blur={N} clip={...}>` | Glassmorphism; clip required |
| Blur the drawing itself | `<Blur blur={N} />` as child | Image filter; applies to that drawing |
| Fragment shader | `Skia.RuntimeEffect.Make(src)` + `<Shader source={...} uniforms={...} />` | See `references/shaders.md` |
| Hundreds of similar sprites | `<Atlas>` | Single draw call; pairs with `useRectBuffer` / `useRSXformBuffer` |
| Particle system / generative art | `<Picture>` with `Skia.PictureRecorder` / `createPicture` | Immediate mode |
| Triangle mesh / per-vertex color gradient | `<Vertices>` | `vertices` + `colors` + `indices`; modes `triangles`/`triangleStrip`/`triangleFan` |
| Smooth bicubic ("Coons") mesh gradient | `canvas.drawPatch(cubics, colors, …)` | Imperative; use `BlendMode.DstOver` on CanvasKit (see offline-rendering.md) |
| Frame / ring / donut hole | `<DiffRect inner={…} outer={…} />` | Even-odd of two (rounded) rects |
| Scatter dots / polyline | `<Points points={…} mode="polygon" />` | modes `points`/`lines`/`polygon` |
| Snapshot a React Native `<View>` to an image | `makeImageFromView(ref)` | Root view needs `collapsable={false}` |
| Record a reusable command list | `createPicture(cb, {width,height})` → `<Picture>` | Cheap (no pixels); sample via `picture.makeShader()` |
| Line / area / price chart with scrub + range morph | `assets/chartMath.ts` + `assets/PriceChart.tsx` | Or react-native-graph (check Skia version, gotcha #12). See `references/charts.md` |
| Bars, axes, multiple series, pies | Victory Native XL (`victory-native`) | Skia-based; hand-roll only for a custom look |
| Sparklines in a list | Static `<Path>` built in `useMemo` | No shared values or gestures per row |
| Cursor y on a curve at finger x | `getYForX(path.toCmds(), x)` | Cache `toCmds()`; label from nearest datum |

## Pattern catalog

These are the most common Skia setups. For each, the canonical structure is below; deep dives and variations are in the reference files.

### Static drawing

```tsx
import { Canvas, Circle, Group } from "@shopify/react-native-skia";

const Logo = () => (
  <Canvas style={{ width: 256, height: 256 }}>
    <Group blendMode="multiply">
      <Circle cx={85} cy={85} r={85} color="cyan" />
      <Circle cx={171} cy={85} r={85} color="magenta" />
      <Circle cx={128} cy={171} r={85} color="yellow" />
    </Group>
  </Canvas>
);
```

### Animated property (Reanimated)

```tsx
import { Canvas, Circle } from "@shopify/react-native-skia";
import { useSharedValue, withRepeat, withTiming } from "react-native-reanimated";
import { useEffect } from "react";

const Pulse = () => {
  const r = useSharedValue(40);
  useEffect(() => {
    r.value = withRepeat(withTiming(80, { duration: 800 }), -1, true);
  }, []);
  return (
    <Canvas style={{ flex: 1 }}>
      <Circle cx={128} cy={128} r={r} color="#3E7CB1" />
    </Canvas>
  );
};
```

### Gesture-driven (gesture-handler + Reanimated)

```tsx
import { Canvas, Circle } from "@shopify/react-native-skia";
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import { useSharedValue } from "react-native-reanimated";

const Draggable = () => {
  const x = useSharedValue(100);
  const y = useSharedValue(100);
  const gesture = Gesture.Pan().onChange((e) => {
    x.value += e.changeX;
    y.value += e.changeY;
  });
  return (
    <GestureDetector gesture={gesture}>
      <Canvas style={{ flex: 1 }}>
        <Circle cx={x} cy={y} r={30} color="#3E7CB1" />
      </Canvas>
    </GestureDetector>
  );
};
```

### Glassmorphism / frosted glass

```tsx
import { Canvas, Image, useImage, BackdropBlur, Fill, rrect, rect } from "@shopify/react-native-skia";

const Frosted = () => {
  const image = useImage(require("./bg.jpg"));
  if (!image) return null;
  const card = rrect(rect(40, 120, 280, 200), 24, 24);
  return (
    <Canvas style={{ flex: 1 }}>
      <Image image={image} x={0} y={0} width={360} height={640} fit="cover" />
      <BackdropBlur blur={12} clip={card}>
        <Fill color="rgba(255,255,255,0.18)" />
      </BackdropBlur>
    </Canvas>
  );
};
```

### Gradient fill

```tsx
import { Canvas, Rect, LinearGradient, vec } from "@shopify/react-native-skia";

const Gradient = () => (
  <Canvas style={{ width: 256, height: 256 }}>
    <Rect x={0} y={0} width={256} height={256}>
      <LinearGradient
        start={vec(0, 0)}
        end={vec(256, 256)}
        colors={["#3E7CB1", "#DFB6B2"]}
      />
    </Rect>
  </Canvas>
);
```

### Animated path morph

```tsx
import { Canvas, Path, Skia, usePathInterpolation } from "@shopify/react-native-skia";
import { useSharedValue, withTiming } from "react-native-reanimated";
import { useEffect } from "react";

const happy = Skia.Path.MakeFromSVGString("M 21 45 C 21 37 ... Z")!;
const sad   = Skia.Path.MakeFromSVGString("M 16 25 C 32 27 ... Z")!;

const Morph = () => {
  const progress = useSharedValue(0);
  useEffect(() => {
    progress.value = withTiming(1, { duration: 600 });
  }, []);
  const path = usePathInterpolation(progress, [0, 1], [sad, happy]);
  return (
    <Canvas style={{ flex: 1 }}>
      <Path path={path} style="stroke" strokeWidth={4} strokeCap="round" />
    </Canvas>
  );
};
```

Paths must be *interpolatable* — same number and types of commands. For arbitrary morphs, use the [flubber](https://github.com/veltman/flubber) library to pre-process. For imperative morphs, `to.interpolate(from, t)` returns `to` at `t = 1` and `from` at `t = 0`, and returns `null` when the structures differ — keep a `?? to` fallback.

### Interactive line chart (scrub + range switch)

```tsx
import { PriceChart } from "./charts/PriceChart"; // copy assets/PriceChart.tsx + assets/chartMath.ts

<PriceChart
  ranges={[day, week, year]}          // Datum[] per range: { x: ms, y: value }, oldest → newest
  rangeIndex={selected}               // changing it morphs the line + area
  width={width}
  color="#31CBD1"                      // six-digit hex
  onSelect={(d) => setHeaderPrice(d?.y ?? null)} // JS thread, only when the datum changes (haptics go here)
/>
```

The pieces, each of which you can lift separately: resample every range to one point budget (so they interpolate) → monotone cubic path built once on the JS thread → area path via `PathBuilder.MakeFromPath` → morph with `to.interpolate(from, progress)` where `from` is whatever is on screen → `Gesture.Pan().activateAfterLongPress()` with reset in `onFinalize` → cursor y from `getYForX(cachedCmds, x)` → label from `nearestIndex(data, xToValue(x))`. Read `references/charts.md` before customizing.

### Custom shader (SKSL)

```tsx
import { Canvas, Fill, Shader, Skia, vec } from "@shopify/react-native-skia";

const src = Skia.RuntimeEffect.Make(`
uniform vec2  resolution;
uniform float t;
vec4 main(vec2 pos) {
  vec2 uv = pos / resolution;
  return vec4(uv.x, uv.y, abs(sin(t)), 1.0);
}`)!;

const ShaderCanvas = () => (
  <Canvas style={{ width: 256, height: 256 }}>
    <Fill>
      <Shader source={src} uniforms={{ resolution: vec(256, 256), t: 1.0 }} />
    </Fill>
  </Canvas>
);
```

For animated uniforms, wrap `uniforms` in `useDerivedValue` so the shader re-evaluates on the UI thread without re-rendering React.

## When you need more depth

The references below are loaded on demand. Read the one that matches the task — don't preemptively read all of them.

- **`references/core-api.md`** — Canvas props, Group (paint inheritance, transforms, clipping, layer effects, zIndex, FitBox), every shape component, Paint as ref, all paint properties, manual paint assignment.
- **`references/animations.md`** — Reanimated integration depth, Skia-specific hooks (`usePathValue`, `usePathInterpolation`, `useClock`, `useRectBuffer`, `useRSXformBuffer`), textures (`useTexture`, `useImageAsTexture`, `usePictureAsTexture`, `runOnUI` patterns), gestures (`GestureDetector`, element tracking), retained vs immediate mode trade-offs.
- **`references/shaders.md`** — `RuntimeEffect.Make`, SKSL vs GLSL differences, uniform types (float, vec2/3/4, matrices, arrays), nested shaders (`ImageShader`), gradients (all four kinds), Perlin noise, blending modes.
- **`references/effects.md`** — Image filters (Blur, Shadow, DisplacementMap, Offset, Morphology, RuntimeShader), backdrop filters (BackdropFilter, BackdropBlur), mask filters (BlurMask), color filters and matrices, path effects (Dash, Discrete, Corner, Sum, Line2D, Path1D, Path2D), the Mask component.
- **`references/recipes.md`** — Production-ready snippets: circular progress, animated gradient background, ripple effect, neon glow text, animated splash, audio-reactive bars, blur card stack.
- **`references/charts.md`** — Read this for **any chart**: library vs hand-rolled (react-native-graph, Victory Native XL, Skia-version compatibility), the data → path pipeline, Y inversion and point budgets, which smoothing curve and what it costs, area fills and gradient tricks, scrubbing (`getYForX`, gesture activation inside scroll views, label-from-data), interruptible range morphs, UI-thread labels, list performance, bars/candles/pies, and the known bugs to fix when copying from the Wallet example or react-native-graph. Pairs with `assets/chartMath.ts` (tested helpers) and `assets/PriceChart.tsx` (typechecked reference component).
- **`references/offline-rendering.md`** — Read this for **Remotion / server-side / CanvasKit-web** work: the imperative `Skia.*` factory API, `createPicture` command lists, sampling pictures as shaders (`picture.makeShader` + `makeShaderWithChildren`), WASM-heap disposal, the liquid-glass refraction recipe, `drawPatch` mesh gradients, and frame-driven (no-Reanimated) animation.

## Learn from the source

When a request resembles a known effect, the official material is faster and more reliable
than improvising — read it before writing a shader or a complex composition from scratch.

- **Tutorial index** — https://shopify.github.io/react-native-skia/docs/tutorials/ groups
  ~25 deep-dive videos by topic (SDFs, animations, backdrop filters, shaders, paths, games).
  Notably: **"Liquid Glass with React Native Skia"** (`youtube.com/watch?v=qYFMOMVZoPY`) is the
  canonical refraction technique this skill's offline glass recipe is built on;
  **"Glassmorphism in React Native"** (`ao2i_sOD-z0`) covers the mobile backdrop-filter version.
- **Example app** — https://github.com/Shopify/react-native-skia/tree/main/apps/example/src/Examples
  is the best source of idiomatic, working code. High-value folders to crib from:
  `Glassmorphism` / `FrostedCard` (backdrop + clip), `Filters` / `Transitions` (runtime-shader
  displacement, nested `ImageShader`s), `Vertices` (mesh deformation with edge preservation),
  `Pictures` (record/replay), `Hue` / `Breathe` (polar `canvas2Polar`/`polar2Canvas` helpers),
  `Neumorphism` (stacked inner/outer `<Shadow>`), `Matrix` (grid + `BlurMask` glow),
  `Wallet` (scrubbable price chart: smoothing, `getYForX`, range morph — pair it with the
  **"Charts with React Native Skia"** video, `youtu.be/xeLdmn3se1I`, and read the fix list in
  `references/charts.md` §10 before copying).
- **react-native-graph** — https://github.com/margelo/react-native-graph (source in
  `package/src`) is the production-hardened version of the Wallet chart: pixel-sampled
  point budgets, interruptible morphs, scrub-dimmed stroke, `onFinalize` gesture reset.
- **Shader playground** — https://shaders.skia.org/ compiles SKSL live; validate there before
  porting from Shadertoy (SKSL ≠ GLSL — see gotcha #5 and `references/shaders.md`).

## Sanity checks before delivering code

Run through this mental checklist for every Skia component you write:

- Canvas has bounded dimensions (`flex: 1` inside a bounded parent, or explicit `width`/`height`).
- `useImage` / `useSVG` results are guarded against `null`.
- Animations use `useSharedValue` + Reanimated, passed directly as props (no `createAnimatedComponent`).
- Color interpolation uses `interpolateColors` from `@shopify/react-native-skia`, not Reanimated's `interpolateColor`.
- Rotations are in radians.
- `origin` is set on the `<Group>` when transforms should pivot around a non-(0,0) point.
- `<Picture>` / `<SVG>` / `<Paragraph>` use a `layer` paint, not group properties, when effects are required.
- Path interpolation targets have identical command structures.
- Worklet callbacks include `"worklet";` directive.
- The component compiles for both iOS and Android (no platform-specific APIs unless guarded).
- Paths are built with `Skia.PathBuilder` (…`.build()`), never by mutating an `SkPath` (gotcha #12).
- **Charts:** Y is inverted, paths are built once per data change (not per frame), morphing ranges share one point budget, the scrub label reads the nearest datum, and the pan gesture resets in `onFinalize`. See `references/charts.md`.
- **If rendering offline / frame-driven** (Remotion, CanvasKit-web, snapshots): values derive from a frame number (not Reanimated), per-frame imperative objects are disposed, no per-frame `readPixels`/offscreen surface, and `RuntimeEffect.Make` is null-checked. See `references/offline-rendering.md`.
