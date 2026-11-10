# Shaders

Detailed reference for SKSL (Skia's shading language), `RuntimeEffect`, uniforms, nested shaders, gradients, and Perlin noise. Read this when you're writing fragment shaders, porting GLSL from Shadertoy, building procedural patterns, or composing multiple color sources.

## SKSL — Skia's shading language

SKSL is GLSL-shaped but not GLSL. The syntax is close, the built-ins differ. The reference for differences: https://github.com/google/skia/tree/main/src/sksl#readme. Test shaders interactively at https://shaders.skia.org/.

One built-in gap worth flagging up front: **SKSL has no `dFdx`/`dFdy`** (screen-space derivatives). When you need a gradient — e.g. the surface normal of an SDF — compute it by **finite differences**, sampling your function at `±eps` and subtracting. The offline liquid-glass shader does exactly this (`references/offline-rendering.md` § 8).

### Compiling

```tsx
import { Skia } from "@shopify/react-native-skia";

const source = Skia.RuntimeEffect.Make(`
vec4 main(vec2 pos) {
  vec2 canvas = vec2(256);
  vec2 uv = pos / canvas;
  return vec4(uv.x, uv.y, 0.5, 1);
}`);

if (!source) throw new Error("Shader compile failed");
```

`RuntimeEffect.Make` returns `null` on a compile error. Always check, even in dev — silent failures are easy to miss when the shader just renders black.

> **TS gotcha:** SKSL is almost always stored in a template literal (`` Skia.RuntimeEffect.Make(`…`) ``). A stray **backtick inside a shader comment** (e.g. writing `` `thickness` `` in an explanatory comment) prematurely closes the template literal, and `tsc` reports a cryptic `',' expected` pointing *into* the shader source. Don't use backticks inside SKSL comments.

### Declarative `<Shader>` vs imperative `makeShader`

There are two ways to turn a compiled effect into a shader, and they take uniforms
**differently**. In JSX, `<Shader source={effect} uniforms={{…}}>` accepts a **name-keyed**
object (shown throughout this file) — the wrapper flattens it for you. The imperative methods on
the effect take a **flat positional `number[]`** instead:

```tsx
makeShader(uniforms: number[], localMatrix?): SkShader
makeShaderWithChildren(uniforms: number[], children?: SkShader[], localMatrix?): SkShader
```

```tsx
// no children
const shader = effect.makeShader([w, h, t]);

// flat uniform array + child shaders, in declaration order:
const shader = effect.makeShaderWithChildren(
  [cx, cy, w / 2, h / 2, radius, time],  // order MUST match the SKSL uniform block
  [imageShaderA, imageShaderB],          // map to `uniform shader …;` in order
);
paint.setShader(shader);
canvas.drawRRect(rr, paint);
```

The flat array is unforgiving: a `float2` consumes two entries, a `float3` three, so the
length and order must track the uniform declarations exactly (the effect can tell you the
expected total via `getUniformFloatCount()`). There is no name-keyed variant of these imperative
methods. This is the backbone of the offline liquid-glass effect; see
`references/offline-rendering.md` § 5.

### The `main` function

Every SKSL shader exports `main(vec2 pos)` returning `vec4` (RGBA, premultiplied). `pos` is the pixel coordinate in canvas space, not normalized — you divide by `resolution` (or hard-code a uniform) to get UV in [0,1].

```sksl
vec4 main(vec2 pos) {
  vec2 uv = pos / resolution;   // 0..1 across the drawing
  return vec4(uv.x, uv.y, 0.0, 1.0);
}
```

### Uniforms

Uniforms are inputs you pass from JS. Supported types: `float`, `float2`, `float3`, `float4`, `float2x2`, `float3x3`, `float4x4`, `int`, `int2`, `int3`, `int4`, plus arrays of any of these.

```sksl
uniform vec2  resolution;
uniform float t;
uniform vec4  color;
uniform float points[12];      // array
```

In JS, the keys must match the uniform names exactly:

```tsx
<Shader
  source={source}
  uniforms={{
    resolution: vec(256, 256),
    t: clock.value,
    color: [0.0, 0.5, 1.0, 1.0],
    points: [/* 12 numbers */],
  }}
/>
```

For animated uniforms, wrap the object in `useDerivedValue` so updates run on the UI thread:

```tsx
const uniforms = useDerivedValue(() => ({
  resolution: vec(width, height),
  t: clock.value / 1000,
}));
return (
  <Canvas style={{ width, height }}>
    <Fill><Shader source={source} uniforms={uniforms} /></Fill>
  </Canvas>
);
```

### Common patterns

**SDF circle:**

```sksl
uniform vec2 c;
uniform float r;

vec4 main(vec2 pos) {
  float d = distance(pos, c) - r;
  return vec4(vec3(step(0.0, -d)), 1.0);
}
```

**Time-driven hue cycle:**

```sksl
uniform float t;
uniform vec2 resolution;

vec3 hsv2rgb(vec3 c) {
  vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
  vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
  return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

vec4 main(vec2 pos) {
  vec2 uv = pos / resolution;
  return vec4(hsv2rgb(vec3(uv.x + t * 0.1, 0.8, 1.0)), 1.0);
}
```

**Glow / radial falloff:**

```sksl
uniform vec2 c;
uniform float r;
uniform vec3 color;

vec4 main(vec2 pos) {
  float d = length(pos - c);
  float a = smoothstep(r, 0.0, d);
  return vec4(color * a, a);
}
```

## Nested shaders (`<Shader>` as a child)

Shaders can take other shaders as children. The `uniform shader name;` declaration in SKSL accepts a child shader. This is how you sample an image inside a fragment shader.

```tsx
import { Canvas, Skia, ImageShader, Shader, Fill, useImage } from "@shopify/react-native-skia";

const source = Skia.RuntimeEffect.Make(`
uniform shader image;
half4 main(float2 xy) {
  xy.x += sin(xy.y / 3.0) * 4.0;
  return image.eval(xy).rbga;   // sample with offset, then swizzle channels
}`)!;

const Demo = () => {
  const image = useImage(require("./photo.jpg"));
  if (!image) return null;
  return (
    <Canvas style={{ width: 256, height: 256 }}>
      <Fill>
        <Shader source={source}>
          <ImageShader
            image={image}
            fit="cover"
            rect={{ x: 0, y: 0, width: 256, height: 256 }}
          />
        </Shader>
      </Fill>
    </Canvas>
  );
};
```

Multiple child shaders are positional — they map to the `uniform shader` declarations in SKSL in order of appearance.

## Built-in gradient shaders

You almost never need a custom shader for gradients — RN Skia ships four. All take a `colors` array (and optional `positions` for non-uniform stops), plus geometry-specific props.

### LinearGradient

```tsx
<Rect x={0} y={0} width={256} height={256}>
  <LinearGradient
    start={vec(0, 0)}
    end={vec(256, 256)}
    colors={["blue", "yellow"]}
  />
</Rect>
```

### RadialGradient

```tsx
<RadialGradient
  c={vec(128, 128)}
  r={128}
  colors={["blue", "yellow"]}
/>
```

### SweepGradient

A "conic" gradient — colors sweep around a center point.

```tsx
<SweepGradient
  c={vec(128, 128)}
  start={0}      // degrees
  end={360}
  colors={["cyan", "magenta", "yellow", "cyan"]}
/>
```

### TwoPointConicalGradient

Two circles with different radii; useful for spotlight effects.

```tsx
<TwoPointConicalGradient
  start={vec(128, 128)} startR={128}
  end={vec(128, 16)}    endR={16}
  colors={["blue", "yellow"]}
/>
```

### Shared gradient props

| Prop | Type | Notes |
| --- | --- | --- |
| `colors` | `string[]` or `SharedValue<string[]>` | Stops. |
| `positions` | `number[]` | Optional explicit positions [0,1]. Same length as `colors`. |
| `mode` | `"clamp" \| "repeat" \| "mirror" \| "decal"` | What happens outside the gradient range. |
| `flags` | `number` | `1` = premultiply before interpolation (smoother for alpha). |
| `transform` | `Transforms2d` | Local transform of the gradient. |

For animated colors, see `references/animations.md` § Color interpolation — must use `interpolateColors` from Skia, not Reanimated.

## Other shader sources

### `ImageShader`

Use an image as a shader. Useful for tiling textures or feeding an image into a runtime shader.

```tsx
<ImageShader
  image={image}
  fit="cover"
  rect={rect(0, 0, width, height)}
  tx="repeat"     // tile mode X
  ty="repeat"     // tile mode Y
/>
```

### Picture shader (`picture.makeShader`)

Sample a recorded `SkPicture` as a shader — the offline-safe alternative to rasterizing a
layer to an image (which leaks the WASM heap per frame). The picture's bounds map 1:1 to the
canvas, so the shader samples in device pixels.

```tsx
const shader = picture.makeShader(TileMode.Clamp, TileMode.Clamp, FilterMode.Linear);
```

Use `FilterMode.Linear` for smooth sampling. Feed the result straight into a runtime effect via
`makeShaderWithChildren` (above). See `references/offline-rendering.md` § 4.

### `ColorShader`

A single solid color as a shader — useful as a child of `<Blend>`.

```tsx
<ColorShader color="rgba(255,0,0,0.5)" />
```

### Imperative shader factories (`Skia.Shader.*`)

When building shaders by hand (outside JSX), the same sources exist as factory methods:

```tsx
Skia.Shader.MakeColor(Skia.Color("rgba(255,0,0,0.5)"));        // solid color
Skia.Shader.MakeBlend(BlendMode.Screen, one, two);             // blend two shaders
Skia.Shader.MakeLinearGradient(p0, p1, colors, positions, TileMode.Clamp);
Skia.Shader.MakeRadialGradient(center, radius, colors, positions, TileMode.Clamp);
Skia.Shader.MakeFractalNoise(freqX, freqY, octaves, seed, tileW, tileH); // freqs in [0,1]
Skia.Shader.MakeTurbulence(freqX, freqY, octaves, seed, tileW, tileH);
```

`colors` is `SkColor[]`; `positions` may be `null`. Noise frequencies must be in `[0.0, 1.0]`;
non-zero `tileW`/`tileH` make the noise tileable for that size (pass `0, 0` for non-tiled).

### `Turbulence` and `FractalNoise`

Perlin-noise–like procedural patterns.

```tsx
<Turbulence freqX={0.05} freqY={0.05} octaves={2} />
<FractalNoise freqX={0.1} freqY={0.1} octaves={4} seed={1} />
```

Compose with `<Blend>` and `<ColorMatrix>` to make clouds, marble, water surface, paper texture.

### `Blend`

Combines two shaders with a blend mode. The blend mode controls how the top shader is composited onto the bottom.

```tsx
<Blend mode="screen">
  <Turbulence freqX={0.05} freqY={0.05} octaves={2} />
  <LinearGradient
    start={vec(0, 0)}
    end={vec(256, 256)}
    colors={["#2A0944", "#A12568"]}
  />
</Blend>
```

The mode list is the same as paint `blendMode`: `srcOver`, `multiply`, `screen`, `overlay`, `darken`, `lighten`, etc.

## Putting it together — the shader pipeline

A drawing's paint pipeline runs in this order:

1. **Shader** — produces the source color for each pixel (gradient, image, runtime effect, etc.)
2. **Color filter** — transforms the source color (matrix, hue shift, B&W, etc.)
3. **Image filter** — operates on the rasterized output (blur, shadow, displacement)
4. **Mask filter** — blurs the alpha channel before blending
5. **Blend mode** — composites the result over the canvas

You stack them as children of the drawing:

```tsx
<Fill>
  <ColorMatrix matrix={SEPIA}>
    <Blur blur={2} mode="clamp">
      <Shader source={runtimeEffect} uniforms={uniforms}>
        <ImageShader image={img} fit="cover" rect={rect(0, 0, 256, 256)} />
      </Shader>
    </Blur>
  </ColorMatrix>
</Fill>
```

The nesting order is *outside-in*: outer effects wrap inner ones. The outermost effect is the last to run on the pixel.

## Porting from GLSL / Shadertoy

The big differences vs Shadertoy's GLSL:

| Shadertoy / GLSL | SKSL |
| --- | --- |
| `void mainImage(out vec4 frag, in vec2 fragCoord)` | `vec4 main(vec2 pos)` |
| `iResolution.xy` | A `resolution` uniform you pass in |
| `iTime` | A `t` uniform you pass in (or `useClock`) |
| `iMouse` | Pan/tap gesture → shared value → uniform |
| Texture sampling: `texture(iChannel0, uv)` | Child `uniform shader x;` + `x.eval(coord)` |
| `gl_FragCoord` | `pos` parameter |

When porting, replace the `mainImage` signature, switch built-ins, and pass any "i*" variables in as uniforms. Most fragment shaders convert in a few minutes once the pattern clicks.

## Troubleshooting

- **All black output:** `Skia.RuntimeEffect.Make` returned null (compile failed) or your shader returns `vec4(0)`. Add `if (!source) throw new Error("compile failed")` so you see the error.
- **Shader compiles but doesn't update:** Uniforms are missing or named differently from the SKSL declaration. Names must match exactly.
- **Animated uniform feels janky:** Make sure `uniforms` is wrapped in `useDerivedValue` so updates happen on the UI thread; recreating the uniforms object on every React render forces a JS→UI hop per frame.
- **Image shader looks wrong / inverted:** Check the `fit` and `rect` props on `<ImageShader>`. The shader gets pixel coordinates in canvas space, not the image's own space.
- **Wrong on iOS vs Android:** Floating-point precision can differ on some Android GPUs. Use `highp` for critical paths, or precompute on the CPU and pass via uniform.
- **Compile-time error not surfacing:** Set `__DEV__` shader logging on, or eyeball at https://shaders.skia.org/ — the playground catches most syntax errors.
