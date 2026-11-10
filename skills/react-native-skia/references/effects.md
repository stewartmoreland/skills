# Effects — image filters, backdrop filters, mask filters, color filters, path effects

Reference for the visual-effect layer of Skia. Each section covers what the effect does, when to use it, and the canonical setup.

## Image filters

Image filters operate on the rasterized pixel output of a drawing. They run *after* the shader and color filter stages.

### `<Blur>`

Gaussian blur applied to the drawing's pixels.

```tsx
<Image image={image} x={0} y={0} width={256} height={256} fit="cover">
  <Blur blur={4} mode="clamp" />
</Image>
```

| Prop | Type | Notes |
| --- | --- | --- |
| `blur` | `number \| Vector` | Blur radius. Pass a vector for asymmetric blur (`vec(rx, ry)`). |
| `mode` | `"clamp" \| "repeat" \| "mirror" \| "decal"` | Edge behavior. `clamp` extends edge pixels — usually what you want. |

### `<Shadow>`

Drop shadow. Stack two of them as children of a drawing to get a glow or soft shadow effect.

```tsx
<RoundedRect x={20} y={20} width={200} height={120} r={16} color="white">
  <Shadow dx={0} dy={8} blur={16} color="rgba(0,0,0,0.2)" />
</RoundedRect>
```

| Prop | Type | Notes |
| --- | --- | --- |
| `dx`, `dy` | `number` | Offset of the shadow. |
| `blur` | `number` | Shadow softness. |
| `color` | `string` | Shadow color (alpha bakes the intensity). |
| `inner` | `boolean` | Inner shadow instead of outer. |
| `shadowOnly` | `boolean` | Draw only the shadow; useful for stacking. |

### `<DisplacementMap>`

Distorts pixels by sampling a child shader's red/green channels as an x/y offset. Used for water surfaces, heat haze, page curl effects.

```tsx
<Image image={image} x={0} y={0} width={256} height={256} fit="cover">
  <DisplacementMap channelX="r" channelY="g" scale={20}>
    <Turbulence freqX={0.01} freqY={0.01} octaves={2} />
  </DisplacementMap>
</Image>
```

### `<Offset>`

Translates the drawing by `dx, dy`. Useful when composing multiple shadow-like effects.

```tsx
<Offset x={10} y={10} />
```

### `<Morphology>`

Dilate or erode the drawing — useful for outlining text or shapes by `radius` pixels.

```tsx
<Morphology operator="dilate" radius={2} />
<Morphology operator="erode" radius={2} />
```

### `<RuntimeShader>`

Use a `RuntimeEffect` as an image filter. Lets you write a fragment shader that takes the already-rendered pixels as input.

```tsx
const source = Skia.RuntimeEffect.Make(`
uniform shader image;
half4 main(float2 xy) {
  return image.eval(xy).bgra;   // swap red and blue
}`)!;

<Image image={image} ...>
  <RuntimeShader source={source} uniforms={{}} />
</Image>
```

### Composing image filters

Image filters chain as children-of-children. The outermost filter applies last.

```tsx
<Image image={image} x={0} y={0} width={256} height={256} fit="cover">
  <Blur blur={2} mode="clamp">
    <ColorMatrix
      matrix={[
        -0.578, 0.99,  0.588, 0, 0,
         0.469, 0.535, -0.003, 0, 0,
         0.015, 1.69, -0.703, 0, 0,
         0,     0,    0,     1, 0,
      ]}
    />
  </Blur>
</Image>
```

This applies a color matrix first, then blurs the result.

## Backdrop filters

Backdrop filters apply an effect to the content *behind* the drawing — what's already on the canvas at that point. This is how you do CSS `backdrop-filter: blur()` (glassmorphism).

Backdrop filters extend `<Group>`, so they accept `clip`, `transform`, etc. The clip defines the region the backdrop effect applies to.

### `<BackdropBlur>`

```tsx
<Canvas style={{ flex: 1 }}>
  <Image image={bg} x={0} y={0} width={width} height={height} fit="cover" />
  <BackdropBlur blur={12} clip={rrect(rect(40, 100, 280, 200), 24, 24)}>
    <Fill color="rgba(255,255,255,0.15)" />
  </BackdropBlur>
</Canvas>
```

