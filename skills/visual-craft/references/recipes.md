# Recipes — frame-driven skeletons for the signature looks

Compact, copy-adaptable skeletons for the looks in `frame-refs/`. Each says **reuse X first**, then
gives the minimal frame-driven shape so you don't re-derive it. All assume
`const frame = useCurrentFrame()` and obey the one law (no clocks/CSS/Reanimated). Pull
color/ease/timing from `src/theme/tokens.ts`. For deep API detail, invoke the matching technical
skill and read its offline doc (see `engine-selection.md`).

> **Before re-deriving a skeleton, check the effects library** (`references/effects-library.md` /
> `docs/effects.md`). Many of these are already packaged: text entrances → `useEnter`/`RiseIn`/
> `Typewriter`; backgrounds → `AnimatedGradient`/`SdfFlow`; a projected wireframe → `Wireframe3D`;
> card surfaces → `FrostedCardStack`/`TiltCard`; depth → `useDepth`/`ParallaxLayer`. Reach for the
> component; drop to these skeletons only when you need something it doesn't cover.

---

## 1. Gradient line-chart draw-on  → `charts`

**Reuse:** `TimeSeriesCard.tsx`, `NeonStroke`/`NeonDot`, `useDrawProgress`.

```tsx
import { Path, Skia } from "@shopify/react-native-skia";
import { SkiaCanvas } from "@remotion/skia";
import { useDrawProgress } from "../components/svg";
import { NeonStroke, NeonDot } from "../components/skia/NeonPath";
import { tokens } from "../theme/tokens";

const PTS = [[10,220],[50,190],[90,150],[130,120],[170,90],[210,55],[250,30]] as const;
const path = Skia.Path.MakeFromSVGString(`M ${PTS.map(([x,y]) => `${x} ${y}`).join(" L ")}`)!;
const bounds = path.computeTightBounds();

const draw = useDrawProgress(28, 28);                 // line draws frames 28..56
// axis first, then line, then dots bloom as the line passes (start = 30 + i*4)
<SkiaCanvas width={280} height={280}>
  <NeonStroke path={path} progress={draw} colors={[tokens.neonBlue, "#66ccff"]} bounds={bounds} width={2.2} />
  {PTS.map(([x,y], i) => {
    const s = 30 + i*4;
    const o = interpolate(frame, [s, s+6], [0,1], {extrapolateLeft:"clamp", extrapolateRight:"clamp"});
    const r = interpolate(frame, [s, s+8, s+16], [3,6,3.5], {extrapolateLeft:"clamp", extrapolateRight:"clamp"});
    return <NeonDot key={i} cx={x} cy={y} r={r} color={tokens.neonBlue} opacity={o} />;
  })}
</SkiaCanvas>
```

Premium touches: animate the gradient `colors` warm→cool over the draw; place on a `grid`-density
`Background`; add a glowing leading dot at the line's head.

## 2. 4-layer neon glow (any line-art)  → `charts`, `tdm`

**Reuse:** `NeonStroke` directly — don't rebuild the glow. Build the path with
`Skia.Path.MakeFromSVGString` (or compose with `Skia.Path` ops), pass `progress` from frame for
draw-on, `glow` to fade a finished stroke. The 4 layers (halo/mid/hairline/core) are already inside.
If you ever need it raw: stack 4 `<Path>` with decreasing `strokeWidth` (×7, ×2.6, ×1, ×0.55),
`<Blur>` on the outer two, white on the core.

## 3. Mesh gradient / glowing blob field  → `gzm`

**Reuse:** `FloatingParticles.tsx` / `GeoShapes.tsx` for blobs; Skia imperative for true mesh.

