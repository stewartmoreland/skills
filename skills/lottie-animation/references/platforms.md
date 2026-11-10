# Cross-platform Lottie Support

Lottie is implemented by four major rendering libraries plus a few smaller ones. They don't have feature parity. This file documents what's safe and what to flag inline when delivering animations.

## The renderers

| Renderer | Platform | Implementation | Notes |
|---|---|---|---|
| lottie-web | Web (browsers) | SVG/Canvas/HTML | Reference implementation, **most feature-complete**. |
| lottie-ios | iOS, macOS | CoreAnimation/Metal | Maintained by Airbnb; good fidelity, missing some web-only features. |
| lottie-android | Android | Native Canvas | Maintained by Airbnb; some performance shortcuts skip features. |
| lottie-react-native | React Native | Wraps iOS + Android natively | Inherits caveats of both underlying platforms. |
| rlottie / Samsung | Tizen, embedded | Native C++ | Used in messaging stickers, Telegram, etc. Very fast, drops some features. |
| Skottie | Skia-based | Skia renderer | Used by Chrome internals, Flutter. Solid fidelity. |

When the user says "Lottie animation" without specifying a target, assume **lottie-web** (most common case for web/marketing). When they mention React Native, iOS, or Android, plan around those constraints.

## Feature support matrix

✅ = supported well, ⚠️ = partial / version-dependent, ❌ = unsupported (silent failure or fallback)

| Feature | web | iOS | Android | RN | Notes |
|---|---|---|---|---|---|
| Shape layers (`ty: 4`) | ✅ | ✅ | ✅ | ✅ | Universal. |
| Solid layers (`ty: 1`) | ✅ | ✅ | ✅ | ✅ | Universal. |
| Image layers (`ty: 2`) | ✅ | ✅ | ✅ | ✅ | Asset paths must resolve. |
| Null layers (`ty: 3`) | ✅ | ✅ | ✅ | ✅ | Used for parenting. |
| Text layers (`ty: 5`) | ✅ | ⚠️ | ❌ | ⚠️ | Android Lottie has very limited text. Convert text to shape paths for cross-platform. |
| Precomp layers (`ty: 0`) | ✅ | ✅ | ✅ | ✅ | Universal. |
| Ellipse / Rectangle / Star | ✅ | ✅ | ✅ | ✅ | Universal. |
| Custom paths (`sh`) | ✅ | ✅ | ✅ | ✅ | Universal. |
| Path morphing (animated `sh`) | ✅ | ✅ | ✅ | ✅ | Requires matching vertex counts. |
| Fill (`fl`) | ✅ | ✅ | ✅ | ✅ | Universal. |
| Stroke (`st`) | ✅ | ✅ | ✅ | ✅ | Universal. |
| Gradient fill (`gf`) | ✅ | ✅ | ✅ | ✅ | Universal. |
| Gradient stroke (`gs`) | ✅ | ✅ | ⚠️ | ✅ | Android: works in 3.4+, older versions skip. |
| Trim path (`tm`) | ✅ | ✅ | ✅ | ✅ | Universal. The "draw-on" workhorse. |
| Repeater (`rp`) | ✅ | ✅ | ⚠️ | ✅ | Android: limited transform animations on repeated copies. |
| Round corners (`rd`) | ✅ | ✅ | ✅ | ✅ | Universal. |
| Merge paths (`mm`) | ✅ | ✅ | ❌ | ⚠️ | Android doesn't support; RN inherits. Avoid for cross-platform. |
| Masks (basic) | ✅ | ✅ | ✅ | ✅ | Universal. |
| Mask modes (add, subtract, intersect) | ✅ | ✅ | ✅ | ✅ | Universal. |
| Mattes (alpha, luma) | ✅ | ✅ | ⚠️ | ⚠️ | Alpha mattes work everywhere; luma mattes are spotty on Android. |
| Drop shadow effect | ✅ | ✅ | ⚠️ | ⚠️ | Android: requires Lottie 6.0+. |
| Blur effect | ✅ | ✅ | ❌ | ⚠️ | Use static rasterized blur on Android instead. |
| Layer blend modes | ✅ | ⚠️ | ⚠️ | ⚠️ | Multiply / screen work everywhere; others vary. Test on target. |
| Auto-orient on path | ✅ | ✅ | ⚠️ | ✅ | Android: limited to simple paths. |
| Expressions (JavaScript) | ✅ | ❌ | ❌ | ❌ | Web-only. **Never use expressions for cross-platform.** |
| Text animators | ✅ | ⚠️ | ❌ | ⚠️ | Convert to shape paths for cross-platform. |
| 3D layers (`ddd: 1`) | ⚠️ | ⚠️ | ⚠️ | ⚠️ | Lottie's 3D is faked (Z transforms applied flat). Avoid relying on Z motion. |

## Decision rules

### Default to safe features

For any animation that might run cross-platform, stick to:
- Shape layers with paths, ellipses, rectangles, stars
- Fill and stroke (solid or gradient)
- Trim paths for draw-on effects
- Repeaters for radial / particle patterns
- Standard transform animations (position, scale, rotation, opacity, anchor)
- Path morphing with matching vertex counts
- Easing tangents (universally supported)

This set covers ~95% of real-world Lottie use cases and renders identically everywhere.

### Flag inline when you use risky features

If the animation uses something with ⚠️ or ❌ support and the user hasn't specified a single-platform target, mention it in your response:

