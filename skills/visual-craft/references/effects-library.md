# Effects library — `src/effects/` (reach for this first)

The repo has a reusable, **frame-driven** effects library. Before hand-rolling a fade, a
transition, a 3D object, or a procedural background, **reach for `src/effects/`** — that's the
duplication this library exists to end. Everything here is a pure function of `useCurrentFrame()`,
exposed as **both components and hooks**, and **themeable**: every effect takes an optional
`colors` palette that defaults to `NEON_PALETTE`, so one effect re-themes per composition by
passing a different array.

This file is the **decision map** — *which effect, when*. The full API (props, signatures,
copy-paste snippets) is the human catalog at **`docs/effects.md`** (the source of truth — don't
duplicate signatures here, they'll drift). Barrel: **`src/effects/index.ts`**. Visual test harness:
the **`EffectsLab`** composition (`src/compositions/EffectsLab.tsx`). Paths are repo-root-relative.

## Pick by need

| You need… | Reach for | Family |
| --- | --- | --- |
| Text/title entrance (fade, rise, scale, blur, 3D rotate) | `useEnter` · `<FadeIn> <RiseIn> <ScaleIn> <BlurIn> <RotateIn>` | `text/` |
| Typed-on text, word-by-word reveal, swap two strings | `<Typewriter>` · `<WordStagger>` · `<CrossDissolveText>` | `text/` |
| Focus pull / depth-of-field / z-dolly / parallax | `useBlurIn` · `useDepth`/`<DepthLayer>` · `<ParallaxLayer>` · `<SkiaBlurLayer>` | `motion/` |
| Cut between two scenes/beats | `<SceneTransition>` + `transitionProgress` (DOM) **or** `<SkiaTransition>` (shader) | `transitions/` |
| Frosted card deck / 3D tilt card | `<FrostedCardStack>` · `<TiltCard>`/`useTilt` | `cards/` |
| Animated full-field background | `<AnimatedGradient>` (DOM) · `<SdfFlow>` (Skia SDF rings/stripes) | `backgrounds/` |
| Rotating 3D wireframe (neon) | `<Wireframe3D>` (+ `rotate3D`/`project`, shapes cube/tetra/octa) | `dimensional/` |

## Transitions — two models + real shaders

- **`<SceneTransition from to progress presentation>`** is the default for **this repo's existing
  comps**: it's self-contained and meant to overlap inside the inter-scene pad, so it does **not**
  disturb the audio-driven additive `offsets[]` math. Drive `progress` with `transitionProgress`.
  DOM presentations: `crossDissolve`, `dipToColor`, `slide`, `push`, `zoomDolly`, `blurDissolve`,
  `iris`, `wipe`, `splatterMask`, `pageTurn`.
- **`present(presentation)`** adapts the same presentations to `@remotion/transitions`
  `TransitionSeries` — for **new** TransitionSeries-based comps only. Caveat: TransitionSeries
  **shortens** total duration, incompatible with the audio-pad timing model.
- **`<SkiaTransition kind from to progress>`** is the **real SKSL** shader path (`crosswarp`,
  `displacement`, `noiseDissolve`, `pageCurl`) over content-agnostic **sources**
  (`pictureSource`/`imageSource`/`colorSource`). Use for a true page-curl/ripple, not the CSS
  `pageTurn` fake. Shader-over-DOM isn't viable offline (needs flag-gated `<HtmlInCanvas>`), so feed
  it Skia pictures or images.

## Offline gotchas callers must respect

These are the rules that make an effect render correctly offline — the value this skill adds over
the plain API doc:

- **Frame-driven only.** Every value derives from `useCurrentFrame()`. No CSS transitions/animations,
  Reanimated, clocks, `Date.now()`, or `Math.random()` at render time.
- **SKSL effects** are compiled **once at module scope** and null-checked with a graceful fallback
  (see `SdfFlow`, `SkiaTransition`). Never compile per frame.
- **Per-frame Skia pictures** are disposed with `del()` (`src/lib/skia-dispose.ts`), or the WASM
  heap climbs until it crashes (~frame 500). Prefer **declarative** Skia (`<Points>`, `<Fill>` +
  `<Shader>`, `<Group layer>`) — nothing imperative per frame to leak (that's why `Wireframe3D` uses
  `<Points mode="lines">` and `SkiaBlurLayer` uses a declarative `<Paint>`).
- **Backdrop blur:** DOM `backdrop-filter` renders offline in Chromium (used by `FrostedCardStack`),
  but a Skia/CanvasKit **runtime-shader** backdrop does **not** — sample a picture instead.
- **Randomness** is seeded with `mulberry32` (`src/lib/prng.ts`) so every render worker agrees.

## Theming

Pass a `colors` palette to re-theme any effect (defaults to `NEON_PALETTE`). Color helpers live in
`src/effects/shared.ts`: `mixHex`, `samplePalette` (smooth palette cycling), `hexToRgb01` (for
SKSL uniforms), plus the eased `frameRange()` and the `Presentation` contract.

## Extending the library (ongoing enhancements)

When adding a new effect so it stays discoverable and consistent:

1. Add it under `src/effects/<family>/` (or a new family folder); keep it frame-driven + themeable
   (`colors` prop) and obey the offline gotchas above.
2. Export it from that family's `index.ts` (it flows through the barrel `src/effects/index.ts`).
3. Add a demo section to `src/compositions/EffectsLab.tsx` so it's visually verifiable.
4. Add an entry to `docs/effects.md` (the full-API source of truth).
5. Add a one-line pointer to the "Pick by need" table above.

## Credits

The card/background/3D batch is adapted (mobile → offline frame-driven) from:
enzomanuelmangano `blur-cards` (`FrostedCardStack`), `animated-gradient` (`AnimatedGradient`),
`animated-3d-card` (`TiltCard`); William Candillon's "Line SDF" gist (`SdfFlow`); friyiajr
`Projection3D` (`Wireframe3D`). Shader transitions port from the gl-transitions catalog (GLSL→SKSL).
