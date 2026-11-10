/**
 * chartMath.ts — portable line-chart geometry for @shopify/react-native-skia.
 *
 * Copy this file into the project (e.g. src/charts/chartMath.ts). It distils the
 * techniques from William Candillon's Wallet example (Shopify/react-native-skia,
 * apps/example/src/Examples/Wallet) and margelo/react-native-graph, with their known
 * edge-case bugs fixed:
 *   - Y is inverted (larger values draw higher), so pixel ↔ value mapping is consistent.
 *   - Every segment is a cubic, so getYForX works for every curve type.
 *   - getYForX clamps outside the data instead of returning a random command's y.
 *   - Paths are built with Skia.PathBuilder (SkPath is immutable in Skia ≥ 2.14).
 *
 * Every function is a worklet, so it runs on the JS thread (useMemo) and on the UI
 * thread (useDerivedValue, gesture callbacks) alike.
 */
import { PathVerb, Skia } from "@shopify/react-native-skia";
import type { PathCommand, SkPath } from "@shopify/react-native-skia";

/** A data point: x is a timestamp in ms (or an index), y is the value. */
export interface Datum {
  x: number;
  y: number;
}

/** A point in canvas pixels. */
export interface Point {
  x: number;
  y: number;
}

/** The drawing area. Padding keeps the stroke, cursor and caps from being clipped. */
export interface Frame {
  width: number;
  height: number;
  padX?: number;
  padY?: number;
}

export interface Domain {
  x: [number, number];
  y: [number, number];
}

export type Curve = "monotone" | "basis" | "linear";

// ---------------------------------------------------------------------------
// Scales
// ---------------------------------------------------------------------------

/**
 * Data extents. `yPad` adds headroom as a fraction of the y-span (0.1 = 10% above
 * and below). A flat series gets a ±1 span so nothing divides by zero.
 */
export const domainOf = (data: Datum[], yPad = 0): Domain => {
  "worklet";
  let x0 = Infinity;
  let x1 = -Infinity;
  let y0 = Infinity;
  let y1 = -Infinity;
  for (let i = 0; i < data.length; i++) {
    const d = data[i];
    if (d.x < x0) x0 = d.x;
    if (d.x > x1) x1 = d.x;
    if (d.y < y0) y0 = d.y;
    if (d.y > y1) y1 = d.y;
  }
  if (data.length === 0) return { x: [0, 1], y: [0, 1] };
  if (y0 === y1) {
    y0 -= 1;
    y1 += 1;
  }
  const pad = (y1 - y0) * yPad;
  return { x: [x0, x1], y: [y0 - pad, y1 + pad] };
};

const inner = (frame: Frame) => {
  "worklet";
  const padX = frame.padX ?? 0;
  const padY = frame.padY ?? 0;
  return {
    padX,
    padY,
    w: Math.max(frame.width - 2 * padX, 0),
    h: Math.max(frame.height - 2 * padY, 0),
  };
};

/** Data → canvas pixels. Larger y values draw higher (smaller pixel y). */
export const toPoints = (
  data: Datum[],
  frame: Frame,
  domain: Domain = domainOf(data)
): Point[] => {
  "worklet";
  const { padX, padY, w, h } = inner(frame);
  const [x0, x1] = domain.x;
  const [y0, y1] = domain.y;
  const dx = x1 - x0;
  const dy = y1 - y0 || 1;
  return data.map((d) => ({
    x: padX + (dx === 0 ? 0.5 : (d.x - x0) / dx) * w,
    y: padY + h - ((d.y - y0) / dy) * h,
  }));
};

/** Canvas pixel x → data x (e.g. the timestamp under the finger). */
export const xToValue = (px: number, frame: Frame, domain: Domain): number => {
  "worklet";
  const { padX, w } = inner(frame);
  const [x0, x1] = domain.x;
  return x0 + ((px - padX) / (w || 1)) * (x1 - x0);
};

