# Patterns & Recipes

Full, copy-pasteable recipes for common UI patterns. Each entry includes the pattern, when to use it, and the complete component. Use these as starting points and adapt to the codebase's design tokens and component conventions.

## Table of contents

1. Swipeable row (swipe to delete / reveal actions)
2. Bottom sheet (drag to open/close with snap)
3. Accordion (expand/collapse with measured height)
4. Animated tab bar (sliding indicator)
5. Parallax scroll header
6. FAB with sub-actions
7. Pull-to-refresh custom indicator
8. Skeleton shimmer loader
9. Shake on error
10. Animated counter (numeric tween)
11. Image carousel with snap
12. Long-press to drag

---

## 1. Swipeable row

Swipe horizontally to reveal a delete action; threshold-based commit.

```tsx
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, {
  useSharedValue, useAnimatedStyle, withSpring, withTiming, runOnJS,
} from 'react-native-reanimated';

const SWIPE_THRESHOLD = -80;
const FULL_DELETE = -200;

export function SwipeableRow({
  children,
  onDelete,
}: { children: React.ReactNode; onDelete: () => void }) {
  const translateX = useSharedValue(0);

  const pan = Gesture.Pan()
    .activeOffsetX([-15, 15])
    .failOffsetY([-12, 12])
    .onChange((e) => {
      // Only allow left-swipe; rubber-band on right
      translateX.value = Math.min(0, translateX.value + e.changeX);
    })
    .onEnd((e) => {
      if (translateX.value < FULL_DELETE) {
        translateX.value = withTiming(-400, { duration: 200 }, () => {
          runOnJS(onDelete)();
        });
      } else if (translateX.value < SWIPE_THRESHOLD) {
        translateX.value = withSpring(SWIPE_THRESHOLD);
      } else {
        translateX.value = withSpring(0);
      }
    });

  const rowStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }],
  }));

  const actionStyle = useAnimatedStyle(() => ({
    opacity: Math.min(1, -translateX.value / 80),
  }));

  return (
    <View style={{ position: 'relative' }}>
      <Animated.View style={[styles.deleteAction, actionStyle]}>
        <Text style={{ color: 'white' }}>Delete</Text>
      </Animated.View>
      <GestureDetector gesture={pan}>
        <Animated.View style={[styles.row, rowStyle]}>{children}</Animated.View>
      </GestureDetector>
    </View>
  );
}
```

Tune `SWIPE_THRESHOLD` (sticky-open position) and `FULL_DELETE` (auto-commit) to taste.

---

## 2. Bottom sheet

Drag from a partially-open state; snap to closed, half, or full. Worklet-driven; no third-party bottom-sheet library needed for the basic case.

```tsx
const { height: SCREEN_H } = Dimensions.get('window');
const SNAP_POINTS = [SCREEN_H, SCREEN_H * 0.5, 80]; // closed, half, peek

export function BottomSheet() {
  const translateY = useSharedValue(SNAP_POINTS[0]);
  const start = useSharedValue(SNAP_POINTS[0]);

  const snapTo = (targetIndex: number) => {
    'worklet';
    translateY.value = withSpring(SNAP_POINTS[targetIndex], { damping: 22, stiffness: 180 });
  };

  const pan = Gesture.Pan()
    .onBegin(() => { start.value = translateY.value; })
    .onUpdate((e) => {
      translateY.value = Math.max(SNAP_POINTS[2], start.value + e.translationY);
    })
    .onEnd((e) => {
      const projected = translateY.value + e.velocityY * 0.2;
      // Pick nearest snap point to projected position
      let nearest = 0;
      let minDist = Math.abs(projected - SNAP_POINTS[0]);
      for (let i = 1; i < SNAP_POINTS.length; i++) {
        const d = Math.abs(projected - SNAP_POINTS[i]);
        if (d < minDist) { minDist = d; nearest = i; }
      }
      snapTo(nearest);
    });

  const sheetStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: translateY.value }],
  }));

  return (
    <GestureDetector gesture={pan}>
      <Animated.View style={[styles.sheet, sheetStyle]}>
        <View style={styles.handle} />
        {/* content */}
      </Animated.View>
    </GestureDetector>
  );
}
```

The velocity-projected snap (`translateY + velocityY * 0.2`) is what gives bottom sheets their natural "flick-to-close" feel.

---

## 3. Accordion (expand/collapse)

