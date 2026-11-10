# Offline & frame-driven rendering (imperative Skia, pictures, disposal)

Read this when Skia is **not** running on the mobile UI thread with Reanimated — i.e.
offline/deferred renderers (Remotion, server-side stills, batch export pipelines), the
CanvasKit/WASM web build, or any host where you own a frame number instead of a clock. The
mobile happy path the rest of this skill describes (`useSharedValue`, `<BackdropBlur>`,
`useClock`) quietly breaks here. This file is the parallel toolkit: the **imperative `Skia.*`
factory API**, **`SkPicture` command lists sampled as shaders**, and **explicit object
disposal**.

## Are you in this mode?

Symptoms, any one of which puts you here:

- There is no UI-thread animation loop. You can't `useSharedValue`; instead you're handed a
  frame index each render (Remotion's `useCurrentFrame()`, a server render loop, a test).
- You're on the **CanvasKit/WASM** build (web, or any Node/offline render). CanvasKit is a
  subset of native Skia — some native conveniences (runtime-shader backdrop filters) aren't
  available, and its objects aren't garbage-collected.
- The render is **long-lived**: hundreds or thousands of frames in one process. Anything you
  allocate per frame and don't free accumulates.

If all three are false (a normal Expo/RN app), prefer the declarative + Reanimated patterns
in `animations.md` — they're simpler and this file's manual disposal is unnecessary there.

## 1. Frame-driven, not Reanimated

Every animated value is a pure function of the frame. No shared values, no `useClock`, no
`withTiming`/`withSpring`. Convert frame → seconds and feed plain math / `interpolate`:

```tsx
const frame = useCurrentFrame();      // host-provided frame index (Remotion shown)
const { fps, width, height } = useVideoConfig();
const t = frame / fps;                // seconds — drives every sin/cos/interpolate
const wobble = Math.sin(t * 0.8 + phase) * 14;
```

Because the output must be deterministic for a given frame, this is actually *easier* to
reason about than the UI-thread model — the same frame always produces the same pixels. The
cost is that you recompute the scene every frame, which is why disposal (§5) matters.

## 2. The imperative `Skia.*` factory API

The JSX components (`<Circle>`, `<Paint>`, `<Shader>`) are sugar over a factory API you call
directly when recording into a picture or precomputing geometry. The ones you'll actually use:

```tsx
import {
  Skia, createPicture, PaintStyle, BlendMode, TileMode, FilterMode, BlurStyle,
  type SkCanvas, type SkPaint, type SkPicture, type SkShader, type SkRuntimeEffect,
} from "@shopify/react-native-skia";

// Geometry
const rect = Skia.XYWHRect(x, y, w, h);            // SkRect
const rr   = Skia.RRectXY(rect, radiusX, radiusY); // rounded rect
const col  = Skia.Color("rgba(0,200,255,0.6)");    // SkColor (hex / rgba / named)

// Paint — a mutable bag of draw attributes
const p = Skia.Paint();
p.setColor(col);
p.setStyle(PaintStyle.Stroke);                     // or PaintStyle.Fill (default)
p.setStrokeWidth(2);
p.setAlphaf(0.75);                                 // 0..1 alpha multiplier
p.setBlendMode(BlendMode.DstOver);                 // Porter-Duff + extras
p.setShader(someShader);
p.setImageFilter(Skia.ImageFilter.MakeBlur(14, 14, TileMode.Clamp, null));
p.setMaskFilter(Skia.MaskFilter.MakeBlur(BlurStyle.Normal, 6, true)); // respectCTM=true

// Shaders
const grad = Skia.Shader.MakeLinearGradient(
  { x, y }, { x: x + w, y: y + h },
  [Skia.Color("#22d3ee"), Skia.Color("#f472b6")],
  [0, 1], TileMode.Clamp,
);
```

You then draw onto an `SkCanvas` (obtained from a picture recorder, §3):

```tsx
canvas.drawRect(rect, paint);
canvas.drawRRect(rr, paint);
canvas.drawCircle(cx, cy, r, paint);
canvas.drawPath(path, paint);
canvas.drawPatch(cubics, colors, texs, BlendMode.DstOver, paint); // Coons patch (§9)
canvas.drawPicture(otherPicture);
canvas.save(); canvas.translate(dx, dy); canvas.scale(s, s); /* ... */ canvas.restore();
canvas.saveLayer(paint); /* draws here are grouped */ canvas.restore(); // applies layer paint
```

This is the same `SkCanvas` you'd get inside a worklet on mobile — the difference is you call
it synchronously from a frame-driven `useMemo`, not a `useDerivedValue` worklet.

## 3. Pictures are the unit of work

An `SkPicture` is a **recorded list of draw commands — not pixels.** Recording is cheap
(no rasterization, no GPU surface, no memory proportional to resolution), which is exactly
what a long offline render needs. Two ways to make one:

```tsx
// Preferred: createPicture takes a draw callback + bounds.
const picture = createPicture((canvas) => drawField(canvas, opts), { width, height });

// Equivalent lower-level form:
const rec = Skia.PictureRecorder();
const canvas = rec.beginRecording(Skia.XYWHRect(0, 0, width, height));
drawField(canvas, opts);
const picture = rec.finishRecordingAsPicture();
```

Replay it in the declarative tree with `<Picture>`:

```tsx
import { SkiaCanvas } from "@remotion/skia";   // or <Canvas> in a plain RN/web host
import { Picture } from "@shopify/react-native-skia";

return (
  <SkiaCanvas width={width} height={height}>
    <Picture picture={fieldPicture} />
    <Picture picture={glassPicture} />
  </SkiaCanvas>
);
```

> `<Picture>` ignores group paint properties — to apply an effect to a whole picture, wrap it
> in a `<Group layer={<Paint>…</Paint>}>` (the layer-effect rule from `core-api.md`), or bake
> the effect into the recording with `saveLayer` (§9).

## 4. Sample a picture as a shader — `picture.makeShader`

This is the move that replaces offscreen rasterization. Instead of rendering a layer to an
image (which needs `readPixels` / a `Surface` — see §6), turn the **recorded picture** into a
shader and feed it straight into a runtime effect:

```tsx
const fieldShader = fieldPicture.makeShader(
  TileMode.Clamp,   // tileX
  TileMode.Clamp,   // tileY
  FilterMode.Linear, // smooth sampling — Nearest shows refraction artifacts
);
```

The picture's bounds map 1:1 to the canvas, so the shader samples in **device pixels** — no
resolution/uv round-trip needed. (Note: the published docs show a no-arg `makeShader()`; the
real binding — and this repo — pass tile modes + a filter mode. Trust the working signature.)

## 5. Runtime effects, imperatively — `makeShaderWithChildren`

Compile the SKSL once at module scope (it returns `null` on a compile error — handle it), then
build a shader by passing a **flat positional uniform array** and **child shaders in
declaration order**:

```tsx
// Lazily compiled, shared across renders. Null if compilation fails.
let refractEffect: SkRuntimeEffect | null | undefined;
const getRefractEffect = (): SkRuntimeEffect | null => {
  if (refractEffect === undefined) {
    refractEffect = Skia.RuntimeEffect.Make(REFRACTION_SKSL) ?? null;
  }
  return refractEffect;
};

const effect = getRefractEffect();
const bodyPaint = Skia.Paint();
if (effect) {
  const bodyShader = effect.makeShaderWithChildren(
    [
      g.cx, g.cy,         // center        (float2)
      g.w / 2, g.h / 2,   // halfSize      (float2)
      g.radius,           // radius        (float)
      thickness, disp, ior, chroma, specular, frost,
      rim[0], rim[1], rim[2], // rimTint   (float3)
      frame / fps,        // time          (float)
    ],
    [fieldShader, blurredShader], // map to `uniform shader image; uniform shader blurredImage;`
  );
  bodyPaint.setShader(bodyShader);
} else {
  // Graceful degrade — a frosted blur if the shader didn't compile.
  bodyPaint.setShader(fieldShader);
  bodyPaint.setImageFilter(Skia.ImageFilter.MakeBlur(14, 14, TileMode.Clamp, null));
}
canvas.drawRRect(rr, bodyPaint);
```

Uniform order in the array must match the SKSL declaration order exactly; a `float2` consumes
two entries, a `float3` three. There's no name-keyed form for `makeShaderWithChildren` — it's
positional. (The declarative `<Shader uniforms={{…}}>` form in `shaders.md` *is* name-keyed;
use that when you're in JSX, this when you're imperative.)

## 6. Why not `BackdropFilter` / offscreen surfaces here

The naive glassmorphism recipe — `<BackdropBlur>` / `<BackdropFilter filter={<Shader/>}>` —
**does not work for a runtime shader on CanvasKit.** And the obvious fallback, rasterizing a
layer per frame to sample it, is a memory trap:

- `canvas.readPixels(...)`, `surface.makeImageSnapshot()`, and `Skia.Surface.MakeOffscreen`
  each materialize a full-resolution pixel buffer on the WASM heap. Do that every frame in a
  long render and it climbs until the process crashes (observed ~frame 500 of an 1800-frame
  render).

The picture-shader route (§4) avoids pixels entirely: a command list is cheap to record, and
`makeShader` samples it without ever rasterizing to a buffer you have to free. Reserve
`makeImageSnapshot` for a genuine one-shot export, never a per-frame inner loop.

## 7. WASM-heap disposal — the make-or-break gotcha

Imperatively-created CanvasKit objects (`Paint`, `Shader`, `Image`, `Surface`, `MaskFilter`,
`Picture`, …) are **not garbage-collected** — they hold WASM heap that must be freed
explicitly. On a long render, skipping this exhausts memory and crashes. The react-native-skia
web wrappers keep the underlying CanvasKit object on `.ref`, which exposes `.delete()`:

```ts
/** Free one CanvasKit object safely (no-op if already gone). */
export const del = (obj: unknown): void => {
  try {
    const ref = (obj as { ref?: { delete?: () => void } } | null)?.ref;
    if (ref && typeof ref.delete === "function" &&
        !(ref as { isDeleted?: () => boolean }).isDeleted?.()) {
      ref.delete();
    }
  } catch {
    // already deleted / not a host object — ignore
  }
};
```

Per-frame pattern: keep the previous frame's picture at module scope, dispose it before
recording the next one, then cache the new one:

```tsx
let prevFieldPicture: SkPicture | null = null;

export const useFieldPicture = (o: FieldOpts): SkPicture =>
  useMemo(() => {
    if (prevFieldPicture) { del(prevFieldPicture); prevFieldPicture = null; }
    const picture = createPicture((canvas) => drawField(canvas, o), {
      width: o.width, height: o.height,
    });
    prevFieldPicture = picture;
    return picture;
    // deps: every value drawField reads, incl. `frame`
  }, [o.width, o.height, o.frame, o.fps, o.gather, o.fragmentOpacity, o.constellation]);
```

### Instance-scoped vs module-scoped — pick by where you render

The module-scope `prevFieldPicture` above is the **simplest correct form for a one-shot
offline render** (a CLI/server render is a single component instance, frames run
sequentially, and the process exits afterward — so the cursor is never shared and the final
frame's leak doesn't matter). It's what the repo ships.

But a module-scope cursor is shared by *every* mount of the component. If the same composition
can be **mounted more than once at the same time** (Remotion Studio preview + a thumbnail,
React StrictMode's double-invoke in dev, or two `<Sequence>`s using it), one instance will
`del()` a picture another instance is still displaying → use-after-free (black frame or a
"deleted object" crash). Disposing inside `useMemo` (a render-phase side effect) is also not
safe under StrictMode/concurrent/discarded renders, and a module cursor never frees the last
picture on unmount. For interactive/Studio/multi-instance use, scope the previous picture to
the instance with `useRef` and dispose in a `useEffect` cleanup:

```tsx
export const useFieldPicture = (o: FieldOpts): SkPicture => {
  const prev = useRef<SkPicture | null>(null);
  const picture = useMemo(
    () => createPicture((c) => drawField(c, o), { width: o.width, height: o.height }),
    [o.width, o.height, o.frame, o.fps /* …everything drawField reads */],
  );
  // free the prior picture once the new one is committed; free the last on unmount
  useEffect(() => {
    const stale = prev.current;
    prev.current = picture;
    return () => del(stale);
  }, [picture]);
  return picture;
};
```

### The critical sub-rule: don't dispose inside a recording

Dispose the **whole picture**, not the individual paints/shaders you created inside its
`createPicture` callback. Deleting them inside the callback is a footgun: the order relative
to the `draw*` call is easy to get wrong (delete before the draw records and you corrupt the
recording), and the picture is the natural unit of cleanup anyway. The transient paints and
shaders are small; the repo runs 1800-frame renders without individually freeing them. Spend
your disposal effort on the per-frame **pictures** (and any per-frame `Surface`/`Image`),
which are what actually grow the heap.

```tsx
// ❌ WRONG — the picture still references this paint at replay time
createPicture((canvas) => {
  const paint = Skia.Paint();
  canvas.drawRect(rect, paint);
  del(paint);                 // BUG
}, { width, height });

// ✅ RIGHT — let the picture own its paints; dispose the picture as a unit
if (prevPicture) del(prevPicture);
const picture = createPicture((canvas) => {
  const paint = Skia.Paint();
  canvas.drawRect(rect, paint);
}, { width, height });
prevPicture = picture;
```

**Never dispose:** objects created once at startup (the lazily-compiled `RuntimeEffect`),
or anything still referenced by a live picture. **Always dispose:** per-frame pictures, and
any per-frame paint/shader you build *outside* a recording (e.g. the body shader in §5, if you
hold it) once it's no longer needed.

## 8. Worked example — Liquid-Glass refraction

The signature pattern, assembled from the pieces above. A persistent stage records the
backdrop "field" and the glass each frame and renders both as pictures:

```tsx
export const EngraStage: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const { glass, gather, fragmentOpacity, constellation } = stageStateAt(frame);

  // 1. Record the ambient field as a cheap picture (drawn imperatively, §2/§3).
  const fieldPicture = useFieldPicture({ width, height, frame, fps, gather, fragmentOpacity, constellation });
  // 2. A frosted copy — the sharp field replayed inside a blurred saveLayer (§9).
  const blurredFieldPicture = useBlurredFieldPicture({ field: fieldPicture, width, height, frame, blur: 20 });
  // 3. Record the glass: its body shader samples BOTH field pictures (§4/§5).
  const glassPicture = useGlassPicture({ fieldPicture, blurredFieldPicture, width, height, glass, frame, fps });

  return (
    <SkiaCanvas width={width} height={height}>
      <Picture picture={fieldPicture} />
      <Picture picture={glassPicture} />
    </SkiaCanvas>
  );
};
```

Inside `useGlassPicture`, the glass body is `drawRRect` painted with the refraction shader
from §5, then stacked with a milky tint fill and a corner→corner specular rim (a blurred halo
+ a crisp hairline via `Skia.Shader.MakeLinearGradient` + `setMaskFilter`).

The SKSL itself (`src/components/skia/refraction.sksl.ts`) models the panel as a slab with a
rounded-over edge and traces a real `refract()` ray:

- **`sdRoundRect(p, halfSize, radius)`** — signed distance to the rounded rect (negative
  inside). Outside the body, pass the backdrop straight through.
- **Surface normal from the SDF gradient**, computed by **finite differences** — SKSL/CanvasKit
  has no `dFdx`/`dFdy`, so sample `sdRoundRect` at `±eps`. The normal lies in-plane at the
  border (max bend) and points straight up one `thickness` inside (flat → the center stays a
  clear lens).
- **`refract(incident, n, 1.0/ior)`** then trace to the backdrop distance to get the sample
  point; **chromatic split** samples R/G/B at `±dispersion` along the refraction vector.
- **Edge-only frost**: `mix(sharp, blurredImage.eval(...), frost * rim)` — `rim = 1 - n.z`, so
  frost rides only the curved bevel and the body stays sharp.
- **Fresnel rim** sheen, a faint **time-driven caustic** confined to the edge band, and **2×2
  supersampling** in `main` to tame aliasing.

This is the react-native-skia `LiquidGlass` (Shader2) technique. The canonical walkthrough is
the official tutorial **"Liquid Glass with React Native Skia"**
(https://www.youtube.com/watch?v=qYFMOMVZoPY); this repo adapts it to a single axis-aligned
device-px rounded rect with two child field shaders.

## 9. Supporting recipes

### Frosted copy via `saveLayer` + blur (no offscreen surface)

Record the sharp picture into a blurred layer — still picture-based, so it disposes as a unit:

```tsx
const picture = createPicture((canvas) => {
  const paint = Skia.Paint();
  paint.setImageFilter(Skia.ImageFilter.MakeBlur(blur, blur, TileMode.Clamp, null));
  canvas.saveLayer(paint);     // everything until restore() is grouped...
  canvas.drawPicture(field);
  canvas.restore();            // ...then the blur applies to the whole layer
}, { width, height });
```

### Flowing mesh gradient via `canvas.drawPatch` (Coons bicubic patches)

For a "Gen-Z" animated brand field. Each cell is a 12-control-point cubic patch with 4 corner
colors. Two gotchas:

- **Use `BlendMode.DstOver`** for colors-only patches — `SrcOver` doesn't render them on
  CanvasKit.
- **Pin the grid edges and over-scan ~15%** so seams never enter frame, and **sample each
  vertex's color from its *undisplaced* position** so hues hold steady while the geometry
  flows.

```tsx
canvas.drawPatch(cubics /* 12 SkPoint */, colors /* 4 SkColor */, null, BlendMode.DstOver, paint);
```

### Cache parsed SVG line-art

`Skia.Path.MakeFromSVGString` is comparatively expensive — parse once at module scope, reuse
every frame; animate by drawing each path with a per-element local progress (`Path` trim or a
staggered alpha) rather than re-parsing.

```tsx
let cached: ReadonlyArray<{ path: SkPath; color: string }> | null = null;
const paths = () => (cached ??= SHAPES.flatMap((s) => {
  const path = Skia.Path.MakeFromSVGString(s.d);
  return path ? [{ path, color: s.color }] : [];
}));
```

## Sanity checklist for offline Skia

- Every value derives from the frame — no `useSharedValue`/`useClock`/`withTiming`.
- Per-frame pictures are disposed (previous freed before the next is recorded).
- No paint/shader is `del()`'d inside a `createPicture` callback.
- No per-frame `readPixels` / `makeImageSnapshot` / offscreen `Surface` in the hot path —
  use `picture.makeShader` instead.
- `RuntimeEffect.Make` result is null-checked with a graceful fallback.
- `makeShaderWithChildren` uniform array matches SKSL declaration order (float2 = 2 slots…).
- Picture/runtime-shader sampling uses `FilterMode.Linear`.
- The runtime effect is compiled once at module scope, never per frame, never disposed.

## See also (this repo)

Repo-specific offline effects built on these exact patterns — SDF color-flow, a projected neon
wireframe, and picture/image-sampled shader scene transitions (page-curl / displacement /
noise-dissolve / crosswarp) — live in the `visual-craft` skill: its
`references/effects-library.md` (decision map) and `docs/effects.md` (full API), implemented under
`src/effects/`. Reach for those before re-deriving an offline Skia effect here.
