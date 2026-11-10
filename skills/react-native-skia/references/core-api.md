# Core API reference

Detailed reference for the foundational components — Canvas, Group, Paint, and the shape primitives. Read this when you need exact prop names, type signatures, or the details on inheritance, transforms, clipping, and layer effects.

## Canvas

The root of every Skia drawing. Behaves like a `<View>` from the layout side and as a portal into Skia's React renderer for everything inside.

| Prop | Type | Notes |
| --- | --- | --- |
| `style` | `ViewStyle` | Layout. Must produce bounded dimensions or nothing renders. |
| `ref` | `Ref<SkiaView>` | Use with `useCanvasRef()` to call `makeImageSnapshot()`. |
| `onSize` | `SharedValue<Size>` | Reanimated SV updated as canvas size changes. Use when sizing drives UI-thread animation. |
| `androidWarmup` | `boolean` | Draws first frame directly on Android compositor. Static icons and fully-opaque drawings only — animated or translucent canvases can misrender. |
| `mode` | `"default" \| "continuous"` | `continuous` re-renders every frame on the UI thread; default re-renders on prop changes. |

### Canvas sizing

**UI thread (preferred for animations):**

```tsx
const size = useSharedValue({ width: 0, height: 0 });
const rect = useDerivedValue(() => ({
  x: 0, y: 0, width: size.value.width, height: size.value.height,
}));
return (
  <Canvas style={{ flex: 1 }} onSize={size}>
    <Rect color="cyan" rect={rect} />
  </Canvas>
);
```

**JS thread (when you need width/height in regular React state):**

```tsx
const { ref, size: { width, height } } = useCanvasSize();
return (
  <Canvas style={{ flex: 1 }} ref={ref}>
    <Rect color="cyan" rect={{ x: 0, y: 0, width, height }} />
  </Canvas>
);
```

### Snapshotting

```tsx
const ref = useCanvasRef();
// later, on UI thread:
const image = ref.current?.makeImageSnapshot(); // SkImage
const bytes = image?.encodeToBytes();           // Uint8Array (PNG by default)
const b64   = image?.encodeToBase64();
```

For drawings that include textures (`useTexture`, `useImageAsTexture`, `usePictureAsTexture`), use `makeImageSnapshotAsync()` instead — it runs on the UI thread and has access to the same Skia context.

### Accessibility

Canvas supports the same accessibility props as View. To make individual canvas elements accessible (or tappable), overlay an `<Animated.View>` on top of them with matching transforms — the same recipe used for per-element gestures.

## Group

Group is the workhorse. It applies paint, transforms, clipping, and layer effects to its descendants.

| Prop | Type | Notes |
| --- | --- | --- |
| `transform` | `Transform2d` | RN transform syntax. Origin is top-left of the group, not center. Rotations in radians. |
| `origin` | `Point` | Shifts the transform origin. **Not inherited by children.** |
| `clip` | `Rect \| RRect \| SkPath` | Restricts drawing to this region. |
| `invertClip` | `boolean` | Inverts the clip region. |
| `layer` | `RefObject<Paint> \| ReactElement<Paint>` | Rasterizes children to a bitmap, then applies the paint's effects. |
| `zIndex` | `number` | Reorders drawing within the parent group. Defaults to 0. Negative values allowed. |
| (paint props) | various | Any paint property (`color`, `style`, `strokeWidth`, `opacity`, `blendMode`, `antiAlias`...) — inherited by descendants. |

### Paint inheritance

```tsx
<Group color="lightblue" style="stroke" strokeWidth={4}>
  <Circle cx={50} cy={50} r={40} />        {/* light-blue stroke, width 4 */}
  <Circle cx={150} cy={50} r={40} color="red" />  {/* red stroke, still width 4 */}
</Group>
```

### Transforms

```tsx
<Group origin={{ x: 100, y: 100 }} transform={[{ rotate: Math.PI / 4 }]}>
  <Rect x={75} y={75} width={50} height={50} color="cyan" />
</Group>
```

Available transforms: `translateX`, `translateY`, `scale`, `scaleX`, `scaleY`, `rotate`, `skewX`, `skewY`, `matrix`, plus 3D variants via `processTransform3d`.

### Clipping

```tsx
<Group clip={rect(10, 10, 200, 200)}>      {/* clip to rectangle */}
<Group clip={rrect(rect(10, 10, 200, 200), 16, 16)}>  {/* rounded */}
<Group clip={Skia.Path.MakeFromSVGString("M 0 0 ... Z")!}>  {/* path */}
<Group clip={path} invertClip>             {/* outside the path is shown */}
```