> *Note: this animation uses merge paths (boolean ops on shapes), which isn't supported on Android. If you need Android support, I can rebuild using pre-merged shape paths — let me know.*

### When the user says "web only"

Use the full feature set without caveats. Expressions, all blend modes, complex mattes, drop shadows — all fair game.

### When the user says "React Native"

Use the iOS + Android intersection. No merge paths, no expressions, simple blend modes (multiply, screen), no luma mattes. Convert any text to shape paths.

### When the user says "iOS only"

Most things work except expressions. Free reign for shape work.

### When the user says "Android only"

Avoid: merge paths, blur, complex blend modes, luma mattes, complex auto-orient. Drop shadow requires Lottie 6.0+ runtime.

## Common cross-platform fixes

### Text → shape paths

After Effects text animators rarely render correctly on Android. The fix: convert text layers to shape layers with the letterforms as `sh` (path) data. Most exporter tools (LottieFiles, Bodymovin export with "Glyphs" enabled) do this automatically.

### Merge paths → pre-merged path

If a design uses merge paths to combine shapes (e.g., a heart made from two circles + a triangle merged), pre-merge them in the source vector tool and export as a single path.

### Drop shadow → baked-in shadow

For Android < 6.0, replace drop shadow effects with a static blurred dark shape positioned behind the element. Animates with the element via parenting.

### Expressions → baked keyframes

Convert any expression-driven property to explicit keyframes. After Effects can do this via "Keyframe Assistant > Convert Expression to Keyframes".

### Luma mattes → alpha mattes

If a luma matte is just being used as a clipping mask (most common case), convert to alpha matte. Set the matte layer's alpha to match what was the luma value.

## File size and performance

Beyond feature support, performance varies by renderer. A few rules of thumb:

- **lottie-web (SVG renderer)**: best for ≤50 layers. Pure shape work scales well. Image-heavy animations slow down.
- **lottie-web (Canvas renderer)**: better for many layers but worse for crisp shapes at scale. Use for animations >50 layers.
- **lottie-ios / lottie-android**: native, fast. Can handle hundreds of layers if needed.
- **rlottie**: extremely fast but feature-limited. Targeted at stickers (small canvases, simple animations).

If file size is a concern (animations served over the wire to mobile):
- Round all numeric values to 2–3 decimal places. Most exporters output 6+ decimals.
- Remove unused properties (older Bodymovin versions include `mn` / `mn`-style metadata that's not used at runtime).
- Use the dotLottie format (`.lottie`) for production — zip-compressed bundle, often 5–10× smaller than raw JSON.

## Testing across platforms

If cross-platform fidelity matters, the user should test the output on each target. Free tools:

- **LottieFiles preview**: web-based, uses lottie-web. https://lottiefiles.com/preview
- **Lottie iOS sample app**: from the lottie-ios repo, drag-drop a JSON file.
- **Lottie Android sample app**: from the lottie-android repo.
- **dotLottie player**: cross-renderer testing via https://dotlottie.io/

When you deliver an animation that uses any ⚠️ or ❌ features, recommend the user test on their target before shipping.

## The dotLottie player family

dotLottie packages (`.lottie` archives) need a dotLottie-aware player. The original `lottie-web`/`lottie-ios`/`lottie-android` libraries can render the embedded animation JSON if you extract it first, but the manifest, themes, and state machines require a v2.0-capable player to take effect.

| Player                  | Platform       | Animations | Themes | State Machines | Notes |
|-------------------------|----------------|------------|--------|----------------|-------|
| dotlottie-web           | Browser (vanilla JS, web component) | ✅ | ✅ | ✅ | Reference v2.0 implementation. |
| dotlottie-react         | React          | ✅ | ✅ | ✅ | Hooks-based API: `useDotLottie`, `useStateMachine`. |
| dotlottie-react-native  | React Native   | ✅ | ✅ | ✅ | Wraps the native iOS/Android players. |
| dotlottie-ios           | iOS, macOS     | ✅ | ✅ | ✅ | Swift package. |
| dotlottie-android       | Android        | ✅ | ✅ | ✅ | Kotlin / Jetpack Compose. |
| Legacy lottie-* players | All            | ⚠️ extract only | ❌ | ❌ | Can render `a/<id>.json` if you unpack, but ignore everything else. |

Player feature pages: https://dotlottie.io/tools/

**Practical implication.** If a project still ships the legacy `lottie-web` (very common in older codebases), a `.lottie` won't load — you either upgrade to `dotlottie-web` or extract the inner JSON. The packager's `--check-only` mode catches problems before delivery, but it can't switch out the player. Confirm the target player supports v2.0 before promising themes or state machines.

**State machine renderer caveats.** Even on supported players, a few features are renderer-dependent:

- Expressions in theme rules: web/iOS/Android players support the standard `$bm_rt` expression model, but advanced functions vary. Stick to `Math.*`, `linear`, `clamp`, `ease` for portability.
- `mode: "Bounce"`: supported across the family, but loop counting in bounce mode counts the full round trip as one iteration — make sure `loopCount` is set accordingly.
- `Tweened` transitions: every player supports the format, but the visual quality of the crossfade varies. For animations where the in/out look needs to match exactly, prefer the same source animation on both sides of the tween or use `SetFrame` actions instead.
- Layer-scoped interactions (`layerName`): rely on the animation's `nm` field exactly matching. If the animation is regenerated by a tool that sanitizes layer names, the interaction silently stops triggering.