- **Blob field (cheap, effective):** seeded positions, frame-driven drift, additive `<Blur>` halos:
```tsx
const rng = useMemo(() => mulberry32(0xB10B5), []);
const blobs = useMemo(() => Array.from({length: 8}, () => ({
  x0: rng(), y0: rng(), vx: (rng()-0.5)*0.3, vy: (rng()-0.5)*0.3, r: 60+rng()*120,
})), []);
// per blob: cx = wrap(x0*W + vx*frame, W); draw <Circle> with <LinearGradient> + <Blur blur={40}/>
```
- **True mesh gradient:** Skia `drawPatch` (4 bezier corners + 4 colors) inside a `createPicture`
  command list, animate corner colors on frame. See `react-native-skia` → `offline-rendering.md`
  ("drawPatch mesh gradients"). Show via `picture.makeShader()` if used as a fill.

## 4. Liquid glass / refraction  → `lg`

**Reuse:** `useGlassPicture` from `LiquidGlass.tsx`; copy the wiring from `EngraStage.tsx`.

```tsx
const fieldPicture = useFieldPicture({width, height, frame, fps, /* your backdrop */});
const blurred = useBlurredFieldPicture({field: fieldPicture, width, height, frame, blur: 20});
const glassPicture = useGlassPicture({
  fieldPicture, blurredFieldPicture: blurred, width, height,
  glass: {cx, cy, w, h, radius}, frame, fps, strength, rimColors: [tokens.neonBlue, tokens.neonPink],
});
<SkiaCanvas width={width} height={height}>
  <Picture picture={fieldPicture} />
  <Picture picture={glassPicture} />
</SkiaCanvas>
```