/** Canvas pixel y → data y (e.g. the price under the cursor). */
export const yToValue = (py: number, frame: Frame, domain: Domain): number => {
  "worklet";
  const { padY, h } = inner(frame);
  const [y0, y1] = domain.y;
  return y0 + ((padY + h - py) / (h || 1)) * (y1 - y0);
};

// ---------------------------------------------------------------------------
// Point budgets
// ---------------------------------------------------------------------------

/**
 * Resample to exactly `count` points, evenly spaced in x, linearly interpolating y.
 * Use it so every range (1H, 1D, 1Y…) produces the same number of path commands —
 * the precondition for SkPath.interpolate morphing between them. Trade-off: spikes
 * between samples are smoothed away; pick count ≈ chart width / 2 px.
 * `data` must be sorted by x.
 */
export const resample = (data: Datum[], count: number): Datum[] => {
  "worklet";
  const n = data.length;
  if (n === 0 || count < 1) return [];
  if (n === 1 || count === 1) {
    const out: Datum[] = [];
    for (let i = 0; i < count; i++) out.push({ x: data[0].x, y: data[0].y });
    return out;
  }
  const x0 = data[0].x;
  const x1 = data[n - 1].x;
  const out: Datum[] = [];
  let j = 0;
  for (let i = 0; i < count; i++) {
    const x = x0 + ((x1 - x0) * i) / (count - 1);
    while (j < n - 2 && data[j + 1].x < x) j++;
    const a = data[j];
    const b = data[j + 1];
    const t = b.x === a.x ? 0 : (x - a.x) / (b.x - a.x);
    out.push({ x, y: a.y + (b.y - a.y) * Math.min(Math.max(t, 0), 1) });
  }
  return out;
};

/**
 * Min/max decimation for large static series: keep at most the lowest and highest
 * point of every `bucketPx`-wide column, in x order. Preserves spikes (unlike
 * resample) but the output length varies, so don't use it on paths you morph.
 */
export const decimateMinMax = (points: Point[], bucketPx = 2): Point[] => {
  "worklet";
  if (points.length <= 2) return points.slice();
  const out: Point[] = [points[0]];
  let start = 1;
  while (start < points.length - 1) {
    const bucket = Math.floor(points[start].x / bucketPx);
    let lo = start;
    let hi = start;
    let end = start;
    while (
      end < points.length - 1 &&
      Math.floor(points[end].x / bucketPx) === bucket
    ) {
      if (points[end].y < points[lo].y) lo = end;
      if (points[end].y > points[hi].y) hi = end;
      end++;
    }
    if (lo === hi) out.push(points[lo]);
    else if (lo < hi) out.push(points[lo], points[hi]);
    else out.push(points[hi], points[lo]);
    start = end;
  }
  out.push(points[points.length - 1]);
  return out;
};

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

/**
 * Build the line. All segments are cubics, and the command count depends only on
 * the number of points and the curve type, so same-length inputs always interpolate.
 *
 * - "monotone": passes through every point and never overshoots (Fritsch–Carlson,
 *   same as d3 curveMonotoneX). Default — the line never shows a price that wasn't
 *   in the data.
 * - "basis": uniform cubic B-spline (what react-native-graph and the Wallet "bezier"
 *   strategy draw). Smoothest, but it cuts corners: peaks render lower than the data.
 * - "linear": straight segments, encoded as cubics so getYForX and morphing still work.
 *
 * `pts` must be sorted by x with no duplicate x values.
 */