The order matters: `<Image>` first lays down the photo; `<BackdropBlur>` then blurs whatever's beneath the clipped region; the `<Fill>` child tints the blurred area. This is the standard frosted-glass card recipe.

### `<BackdropFilter>`

More general — pass any image filter as the `filter` prop.

```tsx
const BLACK_AND_WHITE = [
  0, 1, 0, 0, 0,
  0, 1, 0, 0, 0,
  0, 1, 0, 0, 0,
  0, 1, 0, 1, 0,
];

<BackdropFilter
  clip={rect(0, 128, 256, 128)}
  filter={<ColorMatrix matrix={BLACK_AND_WHITE} />}
/>
```

Apply any combination — color matrix, blur, displacement map, runtime shader — to the canvas content underneath the clip.

> **CanvasKit / offline caveat.** On the WASM (web / offline) build, a **runtime shader cannot
> run as a backdrop filter** — `<BackdropFilter filter={<RuntimeShader/>}>` won't carry your
> effect. And the obvious workaround — snapshotting the backdrop to an image per frame to feed
> the shader — leaks the WASM heap (`readPixels`/`makeImageSnapshot`/offscreen `Surface` each
> allocate a full pixel buffer that isn't GC'd). Instead, record the backdrop as an `SkPicture`
> and sample it with `picture.makeShader()` fed into the effect. Blur, color-matrix, and plain
> displacement backdrops are fine on CanvasKit; only the **runtime-shader** backdrop is the
> problem. See `references/offline-rendering.md` § 6.

## Mask filters

Mask filters blur the alpha channel before the shape is composited. Different from image filters in that they don't touch the source color — they soften the shape edges.

### `<BlurMask>`

```tsx
<Circle cx={128} cy={128} r={80} color="cyan">
  <BlurMask blur={20} style="normal" />
</Circle>
```

Style modes:
- `normal` — standard blur
- `solid` — sharp interior, blurred outside (good for glows)
- `outer` — only the blurred halo, no interior
- `inner` — only the blurred interior, no exterior

Stack with `<Group>` to apply a glow to multiple shapes at once.

## Color filters

Color filters transform the source color channel-by-channel. They run between the shader and image filter stages.

### `<ColorMatrix>` / `<MatrixColorFilter>`

A 4×5 matrix multiplied with each pixel's RGBA. Layout: 5 entries per row (R, G, B, A, constant), 4 rows (output R, G, B, A).

```tsx
const SEPIA = [
  0.393, 0.769, 0.189, 0, 0,
  0.349, 0.686, 0.168, 0, 0,
  0.272, 0.534, 0.131, 0, 0,
  0,     0,     0,     1, 0,
];

<Image image={image} ...>
  <ColorMatrix matrix={SEPIA} />
</Image>
```

Common matrices:
- Black & white: `[0,1,0,0,0, 0,1,0,0,0, 0,1,0,0,0, 0,0,0,1,0]`
- Identity (passthrough): `[1,0,0,0,0, 0,1,0,0,0, 0,0,1,0,0, 0,0,0,1,0]`
- Invert: `[-1,0,0,0,1, 0,-1,0,0,1, 0,0,-1,0,1, 0,0,0,1,0]`
- High-contrast (metaball thresholding): `[1,0,0,0,0, 0,1,0,0,0, 0,0,1,0,0, 0,0,0,18,-7]`

Sites like https://kazzkiq.github.io/svg-color-filter/ give you matrices for arbitrary effects.

### `<LumaColorFilter>`

Converts color to grayscale based on luminance (used internally for monochrome conversions).

### `<BlendColorFilter>`

Applies a blend mode against a constant color.

```tsx
<BlendColorFilter color="red" mode="multiply" />
```

### `<LerpColorFilter>`

Mixes two color filters by a `t` value (0–1) — useful for animating between two color treatments.

```tsx
<LerpColorFilter t={progress}>
  <ColorMatrix matrix={SEPIA} />
  <ColorMatrix matrix={BLACK_AND_WHITE} />
</LerpColorFilter>
```