### Layer effects

The `layer` prop renders children to an offscreen bitmap and applies the paint's effects to the whole group. This is the **only way** to apply effects to `<Picture>`, `<SVG>` (`<ImageSVG>`), or `<Paragraph>` — they ignore group paint properties.

```tsx
<Group
  color="lightblue"
  layer={
    <Paint>
      <Blur blur={20} />
      <ColorMatrix matrix={[/* contrast */]} />
    </Paint>
  }
>
  <Circle cx={0} cy={128} r={120} />
  <Circle cx={256} cy={128} r={120} />
</Group>
```

This is also how you build "metaball" effects — render overlapping shapes into a layer, then run a high-contrast color matrix.

### FitBox

A `Group` variant that auto-scales children from a source rectangle to a destination rectangle.

```tsx
<FitBox src={rect(0, 0, 664, 308)} dst={rect(0, 0, 256, 256)} fit="contain">
  <Path path="M 170.1 215.5 ..." style="stroke" strokeWidth={30} />
</FitBox>
```

Useful for taking SVG exports (with `viewBox="0 0 664 308"`) and dropping them in at any canvas size.

## Paint

A paint is a bag of attributes telling Skia how to draw. You apply paint in three ways:

**As props on a drawing or group:**
```tsx
<Circle cx={50} cy={50} r={40} color="cyan" style="stroke" strokeWidth={4} />
```

**As `<Paint>` children of a drawing or group (allows multiple stacked paints):**
```tsx
<Circle c={vec(128, 128)} r={120}>
  <Paint color="lightblue" />                          {/* fill */}
  <Paint color="#adbce6" style="stroke" strokeWidth={10} />  {/* outer stroke */}
  <Paint color="#ade6d8" style="stroke" strokeWidth={5} />   {/* inner stroke */}
</Circle>
```

**As an imperative `Skia.Paint()` instance assigned via `paint={}`:**
```tsx
const paint = Skia.Paint();
paint.setColor(Skia.Color("lightblue"));
paint.setAntiAlias(true);
return <Circle paint={paint} cx={50} cy={50} r={40} />;
```

### Paint properties

| Property | Type | Notes |
| --- | --- | --- |
| `color` | string or `SkColor` | Hex, rgba, named colors, or `Skia.Color(...)`. |
| `style` | `"fill" \| "stroke"` | Default fill. |
| `strokeWidth` | `number` | Required when `style="stroke"`. |
| `strokeJoin` | `"miter" \| "round" \| "bevel"` | How corners join. |
| `strokeCap` | `"butt" \| "round" \| "square"` | How line ends are capped. |
| `strokeMiter` | `number` | Miter limit. |
| `opacity` | `number` | 0–1, multiplies the color's alpha. |
| `antiAlias` | `boolean` | Defaults to true. |
| `blendMode` | string | Porter-Duff and more: `clear`, `src`, `dst`, `srcOver`, `dstOver`, `srcIn`, `dstIn`, `srcOut`, `dstOut`, `srcATop`, `dstATop`, `xor`, `plus`, `modulate`, `screen`, `overlay`, `darken`, `lighten`, `colorDodge`, `colorBurn`, `hardLight`, `softLight`, `difference`, `exclusion`, `multiply`, `hue`, `saturation`, `color`, `luminosity`. |

### Paint children (complex paints)

These attach to a drawing or group as children and modify its paint pipeline:

- **Shaders** (`<LinearGradient>`, `<RadialGradient>`, `<SweepGradient>`, `<TwoPointConicalGradient>`, `<Shader>` with a `RuntimeEffect`, `<ImageShader>`, `<Turbulence>`, `<FractalNoise>`, `<ColorShader>`, `<Blend>`) — provide the color at each pixel.
- **Image filters** (`<Blur>`, `<Shadow>`, `<DisplacementMap>`, `<Offset>`, `<Morphology>`, `<RuntimeShader>`) — operate on the rendered pixels.
- **Color filters** (`<ColorMatrix>`, `<MatrixColorFilter>`, `<LumaColorFilter>`, `<LinearToSRGBGammaColorFilter>`, `<SRGBToLinearGammaColorFilter>`, `<BlendColorFilter>`, `<LerpColorFilter>`) — operate on individual color channels.
- **Mask filters** (`<BlurMask>`) — blur the alpha channel before drawing.
- **Path effects** (`<DashPathEffect>`, `<DiscretePathEffect>`, `<CornerPathEffect>`, `<SumPathEffect>`, `<Line2DPathEffect>`, `<Path1DPathEffect>`, `<Path2DPathEffect>`) — transform the path geometry.