export const linePath = (pts: Point[], curve: Curve = "monotone"): SkPath => {
  "worklet";
  const b = Skia.PathBuilder.Make();
  const n = pts.length;
  if (n === 0) return b.build();
  b.moveTo(pts[0].x, pts[0].y);
  if (n === 1) {
    b.cubicTo(pts[0].x, pts[0].y, pts[0].x, pts[0].y, pts[0].x, pts[0].y);
    return b.build();
  }

  if (curve === "linear") {
    for (let i = 1; i < n; i++) {
      const a = pts[i - 1];
      const c = pts[i];
      b.cubicTo(
        a.x + (c.x - a.x) / 3,
        a.y + (c.y - a.y) / 3,
        a.x + (2 * (c.x - a.x)) / 3,
        a.y + (2 * (c.y - a.y)) / 3,
        c.x,
        c.y
      );
    }
    return b.build();
  }

  if (curve === "basis") {
    for (let i = 1; i < n; i++) {
      const p0 = i >= 2 ? pts[i - 2] : pts[i - 1];
      const p1 = pts[i - 1];
      const p2 = pts[i];
      b.cubicTo(
        (2 * p0.x + p1.x) / 3,
        (2 * p0.y + p1.y) / 3,
        (p0.x + 2 * p1.x) / 3,
        (p0.y + 2 * p1.y) / 3,
        (p0.x + 4 * p1.x + p2.x) / 6,
        (p0.y + 4 * p1.y + p2.y) / 6
      );
    }
    // Land exactly on the last point. Kept as a cubic so the path stays all-cubic.
    const last = pts[n - 1];
    const p0 = pts[n - 2];
    b.cubicTo(
      (2 * p0.x + last.x) / 3,
      (2 * p0.y + last.y) / 3,
      (p0.x + 2 * last.x) / 3,
      (p0.y + 2 * last.y) / 3,
      last.x,
      last.y
    );
    return b.build();
  }

  // monotone — tangents per d3-shape's curveMonotoneX (slope3 / slope2).
  const tangents: number[] = new Array(n);
  const sign = (v: number) => (v < 0 ? -1 : 1);
  for (let i = 1; i < n - 1; i++) {
    const h0 = pts[i].x - pts[i - 1].x;
    const h1 = pts[i + 1].x - pts[i].x;
    const s0 = h0 ? (pts[i].y - pts[i - 1].y) / h0 : 0;
    const s1 = h1 ? (pts[i + 1].y - pts[i].y) / h1 : 0;
    const p = h0 + h1 ? (s0 * h1 + s1 * h0) / (h0 + h1) : 0;
    const t =
      (sign(s0) + sign(s1)) *
      Math.min(Math.abs(s0), Math.abs(s1), 0.5 * Math.abs(p));
    tangents[i] = Number.isFinite(t) ? t : 0;
  }
  const endSlope = (a: Point, c: Point, t: number) => {
    const h = c.x - a.x;
    return h ? (3 * (c.y - a.y)) / h / 2 - t / 2 : t;
  };
  if (n === 2) {
    const s = (pts[1].y - pts[0].y) / (pts[1].x - pts[0].x || 1);
    tangents[0] = s;
    tangents[1] = s;
  } else {
    tangents[0] = endSlope(pts[0], pts[1], tangents[1]);
    tangents[n - 1] = endSlope(pts[n - 2], pts[n - 1], tangents[n - 2]);
  }
  for (let i = 1; i < n; i++) {
    const a = pts[i - 1];
    const c = pts[i];
    const dx = (c.x - a.x) / 3;
    b.cubicTo(
      a.x + dx,
      a.y + dx * tangents[i - 1],
      c.x - dx,
      c.y - dx * tangents[i],
      c.x,
      c.y
    );
  }
  return b.build();
};

/**
 * Close a line into an area for a gradient fill: down to `baselineY`, back to the
 * first x, close. Interpolates whenever the line does. Never feed it to getYForX.
 */
export const areaPath = (
  line: SkPath,
  pts: Point[],
  baselineY: number
): SkPath => {
  "worklet";
  if (pts.length === 0) return line;
  const b = Skia.PathBuilder.MakeFromPath(line);
  b.lineTo(pts[pts.length - 1].x, baselineY);
  b.lineTo(pts[0].x, baselineY);
  b.close();
  return b.build();
};

/**
 * A flat line at `y` with the same structure linePath produces for `count` points
 * of the given curve — the "from" path for an entrance morph before data arrives.
 */
