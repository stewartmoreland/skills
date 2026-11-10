---
name: visual-craft
description: >-
  Art-director / visual-execution layer for THIS Remotion video repo — turns a brief into a
  premium, frame-driven scene. Use whenever designing, building, critiquing, or elevating the
  LOOK of a scene, composition, or effect: "make this more engaging / less flat / less cheap",
  "design a scene for X", "build the cover / hero / end-card", "add a chart / glass / particle
  / 3D / neon / mesh-gradient visual", "match the reference clips", "give it more polish".
  Counterpart to `story-craft` (that = what to say & why; this = how it looks &
  how to build it). Composes the technical skills — `react-native-skia`, `react-three-fiber`,
  `motion`, `remotion-best-practices` — but enforces the law their default docs violate: in
  this offline render every animated value is a pure function of `useCurrentFrame()`, never
  Reanimated/CSS/clock. Reach for it even when an engine is named but the real ask is "look
  better", and for critique. Prefer it over improvising — this repo's aesthetic and
  reusable components are easy to get wrong.
---

# Visual Craft

The **creative content director** for this Remotion repo. `story-craft` decides *what the piece
says and why*; the technical skills know *how to render a given effect*. Neither one (a) turns a
brief into the repo's specific **premium look**, (b) chooses the right rendering engine per
effect, (c) translates the technical skills' real-time doc patterns into this repo's **offline,
frame-driven** reality, or (d) points you at the components that already exist. That bridge is
this skill's whole job.

The bar is set by `frame-refs/` — four William Candillon–style React Native Skia showcases:
`charts` (animated gradient line charts on a dot-grid), `gzm` (mesh-gradient particle blobs),
`lg` (Apple liquid-glass refraction), `tdm` (blueprint→filled geometric morphs). Open frames
from `frame-refs/{charts,gzm,lg,tdm}/frame_*.png` whenever you need to *see* the target.

---

## 1. How this skill uses the others

You are the director. Pull in the specialists by **invoking them by name with the Skill tool**
(don't read their files by path — `react-three-fiber` is user-global, the rest are in-repo):

| Need | Invoke | Then read (the offline-safe doc) |
| --- | --- | --- |
| Brief, narrative, beats, hook, critique | `story-craft` | its `assets/templates/` (creative-brief, beat-sheet) |
| 2D graphics: line-art, charts, glass, shaders, mesh gradients | `react-native-skia` | **`references/offline-rendering.md` first** — the imperative `Skia.*` / picture API |
| 3D: depth, point clouds, volumetric, neon cages | `react-three-fiber` | **`remotion-r3f.md` first**, then `design-and-aesthetics.md` |
| Motion feel, easing, choreography, stagger | `motion` | (principles only — its Reanimated/CSS APIs do NOT apply here) |
| Remotion mechanics: sequencing, timing, assets, audio | `remotion-best-practices` | its `rules/3d.md`, `rules/timing.md`, `rules/calculate-metadata.md` |

The technical skills' headline examples assume a real-time runtime (Reanimated `useSharedValue`,
R3F `useFrame`, CSS transitions). **Those render frozen or jittery offline.** Always route through
their offline reference doc, and apply §2.

---

## 2. The one law — frame-driven

**Every animated value is a pure function of `useCurrentFrame()`**, via `interpolate()` /
`spring({fps, frame})`. This is non-negotiable because Remotion renders frames out of order in
parallel workers — there is no wall clock.