Measure content height once; animate `height` on toggle. Pure CSS transition — no worklets needed.

```tsx
import { useState, useRef } from 'react';
import { LayoutChangeEvent } from 'react-native';

export function Accordion({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [contentHeight, setContentHeight] = useState(0);

  const onLayout = (e: LayoutChangeEvent) => {
    if (contentHeight === 0) setContentHeight(e.nativeEvent.layout.height);
  };

  return (
    <View>
      <Pressable onPress={() => setOpen(o => !o)}>
        <Text style={styles.header}>{title}</Text>
      </Pressable>
      <Animated.View
        style={{
          height: contentHeight ? (open ? contentHeight : 0) : undefined,
          overflow: 'hidden',
          transitionProperty: 'height',
          transitionDuration: 240,
          transitionTimingFunction: 'ease-out',
        }}
      >
        <View onLayout={onLayout}>{children}</View>
      </Animated.View>
    </View>
  );
}
```

The `contentHeight === 0` check lets the content render at natural height on first mount so we can measure it; subsequent renders use the measured value.

---

## 4. Animated tab bar with sliding indicator

```tsx
export function TabBar({
  tabs, active, onChange,
}: { tabs: string[]; active: number; onChange: (i: number) => void }) {
  const indicatorX = useSharedValue(0);
  const tabWidth = useSharedValue(0);

  useEffect(() => {
    indicatorX.value = withSpring(active * tabWidth.value, { damping: 22, stiffness: 200 });
  }, [active]);

  const indicatorStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: indicatorX.value }],
    width: tabWidth.value,
  }));

  return (
    <View
      style={styles.tabBar}
      onLayout={(e) => { tabWidth.value = e.nativeEvent.layout.width / tabs.length; }}
    >
      {tabs.map((tab, i) => (
        <Pressable key={tab} onPress={() => onChange(i)} style={styles.tab}>
          <Text style={{ color: i === active ? '#1d4ed8' : '#64748b' }}>{tab}</Text>
        </Pressable>
      ))}
      <Animated.View style={[styles.indicator, indicatorStyle]} />
    </View>
  );
}
```

---

## 5. Parallax scroll header

Header shrinks and a hero image translates as the user scrolls.

```tsx
const HEADER_MAX = 280;
const HEADER_MIN = 80;

export function ParallaxScreen() {
  const scrollRef = useAnimatedRef<Animated.ScrollView>();
  const scrollY = useScrollOffset(scrollRef);

  const headerStyle = useAnimatedStyle(() => ({
    height: interpolate(
      scrollY.value,
      [0, HEADER_MAX - HEADER_MIN],
      [HEADER_MAX, HEADER_MIN],
      Extrapolation.CLAMP,
    ),
  }));

  const heroStyle = useAnimatedStyle(() => ({
    opacity: interpolate(
      scrollY.value,
      [0, HEADER_MAX - HEADER_MIN],
      [1, 0],
      Extrapolation.CLAMP,
    ),
    transform: [{
      translateY: interpolate(
        scrollY.value,
        [0, HEADER_MAX - HEADER_MIN],
        [0, -40],
      ),
    }],
  }));

  const titleStyle = useAnimatedStyle(() => ({
    fontSize: interpolate(
      scrollY.value,
      [0, HEADER_MAX - HEADER_MIN],
      [28, 17],
      Extrapolation.CLAMP,
    ),
  }));

  return (
    <View style={{ flex: 1 }}>
      <Animated.View style={[styles.header, headerStyle]}>
        <Animated.Image source={hero} style={[styles.hero, heroStyle]} />
        <Animated.Text style={[styles.title, titleStyle]}>Title</Animated.Text>
      </Animated.View>
      <Animated.ScrollView
        ref={scrollRef}
        scrollEventThrottle={16}
        contentContainerStyle={{ paddingTop: HEADER_MAX }}
      >
        {/* body */}
      </Animated.ScrollView>
    </View>
  );
}
```

---

## 6. FAB with sub-actions

Tap the FAB; sub-actions arc out. CSS transition friendly because the state is binary.

