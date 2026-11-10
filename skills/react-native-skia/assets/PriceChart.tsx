/**
 * PriceChart.tsx — reference implementation of an interactive Skia line chart:
 * range switching with an interruptible path morph, gradient area fill, a scrub
 * cursor that rides the curve, a live value label, and "dim the future" stroke.
 *
 * Built on ./chartMath (copy both files). Typechecked against
 * @shopify/react-native-skia 2.14, react-native-reanimated 4.7 and
 * react-native-gesture-handler 2.33; uses only APIs that also exist in Reanimated 3.
 *
 * Wrap the app in <GestureHandlerRootView>. Inside a ScrollView keep
 * activateAfterLongPress so vertical scrolling still works.
 */
import React, { useEffect, useMemo, useRef } from "react";
import { Platform } from "react-native";
import {
  Canvas,
  Circle,
  Group,
  LinearGradient,
  Line,
  Path,
  Text,
  matchFont,
  vec,
} from "@shopify/react-native-skia";
import type { PathCommand, SkPath } from "@shopify/react-native-skia";
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import {
  cancelAnimation,
  runOnJS,
  useDerivedValue,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";

import {
  areaPath,
  domainOf,
  getYForX,
  linePath,
  nearestIndex,
  resample,
  toPoints,
  xToValue,
} from "./chartMath";
import type { Datum, Domain, Frame } from "./chartMath";

/** Fixed point budget: every range resamples to this, so any two ranges interpolate. */
const POINTS = 120;

const font = matchFont({
  fontFamily: Platform.select({ ios: "Helvetica", default: "sans-serif" }),
  fontSize: 28,
  fontWeight: "600",
});

interface Graph {
  data: Datum[];
  domain: Domain;
  line: SkPath;
  area: SkPath;
  cmds: PathCommand[];
}

const buildGraph = (raw: Datum[], frame: Frame): Graph => {
  const data = resample(raw, POINTS);
  const domain = domainOf(data, 0.08);
  const pts = toPoints(data, frame, domain);
  const line = linePath(pts, "monotone");
  return {
    data,
    domain,
    line,
    area: areaPath(line, pts, frame.height),
    cmds: line.toCmds(),
  };
};

// Worklet-safe formatter: Intl is not guaranteed on the UI runtime.
const formatPrice = (v: number) => {
  "worklet";
  const [int, dec = "00"] = v.toFixed(2).split(".");
  return `$${int.replace(/\B(?=(\d{3})+(?!\d))/g, ",")}.${dec}`;
};

const clamp = (v: number, lo: number, hi: number) => {
  "worklet";
  return Math.min(Math.max(v, lo), hi);
};

export interface PriceChartProps {
  /** One series per range (1D, 1W, 1M…), each sorted oldest → newest, x in ms. */
  ranges: Datum[][];
  /** Index into `ranges` to show. Changing it morphs the line. */
  rangeIndex: number;
  width: number;
  height?: number;
  /** Six-digit hex; alpha suffixes are appended to it. */
  color?: string;
  /** Called on the JS thread each time the scrub crosses a new datum; null on release. */
  onSelect?: (d: Datum | null) => void;
}

export function PriceChart({
  ranges,
  rangeIndex,
  width,
  height = 240,
  color = "#31CBD1",
  onSelect,
}: PriceChartProps) {
  const labelSpace = 56;
  const frame = useMemo<Frame>(
    () => ({ width, height: height - labelSpace, padX: 12, padY: 12 }),
    [width, height]
  );
  // Paths are built once per data/size change on the JS thread, never per frame.
  const graphs = useMemo(
    () => ranges.map((r) => buildGraph(r, frame)),
    [ranges, frame]
  );
  const safeIndex = clamp(rangeIndex, 0, Math.max(graphs.length - 1, 0));
  const target = graphs[safeIndex];

  // ---- range morph -------------------------------------------------------
  const fromLine = useSharedValue<SkPath>(target.line);
  const fromArea = useSharedValue<SkPath>(target.area);
  const toIndex = useSharedValue(safeIndex);
  const progress = useSharedValue(1);

  // SkPath.interpolate(other, w): w = 1 → this path, w = 0 → other.
  const line = useDerivedValue(() => {
    const to = graphs[toIndex.value].line;
    return to.interpolate(fromLine.value, progress.value) ?? to;
  });
  const area = useDerivedValue(() => {
    const to = graphs[toIndex.value].area;
    return to.interpolate(fromArea.value, progress.value) ?? to;
  });

  // Morph on range change AND on data refresh, but not on first mount.
  const mounted = useRef(false);
  useEffect(() => {
    if (!mounted.current) {
      mounted.current = true;
      return;
    }
    // Start from what is on screen right now, so a mid-flight tap doesn't jump.
    fromLine.value = line.value;
    fromArea.value = area.value;
    toIndex.value = safeIndex;
    cancelAnimation(progress);
    progress.value = 0;
    progress.value = withTiming(1, { duration: 450 });
    // Shared values are stable refs; only the target index should retrigger.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [safeIndex, graphs]);

  // Cached commands when idle; the live morphing path only while animating.
  const cmds = useDerivedValue(() =>
    progress.value < 1 ? line.value.toCmds() : graphs[toIndex.value].cmds
  );

  // ---- scrubbing ---------------------------------------------------------
  const x = useSharedValue(0);
  const active = useSharedValue(false);
  const cursorOpacity = useSharedValue(0);
  const lastIndex = useSharedValue(-1);

  const pan = useMemo(() => {
    const notify = (d: Datum | null) => onSelect?.(d);
    const update = (px: number) => {
      "worklet";
      x.value = clamp(px, frame.padX ?? 0, width - (frame.padX ?? 0));
      const g = graphs[toIndex.value];
      const i = nearestIndex(g.data, xToValue(x.value, frame, g.domain));
      if (i !== lastIndex.value) {
        lastIndex.value = i;
        runOnJS(notify)(g.data[i]);
      }
    };
    return Gesture.Pan()
      .activateAfterLongPress(120) // lets a parent ScrollView keep vertical swipes
      .onStart((e) => {
        active.value = true;
        cursorOpacity.value = withTiming(1, { duration: 120 });
        update(e.x);
      })
      .onUpdate((e) => update(e.x))
      .onFinalize(() => {
        // onFinalize also runs on cancel (e.g. the ScrollView took over); onEnd does not.
        active.value = false;
        cursorOpacity.value = withTiming(0, { duration: 160 });
        lastIndex.value = -1;
        runOnJS(notify)(null);
      });
  }, [graphs, frame, width, onSelect, x, active, cursorOpacity, lastIndex, toIndex]);

  // The dot rides the drawn curve; the label reads the real datum.
  const cy = useDerivedValue(() => getYForX(cmds.value, x.value) ?? 0);
  const guideTop = useDerivedValue(() => vec(x.value, frame.padY ?? 0));
  const guideBottom = useDerivedValue(() => vec(x.value, frame.height));
  const label = useDerivedValue(() => {
    const g = graphs[toIndex.value];
    if (!active.value || lastIndex.value < 0) {
      return formatPrice(g.data[g.data.length - 1]?.y ?? 0);
    }
    return formatPrice(g.data[lastIndex.value].y);
  });

  // Hard stop at the finger: past it the stroke dims. Duplicate positions = no blend.
  const stops = useDerivedValue(() => {
    const p = active.value ? clamp(x.value / width, 0, 1) : 1;
    return [0, p, p, 1];
  });
  const strokeColors = [color, color, `${color}40`, `${color}40`];

  return (
    <GestureDetector gesture={pan}>
      <Canvas style={{ width, height }}>
        <Text x={16} y={36} text={label} font={font} color="white" />
        <Group transform={[{ translateY: labelSpace }]}>
          <Path path={area}>
            <LinearGradient
              start={vec(0, 0)}
              end={vec(0, frame.height)}
              colors={[`${color}66`, `${color}00`]}
            />
          </Path>
          <Path
            path={line}
            style="stroke"
            strokeWidth={3}
            strokeJoin="round"
            strokeCap="round"
          >
            <LinearGradient
              start={vec(0, 0)}
              end={vec(width, 0)}
              colors={strokeColors}
              positions={stops}
            />
          </Path>
          <Group opacity={cursorOpacity}>
            <Line
              p1={guideTop}
              p2={guideBottom}
              color={`${color}80`}
              strokeWidth={1}
            />
            <Circle cx={x} cy={cy} r={14} color={color} opacity={0.2} />
            <Circle cx={x} cy={cy} r={6} color={color} />
            <Circle cx={x} cy={cy} r={6} color="white" style="stroke" strokeWidth={2} />
          </Group>
        </Group>
      </Canvas>
    </GestureDetector>
  );
}
