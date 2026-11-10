# Repo reference implementations — reuse, don't reinvent

This repo already implements the signature looks correctly (frame-driven, seeded, picture-based).
Before building any effect, find it here and import/adapt it. Paths are relative to the repo root.
Each entry: **what it is → the technique → when to reuse → which `frame-refs/` archetype it serves.**

> **Effects library (`src/effects/`) — check it first.** A reusable, frame-driven, themeable
> library of entrances, scene transitions (DOM + real SKSL), blur/depth, card surfaces, animated
> backgrounds, and 3D wireframes. The decision map ("which effect, when") is `effects-library.md`;
> full API is `docs/effects.md`. This file (`repo-patterns.md`) catalogs the lower-level building
> blocks those effects are made of.

---

## Skia — neon line-art (REAL Skia, 4-layer glow)

- **`src/components/skia/NeonPath.tsx`** — `NeonStroke` and `NeonDot`, the canonical 4-layer glow.
  - `NeonStroke`: outer halo (`width*7` + `Blur 14`, 0.55α) · mid glow (`width*2.6` + `Blur 3.5`,
    0.9α) · hairline gradient (`width`) · white core (`width*0.55`, 0.85α). `progress` 0→1 trims
    via `<Path end>`; `glow` scales brightness; colors via `<LinearGradient>`.
  - `NeonDot`: blurred halo (`r*2.4` + `Blur 10`, 0.4α) · solid core · white highlight (`r*0.45`).
  - **Reuse for:** any neon line, chart, diagram, draw-on logo, wireframe. Render inside
    `<SkiaCanvas>`; drive `progress` from frame. → `charts`, `tdm`.

- **`src/scenes/services/illustrations/IllustrationPanel.tsx`** — node-network / pipeline / compass
  diagrams built from `NeonStroke`+`NeonDot`, staggered draw-on (dots bloom after the stroke
  finishes). **Reuse for:** category/architecture/flow diagrams. → `tdm`, `charts`.

- **`src/scenes/monday/cards/TimeSeriesCard.tsx`** — the gradient line chart: faint axis draws
  first, then `NeonStroke` line grows left→right, `NeonDot`s bloom (r ramp 3→6→3.5) as the line
  reaches each point. Paths via `Skia.Path.MakeFromSVGString`. **Reuse for:** any metric/trend
  chart. → `charts` (the closest direct match).

## Skia — glass / refraction (REAL Skia, SKSL)

- **`src/components/skia/LiquidGlass.tsx`** — `useGlassPicture(opts) → SkPicture` and the
  REFRACTION SKSL effect. Compiles `Skia.RuntimeEffect.Make` once at module scope
  (`getRefractEffect`, null-checked); feeds `fieldPicture.makeShader()` + a blurred copy into
  `effect.makeShaderWithChildren` — **no offscreen surfaces, no readPixels.** Stacks refracting
  body · milky tint · specular rim. Falls back to frosted blur if compilation fails. All knobs
  (strength, ior, dispersion, specular, frost, rimColors) are frame-derived. **Reuse for:** any
  glass panel, lens, refractive hero. → `lg`.

- **`src/scenes/engra/EngraStage.tsx`** — how to *use* the glass: a persistent Skia stage (Layer A,
  no Sequence, reads absolute frame) records the brand field as a `Picture`, then records the hero
  glass refracting that *same* field as a second `Picture`. Shows the picture-based,
  heap-bounded pattern for a 60s render. **Reuse for:** a procedural backdrop that a glass element
  refracts; long continuous-evolution stages. → `lg`, `gzm`.

## R3F — frame-driven 3D

- **`src/scenes/monday/cards/VectorCloud3D.tsx`** — the project's reference `<ThreeCanvas>`. 44-pt
  cloud, `mulberry32` seed, spin/cluster/bloom all from `interpolate(useCurrentFrame())` (never
  `useFrame`). Additive `meshBasicMaterial` + `toneMapped={false}` + `AdditiveBlending` +
  `depthWrite={false}` for neon with no lights; one shared `SphereGeometry`. **Reuse for:** point
  clouds, constellations, similarity/embedding viz, volumetric neon fields. → `gzm`.

## Backgrounds — seeded particle / geometry fields

- **`src/components/bg/FloatingParticles.tsx`** — 56 particles, seeded base + velocity, position
  `= wrap(x0 + vx*frame, W)`, connection lines fade past a distance threshold. **Reuse for:**
  organic particle bg, network topology, data-flow. → `gzm`.
