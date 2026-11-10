# Visual vocabulary — the `frame-refs/` premium look

The bar for this repo is set by four William Candillon–style React Native Skia showcase clips,
extracted to `frame-refs/{charts,gzm,lg,tdm}/frame_*.png`. **Open the actual frames** when you
design — this file is the distilled map, not a substitute for looking. For each archetype: the
motifs, the color/lighting, the motion, the composition, what makes it *premium*, and — the part
that matters here — **how to achieve it in this repo**.

---

## charts — animated gradient line chart (crypto/finance app mockup)

- **Motifs:** an OLED-dark mobile device frame on a light/tan dot-grid; a hero number; a flowing
  warm→cool gradient line chart; a cyan "pill" tab selector; clean list rows with rounded icons.
  Opening uses concentric rings with a glowing center.
- **Color/lighting:** dark navy UI, saturated orange→yellow→cyan waveform, subtle glass bezel
  reflection, muted background — high contrast between the dark UI and the chart's color.
- **Motion:** the line *draws on* left→right with a hue shift; the center ring breathes; the
  device reveals via scale/translate; tab indicator slides; rows slide in staggered.
- **Composition:** centered portrait device, left-aligned label/value hierarchy, dot-grid bleeding
  to the edges.
- **Premium because:** realistic device shadow/perspective, unhurried easing on every state, color
  grading that feels like a shipping iOS app.
- **Achieve it here:** `TimeSeriesCard.tsx` is exactly this — `NeonStroke` for the gradient line
  with `progress` draw-on, `NeonDot` blooming at each data point. Build paths with
  `Skia.Path.MakeFromSVGString`. For the dot-grid use `Background.tsx` (`grid` density). Recipe:
  `recipes.md` → "Gradient line-chart draw-on".

## gzm — mesh-gradient particle blobs ("Introducing Gen-Z Mode")

- **Motifs:** smooth morphing pill/toggle shapes; blurred glowing particle blobs at varied sizes;
  full-screen mesh gradients; portraits under color filters with feathered masks; soft bokeh.
- **Color/lighting:** vibrant neon gradients (hot pink→purple→cyan→yellow), heavy ambient bloom
  around particles, smooth gradient fields shifting warm↔cool per scene.
- **Motion:** geometric shape morphs (circle↔rounded-rect↔complex), particle bloom with velocity
  trails, animated mesh-gradient color field, blur/focus scene transitions.
- **Composition:** full-bleed gradient backgrounds, centered focal element, scattered depth-layered
  particles, breathing whitespace.
- **Premium because:** artifact-free morphing, natural-feeling particle physics, rich multi-stop
  gradient curves, every transition feels intentional.
- **Achieve it here:** mesh gradients via Skia `drawPatch` / `picture.makeShader()`
  (`react-native-skia` → `offline-rendering.md`). Particle/blob fields:
  `FloatingParticles.tsx` / `GeoShapes.tsx` (seeded, frame-driven). Glow = the 4-layer stack or
  additive Skia `Blur`. Recipe: `recipes.md` → "Mesh gradient" and "Seeded particle field".

## lg — Apple liquid-glass refraction ("LiquidGlass")

- **Motifs:** a glass orb/panel with SDF refraction bending what's behind it; a colorful blurred
  bar passing *through* the glass; device frames on a light cyan dot-grid; high-gloss specular
  rim; wavy lines distorted through the lens.
- **Color/lighting:** light cyan→blue dot grid, saturated magenta/purple→orange bars, white glass
  with soft shadow, bloom on the refracted elements.
- **Motion:** rim refraction (offset sample coords by the surface normal), a color bar sliding
  horizontally behind the glass, isometric device reveals, dot-grid parallax.
- **Composition:** centered hero glass, devices placed with perspective at the edges, everything
  aligned to an invisible grid.
- **Premium because:** convincing optics that match iOS glass, realistic shadows, perfect
  anti-aliasing on glass edges.
- **Achieve it here:** `LiquidGlass.tsx` + `EngraStage.tsx` already do this — the REFRACTION SKSL
  effect fed a `picture.makeShader()` of the field (no offscreen surfaces). The hero refracts the
  *same* field picture it sits on. Recipe: `recipes.md` → "Liquid glass". Note web caveat: a
  runtime shader can't be a backdrop filter — use the picture-shader approach.

## tdm — blueprint→filled geometric morphs ("Telegram Dark Mode")

- **Motifs:** 3D isometric box/card shapes as orange/cyan **wireframes** that morph into filled,
  gradient-colored solids; staggered shape sequences (oval→rounded-rect→filled); blueprint grid;
  layered stacked cards with depth.
- **Color/lighting:** light/gray background, isometric wireframe strokes transitioning
  orange→cyan, gradient fills orange→blue, sketch-weight lines, subtle inter-layer shadow.
- **Motion:** path morphing (stroke→fill), 3D rotation/perspective scaling, staggered reveals
  where each shape follows the previous, recursive depth via layered cards.
- **Composition:** centered isometric stack, ~15–20° perspective offset, aligned to a 3D grid.
- **Premium because:** mathematically clean geometry, cubic-bezier-quality curve morphs, staggered
  timing that creates rhythm.
- **Achieve it here:** wireframe stroke via `NeonStroke` with `progress`, then cross-fade to a
  filled `Path` (interpolate the fill opacity); stagger each shape's start frame. For true 3D
  cages use R3F `EdgesGeometry` + `<lineSegments>` (see `react-three-fiber`
  `design-and-aesthetics.md` — never raw `wireframe`). Recipe: `recipes.md` → "Blueprint→filled
  morph".

---

## The 10 shared principles (true across all four)

1. **Gradient sophistication** — multi-stop and/or animated gradients; never flat color.
2. **Motion is intentional** — clear timing/easing on every transform; no linear, no snap.
3. **Geometric precision** — even organic elements obey math (falloff, grid, SDF, seeded scatter).
4. **Depth layering** — explicit z-order via shadow, blur, opacity, scale, or 3D perspective.
5. **Glasslike / refractive language** — glass, bloom, refraction, or soft glow appears in most.
6. **Color grading** — a deliberate per-scene mood that shifts intentionally between beats.
7. **Typography integration** — text scales, animates, and colors to match the theme.
8. **Smooth easing** — cubic-bezier / physics-feel dominates (house ease `0.16, 1, 0.3, 1`).
9. **Subtle micro-interactions** — pulse, glint, parallax reinforce the main beat.
10. **Production finish** — no aliasing/jank/dither; generous margins; restrained on-screen text.

If a draft fails the premium bar, it almost always violates one of these — usually #2 (unearned or
linear motion), #4 (single-plane/flat), or #10 (too much text, too little margin).