### `<LinearToSRGBGammaColorFilter>` / `<SRGBToLinearGammaColorFilter>`

Gamma corrections. Useful when feeding linear-space pixel data through filters that expect sRGB.

## Path effects

Path effects transform the geometry of a path *before* it's rasterized. Apply them as children of a `<Path>` or any path-based drawing.

### `<DashPathEffect>`

Dashes a stroked path.

```tsx
<Path path={p} style="stroke" strokeWidth={2} color="cyan">
  <DashPathEffect intervals={[10, 5]} phase={0} />
</Path>
```

Animating `phase` produces a "marching ants" / dotted-line-scroll effect.

### `<DiscretePathEffect>`

Adds jitter to a path — makes lines look hand-drawn or sketchy.

```tsx
<DiscretePathEffect length={4} deviation={3} seed={1} />
```

### `<CornerPathEffect>`

Rounds sharp corners by the given radius.

```tsx
<CornerPathEffect r={10} />
```

### `<Path1DPathEffect>`

Stamps a path along another path at intervals. Used for stylized borders, dotted lines with custom stamps, particle trails.

```tsx
<Path1DPathEffect path={stampPath} advance={20} phase={0} style="rotate" />
```

Styles:
- `translate` — translate without rotation
- `rotate` — rotate to follow the path direction
- `morph` — bend the stamp to follow the path

### `<Path2DPathEffect>`

Tiles a path across the canvas using a transformation matrix.

```tsx
<Path2DPathEffect path={tile} matrix={Skia.Matrix().scale(20, 20)} />
```

### `<Line2DPathEffect>` and `<SumPathEffect>`

Less common; see https://shopify.github.io/react-native-skia/docs/path-effects when you need them.

### Composing path effects with `<SumPathEffect>`

```tsx
<SumPathEffect>
  <DiscretePathEffect length={4} deviation={3} />
  <CornerPathEffect r={10} />
</SumPathEffect>
```

The combined effect applies both transformations to the path.

## Mask component

Different from "mask filter" above. `<Mask>` lets you use the alpha channel of one drawing as the mask for another.

```tsx
<Mask mode="luminance" mask={
  <Circle cx={128} cy={128} r={100} color="white" />
}>
  <Image image={image} x={0} y={0} width={256} height={256} fit="cover" />
</Mask>
```

The mask drawing's luminance (or alpha, depending on `mode`) determines what part of the masked drawing is visible. White = visible, black = invisible. Smooth gradients give smooth feathering.

| Prop | Type | Notes |
| --- | --- | --- |
| `mode` | `"alpha" \| "luminance"` | Which channel to read from the mask. |
| `mask` | `ReactElement` | The drawing to use as the mask. |
| children | `ReactElement[]` | The drawing(s) to mask. |

## Pipeline overview

For any drawing, effects apply in this order:

1. **Shader / Color** — what color is each pixel?
2. **Path effects** — geometry transformations of the source path.
3. **Color filters** — per-pixel color transformations.
4. **Mask filters** — alpha channel softening.
5. **Image filters** — operations on the rasterized output.
6. **Blend mode** — composite the result onto the canvas.
7. **Backdrop filters** — applied to whatever's already drawn beneath.

Stacking effects works by nesting them as children of the drawing or as children of each other. Outer effects apply later in the pipeline.

## When you need to apply effects to grouped content

Applying an image filter to a `<Group>` directly doesn't work — group paint properties don't include image filters. You have two options:

1. **`layer` prop on `<Group>`** — rasterizes the group's children into a bitmap, then applies the paint's effects:

```tsx
<Group
  layer={
    <Paint>
      <Blur blur={20} />
    </Paint>
  }
>
  <Circle cx={50} cy={128} r={120} color="lightblue" />
  <Circle cx={200} cy={128} r={120} color="lightblue" />
</Group>
```

2. **`<Mask>` or `<BackdropFilter>`** — depending on whether you want the filter to apply to the group's own pixels or to the content beneath it.

The `layer` approach is also the only way to apply effects to `<Picture>`, `<ImageSVG>`, and `<Paragraph>`, which ignore group paint properties.