- **`src/components/bg/GeoShapes.tsx`** — tesseract cubes + radial pulse rings, spin on `frame %
  period`, sinusoidal breathe. **Reuse for:** abstract geometric motion bg. → `gzm`, `tdm`.
- **`src/components/bg/FloatingCubes.tsx`** — 3D floating geometry, deterministic frame positioning.
- **`src/components/Background.tsx`** — pillar-tinted backdrop with `grid` / `gridArc` / `vignette`
  / `full` density. **Reuse for:** the dot-grid / vignette base under any scene. → `charts`, `lg`.

## Composition / architecture patterns

- **`src/compositions/MondayFoundations.tsx`** — the **persistent-map** pattern: a `<DatabaseMap>`
  at the composition root (no Sequence) reads the **absolute** `useCurrentFrame()` + `offsets[]`,
  while each card interior animates on its **local** frame inside `<Sequence from={activation}
  layout="none">`. **Reuse for:** any visual that must persist and evolve across multiple beats
  (growing map, accumulating elements, a backdrop that morphs through the whole piece).
- **`src/compositions/EngraIntro.tsx`** — 3-layer stack: Skia stage (Layer A) + DOM overlay
  (Layer B, per-beat `<Sequence>`, local frame) + audio (Layer C, gated on `audioReady`). **Reuse
  for:** procedural graphics behind crisp captions/UI.
- **`src/lib/calculate-metadata.ts`** — `makeCalcMetadata(beatIds, kind)`: reads each beat's MP3
  duration (`getAudioDuration` via mediabunny), seconds→frames (`Math.ceil(s*30)`), adds an
  inter-scene pad, returns `durationInFrames` + `sceneDurations[]`. Upwork calcs fall back to a
  fixed per-beat duration + `audioReady[i]=false` so Studio previews before VO exists. **Audio is
  the source of truth — never hardcode durations.** A composition maps `sceneDurations` → cumulative
  `offsets[]` → per-beat `<Sequence from={offsets[i]}>`.

## Helpers / utilities

- **`src/components/svg/`** — `AnimatedPath`, `Connector`, `Arrowhead`, and `useDrawProgress(start,
  dur)` (frame-driven 0→1 used by `TimeSeriesCard`). **Reuse for:** connectors, flow arrows, SVG
  draw-on.
- **`src/scenes/scribe/draw-helpers.ts`** — `cameraForFrame`, `dotAtFrame`, `segmentProgress`,
  `segmentBloom`, `cutFlash` (macro cuts + draw-on for the NeonScribe stage).
- **`src/components/CaptionBand.tsx`**, **`PillarPill.tsx`** — caption rendering + pillar chrome.

## Theme / tokens

- **`src/theme/tokens.ts`** — palette `neonBlue #33aaff` / `neonPurple #aa66ff` / `neonPink
  #ff66aa` / `neonCoral #ff8a5b`; `gradient.{text,hero,diag,mark,coral}`; `type` scale (1080p
  baseline); `motion` frame presets (`enterFrames*`, `glassEnterFrames 15`, `floatLoopFrames 180`,
  `heroFloatLoopFrames 90`, `gradientShiftFrames 240`); `ease.{out:[0.16,1,0.3,1], inOut, outQuint}`;
  `glassCardStyle` / `glassEnhancedStyle` (DOM glass panels). **Always pull color/gradient/ease/
  timing from here** — don't hardcode hexes or beziers.
- **`src/theme/fonts.ts`** — Bricolage Grotesque (display+body) + JetBrains Mono (code+caps labels).
- **`src/scripts/*`** — beat scripts are the content source of truth (`week1-scripts.ts`,
  `services-intro.ts`, `chatbot-intro.ts`, `agent-intro.ts`, `fullstack-mvp.ts`, `engra-intro.ts`).
  Edit copy/timing here, not in the scene.

---

## ⚠️ Fakes — do NOT cite as Skia exemplars

These under `src/components/skia/` are CSS/SVG drop-shadow fakes, not real Skia. Fine as cheap
light-up effects; wrong as references for "how to do real Skia glow":

- `NeonCardEdge.tsx` — drop-shadow stack imitating the 4-layer glow (card light-up).
- `NeonMonogram.tsx` — SVG + drop-shadow gradient monogram with sinusoidal float.
- `NeonOrbitalArc.tsx` — SVG arc with stacked stroke filters, dash-offset drift.

For real Skia glow, use `NeonPath.tsx`.
