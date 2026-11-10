# Charts with React Native Skia

Line charts, sparklines, price/stock/crypto graphs, scrubbable cursors, range switchers
(1H / 1D / 1W / 1Y), area fills, and animated transitions between datasets.

Distilled from three sources that teach the same technique at different levels:
William Candillon's **"Charts with React Native Skia"** video (chapters: point smoothing →
`getYForX` → path interpolation), the **Wallet** example in the Skia repo that the video
builds, and **margelo/react-native-graph**, which packages those recipes as a library.

Two ready-to-copy files ship with this skill:

- **`assets/chartMath.ts`** — scales, resampling, decimation, three curve builders, area
  path, `getYForX`, `nearestIndex`. All worklets. Tested: monotone/linear curves pass
  through every datum, monotone never overshoots, every curve is all-cubic.
- **`assets/PriceChart.tsx`** — a complete interactive chart on top of it (morph, scrub,
  label, area fill, "dim the future" stroke). Typechecked against Skia 2.14 /
  Reanimated 4.7 / Gesture Handler 2.33.

Copy them rather than re-deriving the math; adapt the visuals.

## Contents

1. Pick the level: library or hand-rolled
2. The pipeline
3. Scale and point budget
4. Smoothing — which curve, and what it costs
5. Rendering: stroke, area fill, fades
6. Scrubbing: gesture → cursor → label
7. Switching ranges: path interpolation
8. Text and labels
9. Performance and lists
10. Cribbing from the Wallet example and react-native-graph
11. Bars, candles, axes, pies
12. Offline / Remotion charts
13. Sources

---

## 1. Pick the level: library or hand-rolled

| Need | Use |
| --- | --- |
| One smooth line (+ optional area), scrubbing, range morph — crypto/stock style | **react-native-graph** (`<LineGraph animated points color enablePanGesture … />`), *if* the Skia version fits (below) |
| Axes, ticks, multiple series, bars, stacked areas, pies, press-to-inspect | **Victory Native XL** (`victory-native`, Skia + Reanimated + d3 under the hood: `CartesianChart`, `useChartPressState`) |
| A custom look, unusual interaction, or Skia ≥ 2.14 with react-native-graph not yet updated | **Hand-roll** with `assets/chartMath.ts` + `assets/PriceChart.tsx` |
| Hundreds of tiny non-interactive sparklines in a list | Hand-rolled static `<Path>` or react-native-graph with `animated={false}` |