```tsx
export function FAB() {
  const [open, setOpen] = useState(false);
  const subs = [
    { icon: 'image', angle: -90 },
    { icon: 'video', angle: -135 },
    { icon: 'mic', angle: -180 },
  ];

  return (
    <View style={styles.fabContainer}>
      {subs.map((sub, i) => {
        const rad = (sub.angle * Math.PI) / 180;
        const x = open ? Math.cos(rad) * 70 : 0;
        const y = open ? Math.sin(rad) * 70 : 0;
        return (
          <Animated.View
            key={sub.icon}
            style={{
              position: 'absolute',
              opacity: open ? 1 : 0,
              transform: [{ translateX: x }, { translateY: y }, { scale: open ? 1 : 0.3 }],
              transitionProperty: ['opacity', 'transform'],
              transitionDuration: 220,
              transitionDelay: open ? i * 30 : 0,
              transitionTimingFunction: 'ease-out',
            }}
          >
            <Pressable style={styles.subFab}>
              <Icon name={sub.icon} />
            </Pressable>
          </Animated.View>
        );
      })}
      <Pressable onPress={() => setOpen(o => !o)} style={styles.fab}>
        <Animated.View style={{
          transform: [{ rotate: open ? '45deg' : '0deg' }],
          transitionProperty: 'transform',
          transitionDuration: 200,
        }}>
          <Icon name="plus" />
        </Animated.View>
      </Pressable>
    </View>
  );
}
```

This pattern showcases CSS transitions at their best — three transitioning properties, staggered delay, zero worklets.

---

## 7. Pull-to-refresh custom indicator

A custom indicator that rotates as you pull and triggers refresh when threshold is crossed.

```tsx
const PULL_THRESHOLD = 80;

export function PullableList({ onRefresh }: { onRefresh: () => Promise<void> }) {
  const scrollRef = useAnimatedRef<Animated.ScrollView>();
  const scrollY = useScrollOffset(scrollRef);
  const [refreshing, setRefreshing] = useState(false);

  useAnimatedReaction(
    () => scrollY.value < -PULL_THRESHOLD,
    (passed, prev) => {
      if (passed && !prev) {
        runOnJS(setRefreshing)(true);
        runOnJS(triggerRefresh)();
      }
    },
  );

  const triggerRefresh = async () => {
    await onRefresh();
    setRefreshing(false);
  };

  const indicatorStyle = useAnimatedStyle(() => ({
    opacity: interpolate(scrollY.value, [-PULL_THRESHOLD, 0], [1, 0], Extrapolation.CLAMP),
    transform: [{
      rotate: `${interpolate(scrollY.value, [-PULL_THRESHOLD, 0], [180, 0], Extrapolation.CLAMP)}deg`,
    }],
  }));

  return (
    <View>
      <Animated.View style={[styles.pullIndicator, indicatorStyle]}>
        <Icon name="arrow-down" />
      </Animated.View>
      <Animated.ScrollView ref={scrollRef} scrollEventThrottle={16}>
        {/* content */}
      </Animated.ScrollView>
    </View>
  );
}
```

---

## 8. Skeleton shimmer loader

CSS animation, no worklets.

```tsx
const shimmer: CSSAnimationKeyframes = {
  '0%':   { transform: [{ translateX: -300 }] },
  '100%': { transform: [{ translateX: 300 }] },
};

export function Skeleton({ width, height }: { width: number; height: number }) {
  return (
    <View style={{ width, height, backgroundColor: '#e2e8f0', overflow: 'hidden', borderRadius: 8 }}>
      <Animated.View
        style={{
          width: '60%',
          height: '100%',
          backgroundColor: 'rgba(255,255,255,0.6)',
          animationName: shimmer,
          animationDuration: 1400,
          animationIterationCount: 'infinite',
          animationTimingFunction: 'ease-in-out',
        }}
      />
    </View>
  );
}
```

For multi-line skeletons, stack several with different widths and a small `animationDelay` for staggered shimmer.

---

## 9. Shake on error

CSS keyframe — fire once per error event by toggling the key.

```tsx
const shake: CSSAnimationKeyframes = {
  '0%':   { transform: [{ translateX: 0 }] },
  '20%':  { transform: [{ translateX: -8 }] },
  '40%':  { transform: [{ translateX: 8 }] },
  '60%':  { transform: [{ translateX: -6 }] },
  '80%':  { transform: [{ translateX: 6 }] },
  '100%': { transform: [{ translateX: 0 }] },
};

export function ShakeableField({ error, children }: { error: string | null; children: React.ReactNode }) {
  const [shakeKey, setShakeKey] = useState(0);
  useEffect(() => { if (error) setShakeKey(k => k + 1); }, [error]);
  return (
    <Animated.View
      key={shakeKey}
      style={{ animationName: shake, animationDuration: 360 }}
    >
      {children}
    </Animated.View>
  );
}
```

