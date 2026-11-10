# Engine selection + real-time→frame-driven translation

This repo renders **offline** (Remotion, 30fps, parallel workers). Every engine here is
frame-driven. This doc helps you (1) pick the right engine per effect and (2) translate the
real-time patterns the technical skills' default docs teach into offline-safe code.

---

## Pick the engine

Decide per *effect*, not per scene — a single scene often stacks engines (e.g. Skia stage under a
DOM overlay).

| You want… | Engine | Mount | Read first |
| --- | --- | --- | --- |
| Neon line-art, charts, diagrams, draw-on strokes, path morphs | **Skia** | `<SkiaCanvas>` from `@remotion/skia` | `react-native-skia` → `references/offline-rendering.md` |
| Glass/refraction, SKSL shaders, mesh gradients, displacement | **Skia (imperative)** | `<SkiaCanvas>` + `Skia.*` / `createPicture` | same |
| 3D depth, point clouds, volumetric fields, rotating neon cages, true perspective | **R3F** | `<ThreeCanvas>` from `@remotion/three` | `react-three-fiber` → `remotion-r3f.md`, then `design-and-aesthetics.md` |
| Text, captions, headings, UI chrome, glass *panels*, layout/flow | **DOM + SVG** | plain JSX + `<svg>` | `remotion-best-practices` → `rules/text-animations.md`, `tokens.ts` |
| Connectors, arrowheads, simple animated paths | **SVG** | `<svg>` + repo `components/svg/*` | `repo-patterns.md` |
| Refraction/procedural behind crisp type | **hybrid stack** | Skia stage (Layer A) + DOM overlay (Layer B) + audio (Layer C) | `EngraIntro.tsx` |

Rules of thumb:
- **Glow that must read as neon** → Skia 4-layer stack (`NeonStroke`), not a CSS shadow.
- **Crisp text** → DOM, never rasterized in Skia/Three. Keep text out of the canvas.
- **Anything volumetric or with real parallax/perspective** → R3F. Faking 3D in 2D rarely hits the bar.
- **Mesh gradients / chromatic refraction** → Skia imperative (`drawPatch` / `makeShaderWithChildren`).
- Don't put `<SkiaCanvas>`/`<ThreeCanvas>` in a zero-size parent — they collapse. Pass explicit
  `width`/`height` (from `useVideoConfig()` or a fixed card size like the 280px monday cards).

---

## Translation cheatsheet (real-time → frame-driven)

The technical skills' marquee examples use a real-time clock. Convert as follows. The constant in
all of these: derive from `const frame = useCurrentFrame()`.

| Real-time pattern (DON'T use here) | Frame-driven replacement (DO) |
| --- | --- |
| `const x = useSharedValue(0)` then animate | `const x = interpolate(frame, [a, b], [from, to], {extrapolateLeft:'clamp', extrapolateRight:'clamp', easing: Easing.bezier(0.16,1,0.3,1)})` |
| `withTiming(to, {duration})` | `interpolate(frame, [start, start + durFrames], [from, to], …)` |
| `withSpring(to)` | Remotion `spring({frame, fps, config})` (from `useVideoConfig()`), or `interpolate` for most cases |
| Reanimated `interpolateColor(...)` | Skia `interpolateColors(t, inputRange, colors)` — **note the `s`**; different color format |
| R3F `useFrame(({clock}) => mesh.rotation.y = clock.elapsedTime)` | `const spin = interpolate(frame, [0, N], [0, Math.PI*2], …)` then `<group rotation={[tilt, spin, 0]}>` |
| `useFrame((_, delta) => ref.current.x += delta)` | bind the prop to a frame-derived value (declarative) — no per-frame mutation loop |
| `THREE.Clock` / `clock.getElapsedTime()` | `frame / fps` (seconds) — but prefer interpolating on `frame` directly |
| `Math.random()` for scatter | `mulberry32(seed)()` computed in `useMemo` (deterministic across workers) |
| `useImage`/`useLoader` + `<Suspense>` | preload at composition level; Remotion can't await Suspense offline |
| CSS `transition` / `@keyframes` / Tailwind `animate-*` | interpolate the style value on `frame` |
| `backdrop-filter` with a runtime shader (CanvasKit) | `picture.makeShader()` fed into the SKSL effect (see `LiquidGlass`) |
| `frameloop="demand"` + `invalidate()` | nothing — frames tick deterministically |

### Determinism + memory (why renders crash otherwise)

- **Seed everything random.** `mulberry32(0x5ec709)` style; compute the layout once in `useMemo`.
  Workers render different frames of the same scene — un-seeded randomness makes particles jump.
- **Skia WASM heap:** never create an offscreen `Surface` or call `readPixels` per frame; build a
  `SkPicture` and draw it, or `picture.makeShader()`. Compile `Skia.RuntimeEffect.Make(SKSL)` once
  at **module scope** (cache it), null-check the result. Imperatively-created CanvasKit objects are
  not GC'd; the picture-based approach sidesteps per-frame allocation. Long renders crash ~frame
  500 if you leak.
- **R3F GPU hygiene:** define geometries/materials once and share by reference; `.clone()` a
  material only if meshes mutate it independently. Use additive `meshBasicMaterial` +
  `toneMapped={false}` for neon (no lights needed).

### SKSL ≠ GLSL

Skia shaders are SKSL, not GLSL — don't paste Shadertoy code. Prototype at
https://shaders.skia.org/ before porting. Details in `react-native-skia` → `references/shaders.md`.

---

## When in doubt

Open the matching `frame-refs/` archetype and ask "what is physically happening to the light here?"
Refraction/bloom/mesh → Skia shader. Real depth/parallax → R3F. Crisp informational content →
DOM/SVG. Then reuse the repo component that already does it (`repo-patterns.md`).