Non-negotiables: compile the SKSL effect once at module scope (it's cached in `LiquidGlass`);
picture-shader, no offscreen surfaces; animate `strength`/position on frame. The glass should
refract the *same* field it sits on.

## 5. Blueprint → filled morph  → `tdm`

**Reuse:** `NeonStroke` for the wireframe; cross-fade to a filled `Path`.

```tsx
const drawn = useDrawProgress(start, 20);            // wireframe draws on
const fill  = interpolate(frame, [start+18, start+34], [0,1], {extrapolateLeft:"clamp", extrapolateRight:"clamp", easing: Easing.bezier(0.16,1,0.3,1)});
<>
  <NeonStroke path={shapePath} progress={drawn} colors={[tokens.neonCoral, tokens.neonBlue]} bounds={b} />
  <Path path={shapePath} style="fill" opacity={fill}>
    <LinearGradient start={vec(b.x,b.y)} end={vec(b.x+b.width,b.y+b.height)} colors={[tokens.neonCoral, tokens.neonBlue]} />
  </Path>
</>
```

Stagger each shape's `start` (e.g. `base + i*8`) for the rhythmic reveal. For a true isometric 3D
cage use R3F `EdgesGeometry` + `<lineSegments>` with glow (never raw `wireframe`) — see
`react-three-fiber` → `design-and-aesthetics.md`.

## 6. Frame-driven 3D point cloud / neon field  → `gzm`

**Reuse:** `VectorCloud3D.tsx` — adapt point count, seed, and the cluster/spin curves.

```tsx
<ThreeCanvas width={W} height={H} gl={{alpha:true, antialias:true}} camera={{position:[0,0,3.5], fov:45}}>
  {/* spin = interpolate(frame,[0,240],[0,Math.PI*1.3], {easing:Easing.bezier(0.16,1,0.3,1), ...clamp}) */}
  {/* <group rotation={[0.35, spin, 0]}> ... one shared SphereGeometry per point ... </group> */}
</ThreeCanvas>
```

Material for neon: `meshBasicMaterial` + `transparent` + `blending={THREE.AdditiveBlending}` +
`depthWrite={false}` + `toneMapped={false}` (no lights). Seed positions with `mulberry32` in
`useMemo`. Vary per-point size + hue for depth.

## 7. Seeded particle field / network bg  → `gzm`

**Reuse:** `FloatingParticles.tsx` (positions + distance-faded connection lines) or `GeoShapes.tsx`.
Adjust count, `linkDistance`, palette. Already frame-driven + seeded — usually just drop it in as a
`<Background>`-level layer and tune.

## 8. Cinematic camera move  → all archetypes

Full vocabulary + theory in `cinematic-camera.md`. The two skeletons:

- **3D (R3F):** a `CameraRig` inside `<ThreeCanvas>` — grab the camera with `useThree`, set it from
  the frame, `updateProjectionMatrix()`. Never `useFrame`/clock.
```tsx
const CameraRig = () => {
  const frame = useCurrentFrame();
  const cam = useThree((s) => s.camera) as THREE.PerspectiveCamera;
  const E = {extrapolateLeft:"clamp", extrapolateRight:"clamp", easing: Easing.bezier(0.16,1,0.3,1)} as const;
  const angle = interpolate(frame, [0,220], [-0.45,0.15], E);  // orbit, settles
  const radius = interpolate(frame, [0,220], [6.5,4.2], E);    // push-in
  cam.position.set(Math.sin(angle)*radius, 0.7, Math.cos(angle)*radius);
  cam.lookAt(0,0,0);
  cam.fov = interpolate(frame, [0,220], [52,40], E); cam.updateProjectionMatrix();
  return null;
};
// <ThreeCanvas ...><CameraRig/>{/* additive neon meshes */}</ThreeCanvas>
```
  Pan/tilt = animate the `lookAt` target; dolly-zoom = move radius & fov opposite ways; handheld =
  add `mulberry32` noise to position/target (never Math.random).
- **2D (Skia/DOM):** move the world group via a frame-driven transform (reuse the math in
  `cameraForFrame()`):
```tsx
const scale = interpolate(frame, [0,200], [1,1.12], {extrapolateLeft:"clamp", extrapolateRight:"clamp", easing: Easing.bezier(0.16,1,0.3,1)});
const tx = (CENTER.x - focus.x) * (scale-1), ty = (CENTER.y - focus.y) * (scale-1);
// Skia: <Group transform={[{translateX:tx},{translateY:ty},{scale}]} origin={vec(focus.x,focus.y)}>
// DOM:  transform: `translate(${tx}px,${ty}px) scale(${scale})` (a frame-computed value, NOT a CSS transition)
```
  Parallax = give each depth layer its own translate rate.

## 9. Scene transition between two beats  → all archetypes

**Reuse the effects library — don't hand-roll a crossfade.** Default to the self-contained
`<SceneTransition>` so the audio-driven `offsets[]` timing is undisturbed (overlap it in the
inter-scene pad); drive it with `transitionProgress(frame, cutAt, dur)`.

```tsx
import { SceneTransition, transitionProgress, crossDissolve } from "../effects";
const p = transitionProgress(frame, cutAt, 15);
<SceneTransition from={<SceneA/>} to={<SceneB/>} progress={p} presentation={crossDissolve()} />
```

DOM presentations: `crossDissolve`/`dipToColor`/`slide`/`push`/`zoomDolly`/`blurDissolve`/`iris`/
`wipe`/`splatterMask`/`pageTurn`. For a **real** page-curl/ripple use the SKSL `<SkiaTransition>`
(`crosswarp`/`displacement`/`noiseDissolve`/`pageCurl`) over `pictureSource`/`imageSource` sources.
For a new `TransitionSeries`-based comp, wrap a presentation with `present()` (note: TransitionSeries
shortens the timeline — wrong for audio-pad comps). Full detail: `references/effects-library.md`.

---

## Composition wiring (whichever recipe you use)

- **Persisting across beats?** Use the `MondayFoundations.tsx` persistent-map pattern: container at
  composition root reads absolute frame; interiors in `<Sequence layout="none">` for local frame.
- **Procedural graphics under text?** Stack like `EngraIntro.tsx`: Skia/R3F stage → DOM overlay →
  audio.
- **Timing:** size the composition from audio via `makeCalcMetadata` (`calculate-metadata.ts`);
  map `sceneDurations` → `offsets[]` → `<Sequence from={offsets[i]}>`. Never hardcode durations.
- **Verify:** `npx remotion still <Comp> out/x.png --frame=N`, eyeball vs the `frame-refs/`
  archetype, then full render + `npm run lint && npm run typecheck`.