FORBIDDEN (they don't render offline): CSS transitions/animations, Tailwind animation classes,
Reanimated `useSharedValue`/`withTiming`/`useClock`, R3F `useFrame`/`THREE.Clock`, `Date.now()`,
`requestAnimationFrame`, `Math.random()` at render time.

House rules:
- House easing `Easing.bezier(0.16, 1, 0.3, 1)` (it's `ease.out` in `src/theme/tokens.ts`); clamp
  both extrapolations so animations settle and hold.
- Any "random" look (particles, point clouds, scatter) uses a **seeded PRNG** (`mulberry32`) so all
  workers produce the identical frame.
- Skia/WASM memory: render via **`SkPicture` / `picture.makeShader()`, never per-frame offscreen
  surfaces or `readPixels`**, and compile `Skia.RuntimeEffect.Make` once at module scope — otherwise
  the heap climbs until a crash (~frame 500) on long renders.
- 30fps. Timing comes from audio, not hardcoded — see §6 / `calculate-metadata.ts`.

The full real-time→frame-driven translation table is in `references/engine-selection.md`.

---

## 3. The director's workflow

Work the spine in order. Skipping to "what should it look like" before the goal is the #1 way
scenes come out flat.

1. **Brief** — invoke `story-craft`. Pin the objective, audience, the three time scales
   (macro-arc / scene beats / per-frame focal point), and the hook (brand/value in the first ~3s).
   Confirm it works muted. *Don't choose a look yet.*
2. **Visual concept + shot** — translate the brief into a look using the vocabulary in §4 /
   `references/visual-vocabulary.md`. For each beat name the **single focal point**, decide
   whether motion is *earned* (does it externalize a change you can't read from a still? if not,
   hold the frame), and choose the **one camera move** for the beat (§5b) and how it's framed.
   Pick the matching `frame-refs/` archetype as your reference.
3. **Engine selection** — for each effect choose Skia / R3F / DOM+SVG (§5). When unsure, read
   `references/engine-selection.md`.
4. **Frame-driven build** — read the chosen engine's offline doc (§1), reuse a repo component
   (§6 / `references/repo-patterns.md`) instead of reinventing, build the camera as a rig (3D) or
   stage transform (2D) per §5b, and obey §2. Concrete skeletons for the signature looks are in
   `references/recipes.md`.
5. **Polish & review** — run the §7 premium bar + `story-craft`'s self-check, then *prove it
   visually*: render stills at key frames, then a full render.

---

## 4. Premium visual vocabulary (the shared language of `frame-refs/`)

What separates these clips from a default template — apply deliberately, don't sprinkle:

- **Gradients, never flat fills.** Multi-stop, and often animated (hue drift over
  `gradientShiftFrames`). Use `gradient.*` / the neon palette in `tokens.ts`.
- **4-layer glow.** outer halo (wide + heavy blur) · mid glow · hairline color · white core.
  This is `NeonStroke`/`NeonDot`. It's what makes line-art read as "neon" not "a stroke".
- **Glass / refraction / bloom.** Curved-rim refraction, milky tint, specular rim; additive
  bloom on bright elements. → `LiquidGlass` / `EngraStage`.
- **Depth layering.** Manufacture z-order with shadow, blur, opacity falloff, scale, and 3D
  perspective. Nothing premium is single-plane.
- **Geometric precision.** Even "organic" things (blobs, particles) obey math — circular
  falloff, grids, SDF, seeded scatter.
- **Scene-level color grading.** Each beat has a deliberate mood (warm↔cool, saturated↔muted)
  that shifts intentionally between beats.
- **Intentional easing + micro-interactions.** No linear moves; add a pulse / parallax / glint
  that reinforces (not distracts from) the focal point.
- **Broadcast finish.** Anti-aliased, no jank, generous margins, restrained on-screen text.

The per-archetype breakdown (motifs, color, motion, *and how to achieve each here*) is in
`references/visual-vocabulary.md`.

---

## 5. Engine selection (quick matrix)

| Effect | Engine | Why |
| --- | --- | --- |
| Neon line-art, charts, diagrams, draw-on strokes | **Skia** (`<SkiaCanvas>`) | precise paths + the 4-layer glow + `end` trim |
| Glass, refraction, shaders, mesh gradients | **Skia** imperative (`offline-rendering.md`) | SKSL + `picture.makeShader()` |
| 3D depth, point clouds, volumetric, rotating cages | **R3F** `<ThreeCanvas>` from `@remotion/three` | real perspective; additive neon |
| Text, captions, UI chrome, glass *panels*, layout | **DOM + SVG** | crisp type; cheap; `glassCardStyle` |
| Refraction behind crisp text | **hybrid stack** | Skia stage (Layer A) + DOM overlay (Layer B) — see `EngraIntro` |

Detail + the real-time→frame-driven translation cheatsheet: `references/engine-selection.md`.

## 5b. Camera & cinematography

A static, dead-center frame is the #1 thing that makes a scene read as "a slide". The cheapest
upgrade to production value is a **motivated, eased camera move** — so treat the camera as a
first-class creative decision, not an afterthought. Choose **one dominant move per beat** from its
intent:

| Move | For |
| --- | --- |
| Push-in / pull-out (dolly) | build intensity / reveal context — the default "make a static frame alive" move |
| Pan / tilt | scan a space, connect or reveal focal points |
| Orbit (arc) | prove an object is 3D; hero reveal |
| Zoom (FOV) / dolly-zoom | emphasis without moving / a dramatic "whoa" beat (rare) |
| Rack focus (DoF), roll/Dutch, handheld, parallax | attention hand-off / tension / organic energy / 2D depth |

Rules: every move is **motivated** (reveal/follow/emphasize/transition — else hold); **eased and
settled** (house bezier, clamp, come to rest — no endless drift except an intentional ultra-slow
push); **one dominant move per beat**; it only pays off when there's **depth** to reveal; and the
final framing still lands the focal point.

Frame-driven, always: **3D** — grab the camera with `useThree` inside `<ThreeCanvas>`, set
`position`/`lookAt`/`fov` from `useCurrentFrame()` and call `updateProjectionMatrix()`; never
`useFrame`/clock. **2D** — there is no camera; move the *world*: a frame-driven
`[{translateX},{translateY},{scale}]` (+`origin`/rotate) transform on the stage group (the repo's
`cameraForFrame()` in `src/scenes/scribe/draw-helpers.ts` is the exemplar; parallax = per-layer
translate rates). If the camera must persist across beats, drive it off the **absolute** frame
(persistent-stage pattern). Full move vocabulary, the R3F `CameraRig` skeleton, dolly-zoom,
handheld, and fake-DoF: **`references/cinematic-camera.md`**.

---

## 6. Reuse what exists (highest-value targets)

Don't rebuild these — import them. Full catalog + when-to-reuse + the CSS/SVG-fake caveats in
`references/repo-patterns.md`.

- **`src/effects/` — the reusable effects library; reach for it FIRST** for any entrance, scene
  transition, blur/depth, card surface, animated background, or 3D wireframe. Frame-driven +
  themeable (a `colors` palette). Decision map: `references/effects-library.md`; full API:
  `docs/effects.md`. Covers `useEnter`/`FadeIn`/`Typewriter`, `useDepth`/`ParallaxLayer`,
  `SceneTransition`/`SkiaTransition`, `FrostedCardStack`/`TiltCard`, `AnimatedGradient`/`SdfFlow`,
  `Wireframe3D`.
- `src/components/skia/NeonPath.tsx` — **real** 4-layer neon glow: `NeonStroke` / `NeonDot`.
- `src/components/skia/LiquidGlass.tsx` + `src/scenes/engra/EngraStage.tsx` — SKSL refraction,
  picture-based, module-cached effect (the `lg` archetype).
- `src/scenes/monday/cards/VectorCloud3D.tsx` — frame-driven `<ThreeCanvas>`, additive
  `meshBasicMaterial` + `toneMapped={false}`, `mulberry32`.
- `src/scenes/monday/cards/TimeSeriesCard.tsx` — gradient line-chart draw-on (the `charts`
  archetype), data points bloom as the line reaches them.
- `src/components/bg/{FloatingParticles,GeoShapes,FloatingCubes}.tsx` — seeded particle /
  geometry fields (the `gzm` archetype).
- `src/scenes/services/illustrations/IllustrationPanel.tsx` — neon line-art diagrams.
- `src/compositions/MondayFoundations.tsx` — **persistent-map** pattern: global-frame container
  (no Sequence) + local-frame interiors via `<Sequence layout="none">`. Use for any visual that
  must persist and evolve across beats.
- `src/lib/calculate-metadata.ts` — `makeCalcMetadata`: audio length is the source of truth for
  timing. Never hardcode beat durations.
- `src/theme/tokens.ts` / `src/theme/fonts.ts` — neon palette, `gradient.*`, `ease.*`, `motion.*`
  frame presets, `glassCardStyle`; Bricolage Grotesque + JetBrains Mono.

Caveat: `NeonCardEdge` / `NeonMonogram` / `NeonOrbitalArc` under `skia/` are CSS/SVG **fakes**,
not real Skia — fine as cheap light-up effects, but don't cite them as Skia exemplars.

---

## 7. The premium bar (review before claiming done)

Score the scene against the look it's emulating, not against "it renders":

- [ ] Focal point unmistakable each beat; eye lands where intended in <0.5s.
- [ ] Gradients (not flat), and the signature glow/glass/bloom is present where the archetype calls for it.
- [ ] Real depth (≥2 of: shadow, blur, opacity falloff, scale, 3D).
- [ ] Every motion is earned and uses house easing; nothing linear; settles and holds.
- [ ] Camera move (if any) is motivated, eased, settles, frame-driven, and ends on the focal point — one dominant move per beat (§5b).
- [ ] Reuses repo components/tokens; no reinvented neon/glass/PRNG.
- [ ] Strictly frame-driven (§2); seeded randomness; picture-based Skia.
- [ ] Reads at the `frame-refs/` polish level — compare side by side.
- [ ] Works muted; on-screen text restrained over busy frames.

Then verify (output is gitignored under `out/`):

```bash
npx remotion still <CompositionId> out/check.png --frame=N   # N is 0-based; 30fps → frame 30 = 1s
npx remotion render <CompositionId> out/check.mp4
npm run lint && npm run typecheck
```

Open the still and judge it against the matching `frame-refs/` frame. If it doesn't reach the
bar, return to §2 — usually the fix is concept/restraint, not more effects.
