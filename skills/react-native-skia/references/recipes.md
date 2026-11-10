# Recipes

Production-ready snippets for common visual effects. Each recipe is self-contained — copy, adjust, ship. Tune dimensions, colors, and easing to taste.

## Circular progress

A ring that fills from 0 to 1 as `progress` animates.

```tsx
import { Canvas, Path, Skia, SkPath } from "@shopify/react-native-skia";
import { useSharedValue, withTiming } from "react-native-reanimated";
import { useEffect, useMemo } from "react";

const size = 200;
const strokeWidth = 16;
const r = (size - strokeWidth) / 2;

export const CircularProgress = ({ target = 0.75 }) => {
  const progress = useSharedValue(0);

  const path = useMemo(
    () => Skia.PathBuilder.Make().addCircle(size / 2, size / 2, r).build(),
    []
  );

  useEffect(() => {
    progress.value = withTiming(target, { duration: 1000 });
  }, [target]);

  return (
    <Canvas style={{ width: size, height: size }}>
      <Path
        path={path}
        style="stroke"
        strokeWidth={strokeWidth}
        color="rgba(255,255,255,0.1)"
      />
      <Path
        path={path}
        style="stroke"
        strokeWidth={strokeWidth}
        strokeCap="round"
        color="#3E7CB1"
        start={0}
        end={progress}
      />
    </Canvas>
  );
};
```

## Frosted glass card (glassmorphism)

A blurred backdrop with a tinted overlay — the standard iOS / visionOS glass card.

```tsx
import { Canvas, Image, useImage, BackdropBlur, Fill, rrect, rect } from "@shopify/react-native-skia";

export const FrostedCard = ({ source }) => {
  const image = useImage(source);
  if (!image) return null;

  const card = rrect(rect(40, 200, 280, 220), 24, 24);

  return (
    <Canvas style={{ flex: 1 }}>
      <Image image={image} x={0} y={0} width={360} height={640} fit="cover" />
      <BackdropBlur blur={14} clip={card}>
        <Fill color="rgba(255,255,255,0.18)" />
      </BackdropBlur>
    </Canvas>
  );
};
```

For an outline, draw a stroked `<RoundedRect>` after the `<BackdropBlur>` with the same geometry and a low-opacity white color.

## Animated gradient background

A continuously-shifting linear gradient for splash screens and onboarding backgrounds.

```tsx
import { Canvas, Fill, LinearGradient, interpolateColors, vec } from "@shopify/react-native-skia";
import { useDerivedValue, useSharedValue, withRepeat, withTiming } from "react-native-reanimated";
import { useEffect } from "react";
import { useWindowDimensions } from "react-native";

const startPalette = ["#0F2027", "#203A43", "#2C5364"];
const endPalette   = ["#3E7CB1", "#DFB6B2", "#FFB996"];

export const AnimatedGradientBg = () => {
  const { width, height } = useWindowDimensions();
  const i = useSharedValue(0);

  useEffect(() => {
    i.value = withRepeat(withTiming(startPalette.length - 1, { duration: 6000 }), -1, true);
  }, []);

  const colors = useDerivedValue(() => [
    interpolateColors(i.value, [0, 1, 2], startPalette),
    interpolateColors(i.value, [0, 1, 2], endPalette),
  ]);

  return (
    <Canvas style={{ flex: 1 }}>
      <Fill>
        <LinearGradient start={vec(0, 0)} end={vec(width, height)} colors={colors} />
      </Fill>
    </Canvas>
  );
};
```

## Neon glow

Stack two `BlurMask`s (outer halo + inner glow) and a solid stroke on top.

```tsx
import { Canvas, Path, BlurMask, Skia } from "@shopify/react-native-skia";

const heart = Skia.Path.MakeFromSVGString(
  "M 100 30 C 130 0 180 20 180 60 C 180 100 100 160 100 160 C 100 160 20 100 20 60 C 20 20 70 0 100 30 Z"
)!;

export const NeonHeart = () => (
  <Canvas style={{ width: 200, height: 200 }}>
    {/* outer halo */}
    <Path path={heart} style="stroke" strokeWidth={4} color="#ff2d95">
      <BlurMask blur={20} style="solid" />
    </Path>
    {/* inner glow */}
    <Path path={heart} style="stroke" strokeWidth={2} color="#ffb8d8">
      <BlurMask blur={6} style="solid" />
    </Path>
    {/* core line */}
    <Path path={heart} style="stroke" strokeWidth={1.5} color="#ffffff" />
  </Canvas>
);
```

## Audio-reactive bars

Bars whose heights are driven by a shared value array. Plug in real audio amplitude data (e.g. from `@siteed/expo-audio-stream`) to make it react.