## Shape primitives

### Circle

```tsx
<Circle cx={x} cy={y} r={r} color="cyan" />
// or
<Circle c={vec(x, y)} r={r} color="cyan" />
```

### Rect / RoundedRect

```tsx
<Rect x={0} y={0} width={200} height={100} color="cyan" />
<RoundedRect x={0} y={0} width={200} height={100} r={16} color="cyan" />
<RoundedRect rect={rrect(rect(0, 0, 200, 100), 16, 16)} color="cyan" />
```

For asymmetric corners use `rrect` with separate radii, or build with `Skia.PathBuilder.addRRect`.

### Line

```tsx
<Line p1={vec(0, 0)} p2={vec(100, 100)} color="cyan" strokeWidth={4} style="stroke" />
```

### Oval

```tsx
<Oval x={0} y={0} width={200} height={100} color="cyan" />
```

### Path

The most flexible primitive. Accepts an SVG path string or an `SkPath` built with `Skia.PathBuilder`.

```tsx
<Path path="M 128 0 L 168 80 ... Z" color="lightblue" />

const p = Skia.PathBuilder.Make()
  .moveTo(128, 0)
  .lineTo(168, 80)
  .lineTo(256, 93)
  .close()
  .build();
<Path path={p} color="lightblue" />
```

Path props:

| Prop | Type | Notes |
| --- | --- | --- |
| `path` | `SkPath \| string` | SVG notation or built path. |
| `start` | `number` | Trim start. 0–1. |
| `end` | `number` | Trim end. 0–1. Useful for stroke-draw animations. |
| `stroke` | `StrokeOptions` | `{ width, miter, precision }` — converts the path to its stroked outline as a fill. |
| `fillType` | `"winding" \| "evenOdd" \| "inverseWinding" \| "inverseEvenOdd"` | Inside-test for self-intersecting paths. |

Animating `start` and `end` is the standard way to do "stroke draw-in" animations:

```tsx
const end = useSharedValue(0);
useEffect(() => { end.value = withTiming(1, { duration: 1500 }); }, []);
return <Path path={p} style="stroke" strokeWidth={4} end={end} />;
```

### Polygons, meshes, and ellipses

Specialized primitives beyond the basics:

```tsx
// Frame / ring: even-odd of an outer and inner (rounded) rect.
<DiffRect outer={rrect(rect(0, 0, 256, 256), 25, 25)}
          inner={rrect(rect(50, 50, 156, 156), 50, 50)} color="lightblue" />

// Scatter dots / polyline: mode is "points" | "lines" | "polygon".
<Points points={[vec(128, 0), vec(168, 80), vec(256, 93)]}
        mode="polygon" style="stroke" strokeWidth={4} color="cyan" />

// Triangle mesh with per-vertex colors (a "gradient mesh").
<Vertices
  vertices={[vec(0, 0), vec(256, 0), vec(256, 256), vec(0, 256)]}
  colors={["#61DAFB", "#fb61da", "#dafb61", "#61fbcf"]}
  indices={[0, 1, 2, 0, 2, 3]}   // optional: reuse vertices without duplication
/>
```

| Component | Key props | Notes |
| --- | --- | --- |
| `<DiffRect>` | `outer`, `inner` (`Rect`/`RRect`) | The region between two rects. |
| `<Points>` | `points: Point[]`, `mode`, paint | `mode`: `"points"` \| `"lines"` \| `"polygon"`. |
| `<Vertices>` | `vertices: Point[]`, `colors?`, `indices?`, `textures?`, `mode?`, `blendMode?` | `mode`: `"triangles"` (default) \| `"triangleStrip"` \| `"triangleFan"`. Default blend is `dstOver` with colors, `srcOver` without. Pair `textures` with an `<ImageShader>` child to map an image across the mesh. |
| `<Atlas>` | `image`, `sprites`, `transforms` | Hundreds of sprites in one draw call; pair with `useRectBuffer`/`useRSXformBuffer`. |

For a **smooth** (bicubic, "Coons") mesh gradient rather than flat-shaded triangles, drop to
the imperative `canvas.drawPatch(cubics, colors, texs, blendMode, paint)` — see
`references/offline-rendering.md` § 9.