Bumping `key` remounts the view so the one-shot animation re-fires. Cheap and reliable.

---

## 10. Animated counter

Numeric value tweens on change. Useful for stats, prices, scores.

```tsx
import Animated, { useSharedValue, useAnimatedProps, withTiming } from 'react-native-reanimated';
import { TextInput } from 'react-native';

const AnimatedTextInput = Animated.createAnimatedComponent(TextInput);

export function AnimatedCounter({ value }: { value: number }) {
  const progress = useSharedValue(value);
  useEffect(() => { progress.value = withTiming(value, { duration: 600 }); }, [value]);

  const animatedProps = useAnimatedProps(() => ({
    text: `${Math.round(progress.value).toLocaleString()}`,
    defaultValue: `${Math.round(progress.value)}`,
  }) as any);

  return (
    <AnimatedTextInput
      editable={false}
      style={styles.counter}
      animatedProps={animatedProps}
    />
  );
}
```

`TextInput` is used (not `Text`) because its `text` prop is updatable via `useAnimatedProps`. The `as any` is needed because `text` isn't in `TextInput`'s public type — this is the standard workaround.

---

## 11. Image carousel with snap

ScrollView with paging + an indicator that follows scroll position.

```tsx
const ITEM_W = Dimensions.get('window').width;

export function Carousel({ images }: { images: string[] }) {
  const scrollRef = useAnimatedRef<Animated.ScrollView>();
  const scrollX = useScrollOffset(scrollRef);

  return (
    <View>
      <Animated.ScrollView
        ref={scrollRef}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        scrollEventThrottle={16}
      >
        {images.map((uri) => (
          <Image key={uri} source={{ uri }} style={{ width: ITEM_W, height: 240 }} />
        ))}
      </Animated.ScrollView>
      <View style={styles.dots}>
        {images.map((_, i) => (
          <Dot key={i} index={i} scrollX={scrollX} />
        ))}
      </View>
    </View>
  );
}

function Dot({ index, scrollX }: { index: number; scrollX: SharedValue<number> }) {
  const style = useAnimatedStyle(() => {
    const distance = Math.abs(scrollX.value / ITEM_W - index);
    return {
      width: interpolate(distance, [0, 1], [24, 8], Extrapolation.CLAMP),
      opacity: interpolate(distance, [0, 1], [1, 0.4], Extrapolation.CLAMP),
    };
  });
  return <Animated.View style={[styles.dot, style]} />;
}
```

The active dot widens and brightens based on scroll proximity. Looks polished for very little code.

---

## 12. Long-press to drag

A LongPress activates a Pan. The card lifts on activation (scale + shadow) and follows the finger.

```tsx
export function DraggableCard() {
  const x = useSharedValue(0);
  const y = useSharedValue(0);
  const isActive = useSharedValue(false);

  const long = Gesture.LongPress()
    .minDuration(250)
    .onStart(() => { isActive.value = true; });

  const pan = Gesture.Pan()
    .manualActivation(true) // only activate via long-press chain
    .onTouchesMove((_e, state) => {
      if (isActive.value) state.activate();
    })
    .onChange((e) => {
      x.value += e.changeX;
      y.value += e.changeY;
    })
    .onEnd(() => {
      isActive.value = false;
      x.value = withSpring(0);
      y.value = withSpring(0);
    });

  const gesture = Gesture.Simultaneous(long, pan);

  const style = useAnimatedStyle(() => ({
    transform: [
      { translateX: x.value },
      { translateY: y.value },
      { scale: withSpring(isActive.value ? 1.08 : 1) },
    ],
    shadowOpacity: withSpring(isActive.value ? 0.3 : 0.1),
    shadowRadius: withSpring(isActive.value ? 12 : 4),
    zIndex: isActive.value ? 999 : 1,
  }));

  return (
    <GestureDetector gesture={gesture}>
      <Animated.View style={[styles.card, style]} />
    </GestureDetector>
  );
}
```

Note: nesting `withSpring` inside `useAnimatedStyle` is fine for transient effects keyed off boolean shared values — Reanimated handles the interpolation each time the boolean flips.