**Compatibility warning (checked Oct 2026).** Skia **2.14.0** made `SkPath` immutable:
`moveTo`/`lineTo`/`cubicTo`/`close` now exist only on `SkPathBuilder`
(`Skia.PathBuilder.Make()` … `.build()`, or `Skia.PathBuilder.MakeFromPath(path)` to
extend an existing path). Releases 2.6–2.13 still had the mutators but printed a one-time
`console.warn` per method pointing at the
[path migration guide](https://shopify.github.io/react-native-skia/docs/shapes/path-migration);
the TypeScript types never marked them `@deprecated`, so `tsc` stayed silent.

The stable **react-native-graph 1.4.0** (npm `latest`, Sept 2026) still calls
`Skia.Path.Make().moveTo(...)` (in `CreateGraphPath.ts` and the `straightLine` placeholder in
`AnimatedLineGraph.tsx`) and `path.copy().lineTo(...)`, and its peer dependencies don't
constrain Skia, so on Skia ≥ 2.14 it throws at runtime ("moveTo is not a function"). The
**`1.4.0-alpha.1`** prerelease, published the same day, rewrites path construction on
`Skia.Path.MakeFromCmds` behind a new multi-renderer backend layer — it avoids the crash but
is an alpha with a larger surface change. Options, in rough order of safety:

1. Pin `@shopify/react-native-skia` to `~2.13.1` (not `^`) and rebuild native.
2. `patch-package` the stable release: swap to `Skia.PathBuilder.Make()…build()`, rebuild the
   gradient path with `Skia.PathBuilder.MakeFromPath(path)`, and patch **both** `src/` and the
   `lib/module/` JS that Metro actually bundles.
3. Try `react-native-graph@1.4.0-alpha.1`.
4. Hand-roll with `assets/chartMath.ts`, or move to Victory Native XL.

Re-check npm (`npm view react-native-graph dist-tags`) before recommending — a fixed stable
release may exist by the time you read this.

The same applies to any chart code you find online: if it mutates an `SkPath`, it predates
2.14.

## 2. The pipeline

Every line chart in all three sources is the same six stages. Get the stage boundaries
right and each piece stays small:

```
raw data ─▶ scale to pixels ─▶ fix the point budget ─▶ smooth into an SkPath ─┬▶ draw (stroke + area)
 (JS)        (JS, useMemo)       (resample / decimate)    (JS, once per change) ├▶ toCmds() once → getYForX (UI, per frame)
                                                                                 └▶ interpolate(from, t) (UI, per frame)
```

The rule that makes it fast: **build paths on the JS thread once per data/size change;
on the UI thread only interpolate, hit-test, and move the cursor.** Nothing per frame
should allocate a new path from data.

## 3. Scale and point budget

**Invert Y.** Canvas y grows downward, prices grow upward:
`y = padY + h − ((v − min) / (max − min)) · h`. The Wallet example's `Model.ts` skips the
inversion (high prices draw *low*) while its `Label.tsx` maps y back as if it were
inverted, so the label and the line disagree. `chartMath.toPoints` inverts; `yToValue` /
`xToValue` are its exact inverses.

**Pad the drawing area** by at least half the stroke width (react-native-graph uses
`verticalPadding = lineThickness`) plus the cursor radius horizontally, or round caps and
the dot clip at the canvas edge.

**Guard degenerate domains.** A flat series (min = max) or a single timestamp divides by
zero. `domainOf` widens a flat y-span to ±1; `toPoints` centers a zero-width x-span.

**Fix the point budget.** Two independent reasons:

1. *Size.* A path with 10,000 cubics is slow to build, stroke, and hit-test. Nothing
   below one point per ~2 px is visible anyway.
2. *Morphing.* `SkPath.interpolate` only works between paths with the same verbs in the
   same order (`isInterpolatable`). A 24-point "1D" series and a 365-point "1Y" series
   produce different command counts and simply won't morph — `interpolate` returns `null`.

How the sources handle it, and what to do:

| Approach | Where | Effect |
| --- | --- | --- |
| Slice to a fixed count (`POINTS = 20`) | Wallet `Model.ts` | Morphs, but throws away most of the data |
| Sample one point per 2 px, keep only "exact" points | react-native-graph `createGraphPath` | Bounded size; counts *usually* match for the same width, falls back to no animation when they don't |
| **Resample to N evenly spaced x (linear interp)** | `chartMath.resample` | Same N ⇒ always interpolatable. Choose N ≈ width / 2. Smooths spikes between samples |
| **Min/max per pixel bucket** | `chartMath.decimateMinMax` | Keeps spikes (wicks, outliers) for static charts; count varies, so don't morph it |

## 4. Smoothing — which curve, and what it costs

Candillon's video spends its first chapter here; the choice has consequences people
don't expect.

| Curve | Passes through data? | Overshoots? | Seen in | Use when |
| --- | --- | --- | --- | --- |
| **Monotone** (Fritsch–Carlson; d3 `curveMonotoneX`) | Yes | **Never** | `chartMath` default | Financial / any chart where a viewer reads values off the line |
| **Basis** (uniform cubic B-spline; d3 `curveBasis`) | **No** — cuts corners | Never | react-native-graph; Wallet `"bezier"` | Decorative sparklines where smoothness beats accuracy |
| **Control-point / Catmull-like** (`smoothing` factor) | Yes | Can, at sharp turns | Wallet `"complex"` (its default) | Organic look, modest data |
| **Quadratic midpoint** | Approx. | Can | Wallet `"simple"` | Avoid — emits `quadTo`, which the original `getYForX` can't read |
| **Linear** (as cubics) | Yes | Never | `chartMath` `"linear"` | Step-like data, honest minimalism |

Measured with `chartMath` on a 60-point series with one +25 spike: monotone and linear
sit **0.000 px** from every datum; basis sits **29 px** below the spike. A B-spline price
chart visibly under-reports peaks — and the cursor riding it shows prices that never
existed. That's why section 6 reads the label from the data, not the curve.

Every builder in `chartMath` emits **only cubic segments** (linear segments are encoded
as cubics with ⅓/⅔ control points, endpoints as degenerate cubics). That keeps all three
curves compatible with `getYForX` and with each other's structure for a given N.

Using d3 instead (`d3-shape` + `Skia.Path.MakeFromSVGString(line().curve(curveMonotoneX)(pts)!)`)
works for drawing, but `curveBasis` output starts and ends with `L` segments and
`curveLinear` is all `L`. The `getYForX` in the Wallet example and react-native-graph only
walks `Move` + `Cubic` verbs and returns garbage/undefined on those segments.
`chartMath.getYForX` handles `Line` and `Quad` too, but prefer an all-cubic builder so
interpolation structure stays predictable.

## 5. Rendering: stroke, area fill, fades

**Stroke:** `style="stroke"`, `strokeJoin="round"`, `strokeCap="round"`. A horizontal
`<LinearGradient start={vec(0,0)} end={vec(width,0)} colors={…} />` child gives the
Wallet's multi-color line.

**Area fill:** extend the line down to the baseline and close it:

```ts
const area = Skia.PathBuilder.MakeFromPath(line)
  .lineTo(last.x, baselineY).lineTo(first.x, baselineY).close().build(); // chartMath.areaPath
```

Equivalent, when you still hold the line's builder: `builder.build()` takes a snapshot
*without* resetting the builder (only `builder.detach()` resets), so you can
`const line = b.build(); const area = b.lineTo(…).lineTo(…).close().build();`. Verified in
the 2.14 native binding (`JsiSkPathBuilder::build` → `snapshot()`).

Fill it with a vertical gradient from `color + "66"` to `color + "00"`. Area paths
interpolate whenever their lines do (same appended verbs), so morph both with the same
progress. Draw the area *before* the stroke. Never hit-test the area path.

**Alpha suffixes need six-digit hex.** `"#fff" + "33"` is not a color. react-native-graph
normalizes with `getSixDigitHex`; do the same or take colors as `Skia.Color`/rgba.

**Fade-in at the left edge** (react-native-graph `enableFadeInMask`): stroke gradient
`[color+"00", color+"ff"]` over the first ~15% of the width.

**Dim the future while scrubbing** (react-native-graph's nicest trick): give the stroke
gradient duplicated stop positions so there's a hard edge at the finger.

```ts
const stops = useDerivedValue(() => {
  const p = active.value ? x.value / width : 1;
  return [0, p, p, 1];
});
// colors: [color, color, color + "40", color + "40"], positions={stops}
```

Duplicate positions = no blend region. `positions` accepts a derived value, so this runs
entirely on the UI thread.

**Last-point indicator** (`enableIndicator`): a circle at the final point whose y comes
from `getYForX(cmds, lastX)`; pulse it with `withRepeat(withSequence(…))` on radius and
opacity, and stop pulsing while the user scrubs.

## 6. Scrubbing: gesture → cursor → label

**The gesture.** Wrap the `<Canvas>` (or a `View` around it) in a `GestureDetector`
with `Gesture.Pan()`. Pick activation by context:

- Standalone chart: `.minDistance(0)` (Wallet) so the cursor appears on touch-down.
- Inside a `ScrollView`/`FlatList`: `.activateAfterLongPress(120–300)`
  (react-native-graph's `panGestureDelay`, default 300) — otherwise the chart steals
  vertical scrolls.
- **Reset state in `.onFinalize`, not only `.onEnd`.** When a parent scroll view cancels
  the pan, `onEnd` never fires and the cursor stays stuck on screen. react-native-graph
  fixed exactly this bug.

Clamp `x` to the padded drawing area. Memoize the gesture with `useMemo`.

**The cursor's y: `getYForX`.** This is the video's centerpiece. Given the finger's x,
find the cubic segment spanning it, solve `x(t) = x` for the curve parameter t, and
evaluate `y(t)`. The Wallet/react-native-graph version solves the cubic analytically and
rounds roots to 2 decimals; `chartMath.getYForX` bisects instead (24 iterations, robust
for any left-to-right segment) and clamps outside the data. Feed it **cached** commands:

```ts
// once per path (JS):        const cmds = line.toCmds();
// per frame (UI):            const cy = useDerivedValue(() => getYForX(cmds.value, x.value) ?? 0);
```

`path.toCmds()` allocates; the Wallet calls it inside a derived value on every frame.
Only do that while the path is mid-morph (see `PriceChart.tsx`: live commands while
`progress < 1`, cached otherwise).

**The label's value: read the data, not the curve.** Convert finger x → data x with
`xToValue`, then `nearestIndex(data, dataX)` (binary search) and show `data[i].y`. The
curve's y between samples is an interpolation artifact — on a basis curve it's off by
pixels-worth of price. react-native-graph does the same (`getClosestPointIndex`).

**Talking to React.** Fire `runOnJS(onPointSelected)(datum)` (Reanimated 4 also offers
`scheduleOnRN` from react-native-worklets) **only when the index changes** — not on every
pan event — to drive haptics or a React-rendered header. Keep the in-canvas label on the
UI thread (section 8) so it never waits on JS.

**Touch target / element tracking.** Skia drawings can't receive touches. For a larger
hit area or an accessible element that follows the cursor, the Wallet overlays a
`pointerEvents="none"` `Animated.View` positioned with `useAnimatedStyle` from the same
`x`/`y` shared values.

**Cursor appearance.** Animate opacity/radius with `withTiming`/`withSpring` set in
`onStart`/`onFinalize` (react-native-graph's `SelectionDot` springs radius 0→5).
Concentric translucent circles + a white stroke ring (Wallet `Cursor.tsx`) read well on
dark backgrounds. To tint the cursor by its x along a gradient, use Skia's
`interpolateColors(x / width, stops, colors)` — the Wallet uses Reanimated's
`interpolateColor` and then has to unpack the packed ARGB integer by hand.

## 7. Switching ranges: path interpolation

**Direction of `interpolate`.** `to.interpolate(from, t)` returns `to` at `t = 1` and
`from` at `t = 0` (Skia: weight 1 = *this* path). Both sources write it this way; getting
it backwards makes the animation run in reverse.

```ts
const line = useDerivedValue(() =>
  graphs[toIndex.value].line.interpolate(fromLine.value, progress.value) ?? graphs[toIndex.value].line
);
```

**Preconditions.** Same verbs, same order — guaranteed by `resample(…, N)` + the same
curve type. Check `isInterpolatable` if inputs can vary; `interpolate` returns `null`
otherwise, so always keep a `?? to` fallback.

**Make it interruptible.** The Wallet stores indices `{ current, next }` and on tap sets
`current = next` — a tap mid-animation snaps to the old target first. react-native-graph
instead captures *what's on screen now* as the new `from`:

```ts
fromLine.value = line.value;      // the currently displayed, half-morphed path
toIndex.value = nextIndex;
cancelAnimation(progress);
progress.value = 0;               // must restart from 0, or withTiming(1) at 1 does nothing
progress.value = withTiming(1, { duration: 450 });
```

**Entrance animation.** Morph from a flat line with the same structure
(`chartMath.flatLine(N, frame, midY)`) — react-native-graph's `straightLine` placeholder.

**Data refresh = same mechanism.** New prices for the same range just become the new
`to`; react-native-graph re-runs the morph on every points change.

**Range selector.** The Wallet `Selection.tsx`: a row of RN `TouchableWithoutFeedback`
buttons over a Skia `<Canvas style={StyleSheet.absoluteFill}>` holding a gradient
`<RoundedRect>` pill whose `translateX = mix(progress, currentIndex·w, nextIndex·w)`. The
pill and the chart share the same `progress` shared value, so they move in lockstep.

## 8. Text and labels

- **In-canvas, UI-thread label:** `<Text text={derivedString} font={font} />`. `text`
  accepts a shared/derived value, so the price updates every frame with zero React
  renders.
- **Fonts:** `matchFont({ fontFamily, fontSize })` for system fonts (no loading state), or
  `useFont(require("./Font.otf"), size)` which returns `null` until loaded — guard it,
  including inside worklets that call `font.measureText`.
- **Centering:** `x = width / 2 − font.measureText(str).width / 2`, computed in a derived
  value. Measuring the *max* string once (as the Wallet does) avoids the label jittering
  as digits change; a monospaced font (Wallet: SF Mono) helps further.
- **Formatting on the UI thread:** don't rely on `Intl`/`toLocaleString` inside worklets;
  use a small regex formatter (`PriceChart.tsx` `formatPrice`, Wallet `format`).
- **Axis labels / min–max captions** that don't animate are simpler as RN `<Text>` above
  and below the canvas (react-native-graph's `TopAxisLabel` / `BottomAxisLabel`).

## 9. Performance and lists

- `useMemo` the built graphs keyed on data + size; never rebuild in render.
- Static charts (lists, cards): render a plain `<Path>` with no shared values, no
  gesture, no gradients that depend on animation. react-native-graph splits
  `StaticLineGraph` vs `AnimatedLineGraph` for exactly this reason — dozens of animated
  canvases in a `FlatList` will drop frames during scroll.
- Measure with `onLayout` (react-native-graph) or pass the width in; a canvas with
  width 0 must early-return before building paths.
- Worklets capture what they reference. Capturing large data arrays in many worklets
  copies them to the UI runtime; capture the built `graphs` array once (as the Wallet
  does) or store commands in a shared value (react-native-graph).
- Point budget (section 3) bounds `getYForX` cost: it's O(segments) per frame, fine
  for a few hundred.

## 10. Cribbing from the Wallet example and react-native-graph

Both are excellent references. When copying from them, fix these:

| Source | Issue | Fix |
| --- | --- | --- |
| Wallet (all files) | Imports from `"react-native-skia"` — a monorepo alias | `@shopify/react-native-skia` |
| Wallet `Math.ts` | Imports `exhaustiveCheck` from an internal path | Delete it or inline `const _: never = strategy` |
| Wallet `Model.ts` | Y not inverted; `Label.tsx` assumes it is | Invert (`chartMath.toPoints`) |
| Wallet `Model.ts` | Pushes an extra point at `WIDTH + 10` so the right edge has a segment | Clamp in `getYForX` instead |
| Wallet `Math.ts` `getYForX` | Falls back to `cmds[1][6]` (the first segment's end y) when no segment matches | Clamp to first/last point |
| Wallet `Wallet.tsx` | `path.value.toCmds()` every frame | Cache when not morphing |
| Wallet `Selection.tsx` | Tap mid-transition snaps | Capture the on-screen path as `from` (section 7) |
| Wallet `Cursor.tsx` | Reanimated `interpolateColor` + manual ARGB unpacking | Skia `interpolateColors` |
| react-native-graph (stable 1.4.0) | Mutates `SkPath` — breaks on Skia ≥ 2.14 | `Skia.PathBuilder` (or the 1.4.0-alpha.1 `MakeFromCmds` rewrite) |
| react-native-graph | B-spline curve under-reports peaks | Monotone curve if values matter |
| react-native-graph | `selectionDotShadowColor` is documented as unused | Style a custom `SelectionDot` |
| Both `getYForX` | Only `Move` + `Cubic` verbs | Use an all-cubic builder, or `chartMath.getYForX` |

## 11. Bars, candles, axes, pies

The same rules carry over; only the geometry changes.

- **Bars:** one `<RoundedRect>` per bar, or for many bars a single path built from
  `addRRect` calls (one draw). Animate heights by interpolating a progress value into
  each bar's height/y (or by building both paths with identical structure and using
  `interpolate`). Hit-test with `nearestIndex` on bar centers — no curve solving needed.
- **Candles:** wick = `<Line>`, body = `<Rect>`; build all into two paths (up/down
  colors) per range. Use `decimateMinMax`-style bucketing when zoomed out.
- **Axes/grid:** `<Line>`s with `DashPathEffect` for gridlines; tick labels via
  `<Text>`/`matchFont`. If you need nice ticks, `d3-scale`'s `.ticks()` / `.nice()` is
  worth the dependency (the video recommends D3/visx for scaling).
- **Pies/donuts:** arcs via `Skia.PathBuilder.Make().addArc(oval, start, sweep)` or a
  stroked `<Path>` with `start`/`end` trim props animated per slice; angles in degrees
  for `addArc`, radians everywhere else.
- Reaching for all of these at once is the signal to use Victory Native XL instead.

## 12. Offline / Remotion charts

No gestures and no Reanimated clock (see `offline-rendering.md`). Drive everything from
the frame: `progress = interpolate(frame, [start, end], [0, 1], clamp)` for the morph,
`end={progress}` on the `<Path>` for a draw-on reveal, and `x = progress · width` +
`getYForX` for a cursor that "plays" across the line. Build paths once per composition
props, not per frame.

## 13. Sources

- Video: William Candillon, "Charts with React Native Skia" (May 2022) —
  https://youtu.be/xeLdmn3se1I — chapters: point smoothing, getYForX, path interpolation.
- Wallet example: https://github.com/Shopify/react-native-skia/tree/main/apps/example/src/Examples/Wallet
  (`Model.ts` data → path, `Math.ts` smoothing + `getYForX`, `Wallet.tsx` morph + cursor,
  `components/Selection.tsx` range pill, `components/Label.tsx` UI-thread text,
  `components/useGraphTouchHandler.ts` pan).
- react-native-graph: https://github.com/margelo/react-native-graph (source under
  `package/src`: `CreateGraphPath.ts`, `GetYForX.ts`, `AnimatedLineGraph.tsx`,
  `hooks/usePanGesture.ts`, `SelectionDot.tsx`).
- Victory Native XL: https://commerce.nearform.com/open-source/victory-native/
- Bézier background for `getYForX`: "A Primer on Bézier Curves", https://pomax.github.io/bezierinfo/