export const flatLine = (
  count: number,
  frame: Frame,
  y: number,
  curve: Curve = "monotone"
): SkPath => {
  "worklet";
  const { padX, w } = inner(frame);
  const pts: Point[] = [];
  for (let i = 0; i < count; i++) {
    pts.push({ x: padX + (count === 1 ? 0.5 : i / (count - 1)) * w, y });
  }
  return linePath(pts, curve);
};

// ---------------------------------------------------------------------------
// Hit testing
// ---------------------------------------------------------------------------

const cubicAt = (t: number, a: number, b: number, c: number, d: number) => {
  "worklet";
  const u = 1 - t;
  return u * u * u * a + 3 * u * u * t * b + 3 * u * t * t * c + t * t * t * d;
};

const quadAt = (t: number, a: number, b: number, c: number) => {
  "worklet";
  const u = 1 - t;
  return u * u * a + 2 * u * t * b + t * t * c;
};

/**
 * The y of the path at pixel x. Walks Move/Line/Quad/Cubic commands, finds the
 * segment spanning x, and bisects for the curve parameter (robust for any segment
 * whose x runs left→right, which every curve above guarantees). Outside the path's
 * x-range it clamps to the first/last point. Returns undefined for an empty path.
 *
 * Call `path.toCmds()` once per path and keep the result in a shared value: that
 * call allocates, and gesture handlers fire every frame.
 */
export const getYForX = (
  cmds: PathCommand[],
  x: number
): number | undefined => {
  "worklet";
  let cx = 0;
  let cy = 0;
  let firstX: number | undefined;
  let firstY = 0;
  let lastX = 0;
  let lastY = 0;
  for (let i = 0; i < cmds.length; i++) {
    const c = cmds[i];
    const verb = c[0];
    if (verb === PathVerb.Move) {
      cx = c[1];
      cy = c[2];
      if (firstX === undefined) {
        firstX = cx;
        firstY = cy;
      }
      continue;
    }
    let ex: number;
    let ey: number;
    if (verb === PathVerb.Line) {
      ex = c[1];
      ey = c[2];
      if (x >= cx && x <= ex) {
        return ex === cx ? ey : cy + ((x - cx) / (ex - cx)) * (ey - cy);
      }
    } else if (verb === PathVerb.Quad) {
      ex = c[3];
      ey = c[4];
      if (x >= cx && x <= ex) {
        let lo = 0;
        let hi = 1;
        for (let k = 0; k < 24; k++) {
          const m = (lo + hi) / 2;
          if (quadAt(m, cx, c[1], ex) < x) lo = m;
          else hi = m;
        }
        return quadAt((lo + hi) / 2, cy, c[2], ey);
      }
    } else if (verb === PathVerb.Cubic) {
      ex = c[5];
      ey = c[6];
      if (x >= cx && x <= ex) {
        let lo = 0;
        let hi = 1;
        for (let k = 0; k < 24; k++) {
          const m = (lo + hi) / 2;
          if (cubicAt(m, cx, c[1], c[3], ex) < x) lo = m;
          else hi = m;
        }
        return cubicAt((lo + hi) / 2, cy, c[2], c[4], ey);
      }
    } else {
      // Conic / Close: not produced by these builders; skip.
      continue;
    }
    cx = ex;
    cy = ey;
    lastX = ex;
    lastY = ey;
  }
  if (firstX === undefined) return undefined;
  return x < firstX ? firstY : lastY;
};

/**
 * Index of the datum whose x is closest to `x` (data space), by binary search.
 * Use it for the scrub label: read the value from the data, not from the curve —
 * a smoothed curve's y between samples is not a real price.
 */
export const nearestIndex = (data: Datum[], x: number): number => {
  "worklet";
  const n = data.length;
  if (n === 0) return -1;
  let lo = 0;
  let hi = n - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (data[mid].x < x) lo = mid + 1;
    else hi = mid;
  }
  if (lo > 0 && x - data[lo - 1].x <= data[lo].x - x) return lo - 1;
  return lo;
};