## Text

Two APIs:

- **`<Text>`** — single-line, font-based. Quick labels.
- **`<Paragraph>`** — full typography (line breaking, justification, multiple styles, emojis). Subject to the layer-effect rule for filters.

Always load fonts via `useFonts()` or `matchFont()`; raw font files won't work without registration.

## Imperative drawing

For one-off computations or pre-building paths/pictures, use the imperative API:

```tsx
Skia.Color("lightblue")
Skia.Paint()
Skia.PathBuilder.Make()
Skia.Path.MakeFromSVGString(svgStr)
Skia.PictureRecorder()
Skia.Surface.MakeOffscreen(width, height)
Skia.RRectXY(rect, rx, ry)
Skia.XYWHRect(x, y, w, h)
Skia.Color4f([r, g, b, a])
Skia.Data.fromBase64(str) / Skia.Data.fromBytes(uint8arr) / Skia.Data.fromURI(uri)
Skia.RuntimeEffect.Make(sksl)
Skia.Image.MakeImageFromEncoded(data)
Skia.Image.MakeImage({ width, height, alphaType, colorType }, data, rowBytes)
```

These run synchronously on the JS thread (or inside a `"worklet"` on the UI thread). They return Skia objects you can pass back into the declarative tree.

### Mutating a `Skia.Paint()`

The imperative paint is a mutable object with setters mirroring the declarative props:

```tsx
const p = Skia.Paint();
p.setColor(Skia.Color("rgba(0,200,255,0.6)"));
p.setStyle(PaintStyle.Stroke);   // or PaintStyle.Fill
p.setStrokeWidth(2);
p.setAlphaf(0.75);               // 0..1
p.setAntiAlias(true);
p.setBlendMode(BlendMode.DstOver);
p.setShader(shader);
p.setImageFilter(Skia.ImageFilter.MakeBlur(14, 14, TileMode.Clamp, null));
p.setMaskFilter(Skia.MaskFilter.MakeBlur(BlurStyle.Normal, 6, true)); // last arg = respectCTM
```

### Drawing onto an `SkCanvas`

Inside a picture recording (`createPicture` / `PictureRecorder`) or an offscreen surface you
issue draws directly:

```tsx
canvas.drawRect(rect, paint);
canvas.drawRRect(rr, paint);
canvas.drawCircle(cx, cy, r, paint);
canvas.drawPath(path, paint);
canvas.drawPicture(otherPicture);
canvas.drawPatch(cubics, colors, texs, BlendMode.DstOver, paint); // bicubic mesh patch
canvas.save(); canvas.translate(dx, dy); canvas.scale(s, s); /* … */ canvas.restore();
canvas.saveLayer(paint); /* grouped draws */ canvas.restore(); // applies layer paint (e.g. blur)
```

> **Lifetime warning.** Imperatively-created CanvasKit objects (paints, shaders, images,
> surfaces, pictures) are not garbage-collected — they must be freed with `.ref.delete()`. This
> only bites in long/offline renders that allocate per frame; for the disposal pattern and the
> "never delete inside a recording" rule, see `references/offline-rendering.md` § 7.

## Helpers and utilities

Useful imports from `@shopify/react-native-skia`:

- **`vec(x, y)`** — make a `Point`/`Vector`.
- **`rect(x, y, w, h)`** — make a `Rect`.
- **`rrect(rect, rx, ry)`** — make a `RoundedRect`.
- **`interpolateColors(value, inputRange, outputColors)`** — color interpolation that round-trips through Skia's color format. Use this instead of Reanimated's `interpolateColor`.
- **`processTransform3d(transforms)`** — for 3D card flips and perspective effects.
- **`fitRects(fit, src, dst)`** — compute src and dst rectangles for a given fit mode.

## Testing

Jest support via Skia's web mock:

```js
// jest.config.js
module.exports = {
  testEnvironment: "@shopify/react-native-skia/jestEnv.js",
  setupFilesAfterEnv: ["@shopify/react-native-skia/jestSetup.js"],
};
```

Plus a `transformIgnorePatterns` entry to keep Jest from transforming Skia files:

```js
"transformIgnorePatterns": [
  "node_modules/(?!(react-native|react-native.*|@react-native.*|@?react-navigation.*|@shopify/react-native-skia)/)"
]
```

The mock loads CanvasKit (WASM); tests run against the web implementation. Pixel-perfect output isn't guaranteed across platforms but the API surface is identical.