```tsx
import { Canvas, Rect, vec, LinearGradient } from "@shopify/react-native-skia";
import { useDerivedValue, useSharedValue, withRepeat, withTiming } from "react-native-reanimated";
import { useEffect } from "react";

const BAR_COUNT = 32;
const GAP = 4;

export const AudioBars = ({ width = 360, height = 120 }) => {
  const barWidth = (width - GAP * (BAR_COUNT - 1)) / BAR_COUNT;
  const phase = useSharedValue(0);

  useEffect(() => {
    phase.value = withRepeat(withTiming(Math.PI * 2, { duration: 2000 }), -1);
  }, []);

  return (
    <Canvas style={{ width, height }}>
      {Array.from({ length: BAR_COUNT }).map((_, i) => {
        const h = useDerivedValue(() => {
          const amp = Math.sin(phase.value + i * 0.3) * 0.5 + 0.5;
          return Math.max(8, amp * height);
        });
        const y = useDerivedValue(() => (height - h.value) / 2);
        return (
          <Rect
            key={i}
            x={i * (barWidth + GAP)}
            y={y}
            width={barWidth}
            height={h}
          >
            <LinearGradient
              start={vec(0, 0)}
              end={vec(0, height)}
              colors={["#3E7CB1", "#DFB6B2"]}
            />
          </Rect>
        );
      })}
    </Canvas>
  );
};
```

The `Array.from(...).map` with hooks inside is fine because `BAR_COUNT` is constant — React sees the same hook calls in the same order on every render.

## Tap ripple

A Material-style ripple expanding from the tap point.

```tsx
import { Canvas, Circle, Fill } from "@shopify/react-native-skia";
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import { useSharedValue, withTiming } from "react-native-reanimated";

const SIZE = 280;

export const RippleButton = () => {
  const cx = useSharedValue(SIZE / 2);
  const cy = useSharedValue(SIZE / 2);
  const r = useSharedValue(0);
  const opacity = useSharedValue(0);

  const tap = Gesture.Tap().onStart((e) => {
    cx.value = e.x;
    cy.value = e.y;
    r.value = 0;
    opacity.value = 0.4;
    r.value = withTiming(SIZE, { duration: 500 });
    opacity.value = withTiming(0, { duration: 500 });
  });

  return (
    <GestureDetector gesture={tap}>
      <Canvas style={{ width: SIZE, height: SIZE }}>
        <Fill color="#1F1F23" />
        <Circle cx={cx} cy={cy} r={r} color="rgba(255,255,255,0.5)" opacity={opacity} />
      </Canvas>
    </GestureDetector>
  );
};
```

## Stroke draw-in animation

A path that draws itself like a hand-written signature.

```tsx
import { Canvas, Path, Skia } from "@shopify/react-native-skia";
import { useSharedValue, withTiming, Easing } from "react-native-reanimated";
import { useEffect } from "react";

const signature = Skia.Path.MakeFromSVGString(
  "M 20 100 C 60 40 120 160 180 100 S 280 40 340 100"
)!;

export const SignatureDraw = () => {
  const end = useSharedValue(0);
  useEffect(() => {
    end.value = withTiming(1, { duration: 1500, easing: Easing.inOut(Easing.cubic) });
  }, []);
  return (
    <Canvas style={{ width: 360, height: 200 }}>
      <Path
        path={signature}
        style="stroke"
        strokeWidth={3}
        strokeCap="round"
        strokeJoin="round"
        color="#3E7CB1"
        end={end}
      />
    </Canvas>
  );
};
```

## Pinch-to-zoom image

Pan + pinch on a Skia image, with state living in shared values.

```tsx
import { Canvas, Image, useImage } from "@shopify/react-native-skia";
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import { useSharedValue, useDerivedValue } from "react-native-reanimated";
import { useWindowDimensions } from "react-native";

export const ZoomablePhoto = ({ source }) => {
  const { width, height } = useWindowDimensions();
  const image = useImage(source);

  const tx = useSharedValue(0);
  const ty = useSharedValue(0);
  const scale = useSharedValue(1);
  const savedScale = useSharedValue(1);

  const pan = Gesture.Pan().onChange((e) => {
    tx.value += e.changeX;
    ty.value += e.changeY;
  });

  const pinch = Gesture.Pinch()
    .onUpdate((e) => { scale.value = savedScale.value * e.scale; })
    .onEnd(() => { savedScale.value = scale.value; });

  const gesture = Gesture.Simultaneous(pan, pinch);

  const transform = useDerivedValue(() => [
    { translateX: tx.value },
    { translateY: ty.value },
    { scale: scale.value },
  ]);

  if (!image) return null;

  return (
    <GestureDetector gesture={gesture}>
      <Canvas style={{ flex: 1 }}>
        <Image
          image={image}
          x={0} y={0} width={width} height={height}
          fit="contain"
          transform={transform}
          origin={{ x: width / 2, y: height / 2 }}
        />
      </Canvas>
    </GestureDetector>
  );
};
```

## Mesh gradient (animated)

Driven by a fragment shader for smooth, painterly color blending — no pre-rendered images.

```tsx
import { Canvas, Fill, Shader, Skia, useClock, vec } from "@shopify/react-native-skia";
import { useDerivedValue } from "react-native-reanimated";
import { useWindowDimensions } from "react-native";

const source = Skia.RuntimeEffect.Make(`
uniform vec2  resolution;
uniform float t;

vec3 palette(float t) {
  vec3 a = vec3(0.5, 0.5, 0.5);
  vec3 b = vec3(0.5, 0.5, 0.5);
  vec3 c = vec3(1.0, 1.0, 1.0);
  vec3 d = vec3(0.263, 0.416, 0.557);
  return a + b * cos(6.28318 * (c * t + d));
}

vec4 main(vec2 pos) {
  vec2 uv = (pos * 2.0 - resolution) / resolution.y;
  vec3 col = vec3(0.0);
  for (float i = 0.0; i < 4.0; i++) {
    uv = fract(uv * 1.5) - 0.5;
    float d = length(uv) * exp(-length(uv));
    vec3 c = palette(length(uv) + i * 0.4 + t * 0.4);
    d = sin(d * 8.0 + t) / 8.0;
    d = abs(d);
    d = pow(0.01 / d, 1.2);
    col += c * d;
  }
  return vec4(col, 1.0);
}`)!;

export const MeshGradient = () => {
  const { width, height } = useWindowDimensions();
  const clock = useClock();
  const uniforms = useDerivedValue(() => ({
    resolution: vec(width, height),
    t: clock.value / 1000,
  }));

  return (
    <Canvas style={{ flex: 1 }}>
      <Fill>
        <Shader source={source} uniforms={uniforms} />
      </Fill>
    </Canvas>
  );
};
```

## Liquid wave progress

A wave that fills a container from bottom to top as `progress` increases — classic for water/charging indicators.

```tsx
import { Canvas, Path, Skia, Group, Circle, useClock } from "@shopify/react-native-skia";
import { useDerivedValue, useSharedValue, withTiming } from "react-native-reanimated";
import { useEffect, useMemo } from "react";

const SIZE = 200;

export const WaveProgress = ({ target = 0.6 }) => {
  const progress = useSharedValue(0);
  const clock = useClock();

  useEffect(() => {
    progress.value = withTiming(target, { duration: 1200 });
  }, [target]);

  const wave = useDerivedValue(() => {
    "worklet";
    const b = Skia.PathBuilder.Make();
    const amplitude = 6;
    const frequency = (2 * Math.PI) / 80;
    const phase = clock.value / 300;
    const baseY = SIZE - progress.value * SIZE;

    b.moveTo(-20, baseY);
    for (let x = -20; x <= SIZE + 20; x += 4) {
      const y = baseY + Math.sin(x * frequency + phase) * amplitude;
      b.lineTo(x, y);
    }
    b.lineTo(SIZE + 20, SIZE);
    b.lineTo(-20, SIZE);
    b.close();
    return b.build();
  });

  const clip = useMemo(
    () => Skia.PathBuilder.Make().addCircle(SIZE / 2, SIZE / 2, SIZE / 2).build(),
    []
  );

  return (
    <Canvas style={{ width: SIZE, height: SIZE }}>
      <Circle cx={SIZE / 2} cy={SIZE / 2} r={SIZE / 2} color="rgba(62,124,177,0.15)" />
      <Group clip={clip}>
        <Path path={wave} color="#3E7CB1" />
      </Group>
    </Canvas>
  );
};
```

## Notes on customization

These are starting points. To adapt:

- **Colors:** swap the hex strings; nothing else needs to change.
- **Sizing:** every recipe uses an explicit `size`/`width`/`height` at the top. Change one constant.
- **Easing / timing:** Reanimated's `Easing` module has the full set — `Easing.bezier(...)`, `Easing.elastic(...)`, `Easing.bounce`, etc.
- **Stop animations on unmount:** `withRepeat`s keep going even after unmount unless you set the shared value to a finite state in `useEffect`'s cleanup, or use `cancelAnimation(sharedValue)`.
- **Performance:** if a recipe with many shapes/elements feels janky on lower-end Android, look at `references/animations.md` § Performance heuristics.
