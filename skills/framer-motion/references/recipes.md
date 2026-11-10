# Animation Recipes

Copy-paste patterns for common needs. Each recipe is production-ready with the defaults reasoned through in `design-principles.md` and the API choices from `motion-react.md` or `reanimated.md`.

## Table of contents

**Microinteractions**
1. Hover-lift card
2. Press-in button
3. Animated toggle switch
4. Hover-tilt card (mouse parallax)
5. Animated counter
6. Magnetic CTA button

**Page & route transitions**
7. Next.js App Router page transitions (fade)
8. Next.js App Router page transitions (slide)
9. Tab content crossfade

**Scroll-linked**
10. Scroll progress bar
11. Reveal-on-scroll list
12. Parallax hero
13. Scroll-driven hero sequence (Apple-style)

**Layout**
14. Magic move (shared element)
15. Drag-to-reorder list
16. List item reorder (without drag)
17. Expanding/collapsing card

**SVG**
18. Animated path draw-in
19. Animated icon morph (menu ↔ close)
20. Animated logo reveal

**Modal & sheet**
21. Modal with backdrop
22. Bottom sheet (mobile, swipe-to-dismiss)

**Reanimated-specific**
23. Swipe-to-delete row
24. Pinch-to-zoom image
25. Pull-to-refresh

---

## Microinteractions

### 1. Hover-lift card

```tsx
"use client";
import { motion } from "motion/react";

<motion.div
  className="rounded-2xl bg-card p-6 shadow-sm cursor-pointer"
  whileHover={{ y: -4, boxShadow: "0 12px 32px -8px rgb(0 0 0 / 0.15)" }}
  whileTap={{ scale: 0.99 }}
  transition={{ type: "spring", stiffness: 400, damping: 30 }}
>
  {children}
</motion.div>
```

### 2. Press-in button

```tsx
"use client";
import { motion } from "motion/react";

<motion.button
  className="px-5 py-3 rounded-xl bg-primary text-primary-foreground font-medium"
  whileHover={{ scale: 1.03 }}
  whileTap={{ scale: 0.96 }}
  transition={{ type: "spring", stiffness: 500, damping: 25 }}
>
  {label}
</motion.button>
```

### 3. Animated toggle switch

```tsx
"use client";
import { motion } from "motion/react";

function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className={`relative h-7 w-12 rounded-full transition-colors ${on ? "bg-primary" : "bg-muted"}`}
    >
      <motion.span
        className="absolute top-1 left-1 h-5 w-5 rounded-full bg-white shadow-md"
        animate={{ x: on ? 20 : 0 }}
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
      />
    </button>
  );
}
```

### 4. Hover-tilt card (mouse parallax)

```tsx
"use client";
import { motion, useMotionValue, useTransform, useSpring } from "motion/react";

function TiltCard({ children }: { children: React.ReactNode }) {
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const rotateX = useSpring(useTransform(y, [-150, 150], [10, -10]), { stiffness: 200, damping: 20 });
  const rotateY = useSpring(useTransform(x, [-150, 150], [-10, 10]), { stiffness: 200, damping: 20 });

  return (
    <motion.div
      onMouseMove={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        x.set(e.clientX - rect.left - rect.width / 2);
        y.set(e.clientY - rect.top - rect.height / 2);
      }}
      onMouseLeave={() => { x.set(0); y.set(0); }}
      style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
      className="rounded-2xl bg-card p-8"
    >
      <div style={{ transform: "translateZ(40px)" }}>{children}</div>
    </motion.div>
  );
}
```

### 5. Animated counter

```tsx
"use client";
import { useEffect } from "react";
import { motion, useMotionValue, useTransform, animate } from "motion/react";

function Counter({ to, duration = 1.2 }: { to: number; duration?: number }) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (v) => Math.round(v).toLocaleString());

  useEffect(() => {
    const controls = animate(count, to, { duration, ease: [0.32, 0.72, 0, 1] });
    return controls.stop;
  }, [to, duration, count]);

  return <motion.span>{rounded}</motion.span>;
}
```

### 6. Magnetic CTA button

```tsx
"use client";
import { useRef } from "react";
import { motion, useMotionValue, useSpring } from "motion/react";

function MagneticButton({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLButtonElement>(null);
  const x = useSpring(useMotionValue(0), { stiffness: 300, damping: 20 });
  const y = useSpring(useMotionValue(0), { stiffness: 300, damping: 20 });

  return (
    <motion.button
      ref={ref}
      style={{ x, y }}
      onMouseMove={(e) => {
        const rect = ref.current!.getBoundingClientRect();
        const relX = e.clientX - rect.left - rect.width / 2;
        const relY = e.clientY - rect.top - rect.height / 2;
        x.set(relX * 0.3);
        y.set(relY * 0.3);
      }}
      onMouseLeave={() => { x.set(0); y.set(0); }}
      className="px-6 py-3 rounded-full bg-primary text-primary-foreground"
    >
      {children}
    </motion.button>
  );
}
```

---

## Page & route transitions

### 7. Next.js App Router page transitions (fade)

```tsx
// app/template.tsx — runs on every navigation
"use client";
import { motion } from "motion/react";

export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.32, ease: [0.32, 0.72, 0, 1] }}
    >
      {children}
    </motion.div>
  );
}
```

`template.tsx` (not `layout.tsx`) re-mounts on every navigation, which is what makes this work without `AnimatePresence`.

### 8. Next.js App Router page transitions (slide)

For directional transitions (forward = slide left, back = slide right), use AnimatePresence with the pathname as key:

```tsx
// app/layout.tsx
"use client";
import { AnimatePresence, motion } from "motion/react";
import { usePathname } from "next/navigation";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <html>
      <body>
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={pathname}
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -24 }}
            transition={{ type: "spring", stiffness: 260, damping: 30 }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </body>
    </html>
  );
}
```

### 9. Tab content crossfade

```tsx
"use client";
import { AnimatePresence, motion } from "motion/react";

function Tabs({ active, panels }: { active: string; panels: Record<string, React.ReactNode> }) {
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={active}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -4 }}
        transition={{ duration: 0.18 }}
      >
        {panels[active]}
      </motion.div>
    </AnimatePresence>
  );
}
```

---

## Scroll-linked

### 10. Scroll progress bar

```tsx
"use client";
import { motion, useScroll, useSpring } from "motion/react";

export function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 100, damping: 30, restDelta: 0.001 });
  return (
    <motion.div
      style={{ scaleX, transformOrigin: "0%" }}
      className="fixed top-0 left-0 right-0 h-0.5 bg-primary z-50"
    />
  );
}
```

### 11. Reveal-on-scroll list

```tsx
"use client";
import { motion } from "motion/react";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
};
const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 200, damping: 24 } },
};

<motion.ul
  variants={container}
  initial="hidden"
  whileInView="show"
  viewport={{ once: true, amount: 0.3 }}
  className="space-y-4"
>
  {items.map((i) => (
    <motion.li key={i.id} variants={item}>{i.content}</motion.li>
  ))}
</motion.ul>
```

### 12. Parallax hero

```tsx
"use client";
import { useRef } from "react";
import { motion, useScroll, useTransform } from "motion/react";

function ParallaxHero({ image, children }: { image: string; children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);
  const opacity = useTransform(scrollYProgress, [0, 1], [1, 0.4]);

  return (
    <section ref={ref} className="relative h-screen overflow-hidden">
      <motion.div
        style={{ y, backgroundImage: `url(${image})` }}
        className="absolute inset-0 bg-cover bg-center -inset-y-1/4"
      />
      <motion.div style={{ opacity }} className="relative z-10 flex h-full items-center justify-center">
        {children}
      </motion.div>
    </section>
  );
}
```

**Half the scroll distance is plenty.** A 50–60% parallax offset feels rich; 100%+ feels disorienting.

### 13. Scroll-driven hero sequence (Apple-style)

A pinned section where multiple states animate as the user scrolls through.

```tsx
"use client";
import { useRef } from "react";
import { motion, useScroll, useTransform } from "motion/react";

function ScrollSequence() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end end"] });

  // Three "scenes" — 0–0.33, 0.33–0.66, 0.66–1
  const scene1Opacity = useTransform(scrollYProgress, [0, 0.2, 0.33], [1, 1, 0]);
  const scene2Opacity = useTransform(scrollYProgress, [0.33, 0.5, 0.66], [0, 1, 0]);
  const scene3Opacity = useTransform(scrollYProgress, [0.66, 0.85, 1], [0, 1, 1]);

  const scale = useTransform(scrollYProgress, [0, 1], [1, 1.3]);

  return (
    <section ref={ref} className="relative h-[300vh]">
      <div className="sticky top-0 h-screen flex items-center justify-center overflow-hidden">
        <motion.div style={{ scale, opacity: scene1Opacity }} className="absolute"><Scene1 /></motion.div>
        <motion.div style={{ opacity: scene2Opacity }} className="absolute"><Scene2 /></motion.div>
        <motion.div style={{ opacity: scene3Opacity }} className="absolute"><Scene3 /></motion.div>
      </div>
    </section>
  );
}
```

The outer section is 3x the viewport height; the inner content is pinned at `sticky top-0 h-screen` and animates based on scroll progress through the outer.

---

## Layout

### 14. Magic move (shared element)

```tsx
"use client";
import { useState } from "react";
import { motion, AnimatePresence, LayoutGroup } from "motion/react";

function Gallery({ items }: { items: { id: string; image: string }[] }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = items.find((i) => i.id === selectedId);

  return (
    <LayoutGroup>
      <div className="grid grid-cols-3 gap-4">
        {items.map((item) => (
          <motion.div
            key={item.id}
            layoutId={`card-${item.id}`}
            onClick={() => setSelectedId(item.id)}
            className="aspect-square rounded-xl bg-cover bg-center cursor-pointer"
            style={{ backgroundImage: `url(${item.image})` }}
          />
        ))}
      </div>

      <AnimatePresence>
        {selected && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSelectedId(null)}
          >
            <motion.div
              layoutId={`card-${selected.id}`}
              className="max-w-3xl w-full aspect-video rounded-2xl bg-cover bg-center"
              style={{ backgroundImage: `url(${selected.image})` }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </LayoutGroup>
  );
}
```

### 15. Drag-to-reorder list

```tsx
"use client";
import { Reorder, motion } from "motion/react";
import { useState } from "react";

export function ReorderList() {
  const [items, setItems] = useState([
    { id: "1", label: "First" },
    { id: "2", label: "Second" },
    { id: "3", label: "Third" },
  ]);

  return (
    <Reorder.Group axis="y" values={items} onReorder={setItems} className="space-y-2">
      {items.map((item) => (
        <Reorder.Item
          key={item.id}
          value={item}
          className="rounded-xl bg-card p-4 cursor-grab active:cursor-grabbing"
          whileDrag={{ scale: 1.02, boxShadow: "0 12px 24px -8px rgb(0 0 0 / 0.2)" }}
        >
          {item.label}
        </Reorder.Item>
      ))}
    </Reorder.Group>
  );
}
```

### 16. List item reorder (without drag)

Items shuffle to new positions when the underlying array reorders. Animate the layout change:

```tsx
"use client";
import { motion, AnimatePresence } from "motion/react";

function FilteredList({ items }: { items: { id: string; label: string }[] }) {
  return (
    <ul className="space-y-2">
      <AnimatePresence mode="popLayout">
        {items.map((item) => (
          <motion.li
            key={item.id}
            layout
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.96 }}
            transition={{ type: "spring", stiffness: 350, damping: 30 }}
            className="rounded-xl bg-card p-4"
          >
            {item.label}
          </motion.li>
        ))}
      </AnimatePresence>
    </ul>
  );
}
```

`mode="popLayout"` is critical — it removes exiting items from the layout flow so siblings reflow immediately, which makes the magic look right.

### 17. Expanding/collapsing card

```tsx
"use client";
import { useState } from "react";
import { motion } from "motion/react";

function ExpandingCard({ summary, detail }: { summary: React.ReactNode; detail: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <motion.div
      layout
      onClick={() => setOpen(!open)}
      className="rounded-2xl bg-card p-6 cursor-pointer overflow-hidden"
      transition={{ layout: { type: "spring", stiffness: 300, damping: 32 } }}
    >
      <motion.div layout="position">{summary}</motion.div>
      {open && (
        <motion.div
          layout
          initial={{ opacity: 0 }}
          animate={{ opacity: 1, transition: { delay: 0.1 } }}
          className="mt-4"
        >
          {detail}
        </motion.div>
      )}
    </motion.div>
  );
}
```

`layout="position"` on the summary prevents it from stretching during the animation.

---

## SVG

### 18. Animated path draw-in

```tsx
"use client";
import { motion } from "motion/react";

<svg viewBox="0 0 200 200" className="w-48 h-48">
  <motion.path
    d="M 20 100 Q 100 20, 180 100 T 340 100"
    fill="none"
    stroke="currentColor"
    strokeWidth={3}
    strokeLinecap="round"
    initial={{ pathLength: 0 }}
    animate={{ pathLength: 1 }}
    transition={{ duration: 1.5, ease: "easeInOut" }}
  />
</svg>
```

For a "drawing" check or signature, animate `pathLength` 0 → 1. For an "erasing" effect, animate `pathOffset` 0 → 1 (or both for a moving dash).

### 19. Animated icon morph (menu ↔ close)

```tsx
"use client";
import { motion } from "motion/react";

function MenuIcon({ open }: { open: boolean }) {
  return (
    <svg viewBox="0 0 24 24" className="w-6 h-6">
      <motion.line
        x1="3" x2="21" y1="6" y2="6"
        stroke="currentColor" strokeWidth="2" strokeLinecap="round"
        animate={open ? { rotate: 45, y1: 12, y2: 12 } : { rotate: 0, y1: 6, y2: 6 }}
        style={{ originX: "12px", originY: "12px" }}
        transition={{ type: "spring", stiffness: 400, damping: 28 }}
      />
      <motion.line
        x1="3" x2="21" y1="12" y2="12"
        stroke="currentColor" strokeWidth="2" strokeLinecap="round"
        animate={open ? { opacity: 0 } : { opacity: 1 }}
        transition={{ duration: 0.15 }}
      />
      <motion.line
        x1="3" x2="21" y1="18" y2="18"
        stroke="currentColor" strokeWidth="2" strokeLinecap="round"
        animate={open ? { rotate: -45, y1: 12, y2: 12 } : { rotate: 0, y1: 18, y2: 18 }}
        style={{ originX: "12px", originY: "12px" }}
        transition={{ type: "spring", stiffness: 400, damping: 28 }}
      />
    </svg>
  );
}
```

### 20. Animated logo reveal

Stagger path strokes across the logo:

```tsx
"use client";
import { motion } from "motion/react";

const draw = {
  hidden: { pathLength: 0, opacity: 0 },
  visible: (i: number) => ({
    pathLength: 1,
    opacity: 1,
    transition: {
      pathLength: { delay: i * 0.2, type: "spring", duration: 1.5, bounce: 0 },
      opacity: { delay: i * 0.2, duration: 0.01 },
    },
  }),
};

<motion.svg viewBox="0 0 400 200" initial="hidden" animate="visible">
  <motion.path d="M 50 100 L 150 50" custom={0} variants={draw} stroke="currentColor" fill="none" strokeWidth={4} />
  <motion.path d="M 150 50 L 250 150" custom={1} variants={draw} stroke="currentColor" fill="none" strokeWidth={4} />
  <motion.path d="M 250 150 L 350 100" custom={2} variants={draw} stroke="currentColor" fill="none" strokeWidth={4} />
</motion.svg>
```

---

## Modal & sheet

### 21. Modal with backdrop

```tsx
"use client";
import { AnimatePresence, motion } from "motion/react";

function Modal({ open, onClose, children }: { open: boolean; onClose: () => void; children: React.ReactNode }) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: 4 }}
            transition={{ type: "spring", stiffness: 320, damping: 28 }}
            role="dialog" aria-modal="true"
            className="fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2 w-full max-w-md rounded-2xl bg-card p-6 shadow-xl"
          >
            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

**Focus management note:** focus the first focusable element after mount; on close, restore focus to the trigger that opened the modal. Don't wait for the animation to finish.

### 22. Bottom sheet (mobile, swipe-to-dismiss)

```tsx
"use client";
import { motion, AnimatePresence, useMotionValue, useTransform } from "motion/react";

function BottomSheet({ open, onClose, children }: { open: boolean; onClose: () => void; children: React.ReactNode }) {
  const y = useMotionValue(0);
  const opacity = useTransform(y, [0, 300], [1, 0]);

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            style={{ opacity }}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/50"
          />
          <motion.div
            style={{ y }}
            drag="y" dragConstraints={{ top: 0, bottom: 0 }} dragElastic={{ top: 0, bottom: 0.4 }}
            onDragEnd={(_, info) => { if (info.offset.y > 100 || info.velocity.y > 500) onClose(); }}
            initial={{ y: "100%" }} animate={{ y: 0 }} exit={{ y: "100%" }}
            transition={{ type: "spring", stiffness: 280, damping: 30 }}
            className="fixed bottom-0 inset-x-0 z-50 rounded-t-3xl bg-card pt-2 pb-8 px-6"
          >
            <div className="mx-auto mb-4 h-1.5 w-10 rounded-full bg-muted" />
            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

---

## Reanimated-specific

### 23. Swipe-to-delete row

```tsx
import Animated, { useSharedValue, useAnimatedStyle, withSpring, withTiming, runOnJS } from "react-native-reanimated";
import { Gesture, GestureDetector } from "react-native-gesture-handler";

function SwipeRow({ children, onDelete }: { children: React.ReactNode; onDelete: () => void }) {
  const tx = useSharedValue(0);
  const height = useSharedValue(64);

  const pan = Gesture.Pan()
    .activeOffsetX([-10, 10])
    .onUpdate((e) => { tx.value = Math.min(0, e.translationX); })
    .onEnd((e) => {
      if (e.translationX < -100) {
        tx.value = withTiming(-400, { duration: 200 });
        height.value = withTiming(0, { duration: 200 }, () => runOnJS(onDelete)());
      } else {
        tx.value = withSpring(0);
      }
    });

  const style = useAnimatedStyle(() => ({
    transform: [{ translateX: tx.value }],
    height: height.value,
  }));

  return (
    <GestureDetector gesture={pan}>
      <Animated.View style={[{ overflow: "hidden" }, style]}>{children}</Animated.View>
    </GestureDetector>
  );
}
```

### 24. Pinch-to-zoom image

```tsx
import Animated, { useSharedValue, useAnimatedStyle, withSpring } from "react-native-reanimated";
import { Gesture, GestureDetector } from "react-native-gesture-handler";

function ZoomableImage({ source }: { source: any }) {
  const scale = useSharedValue(1);
  const savedScale = useSharedValue(1);
  const tx = useSharedValue(0);
  const ty = useSharedValue(0);
  const savedTx = useSharedValue(0);
  const savedTy = useSharedValue(0);

  const pinch = Gesture.Pinch()
    .onUpdate((e) => { scale.value = savedScale.value * e.scale; })
    .onEnd(() => {
      savedScale.value = scale.value;
      if (scale.value < 1) {
        scale.value = withSpring(1);
        savedScale.value = 1;
        tx.value = withSpring(0); ty.value = withSpring(0);
        savedTx.value = 0; savedTy.value = 0;
      }
    });

  const pan = Gesture.Pan()
    .onUpdate((e) => {
      tx.value = savedTx.value + e.translationX;
      ty.value = savedTy.value + e.translationY;
    })
    .onEnd(() => { savedTx.value = tx.value; savedTy.value = ty.value; });

  const composed = Gesture.Simultaneous(pinch, pan);

  const style = useAnimatedStyle(() => ({
    transform: [{ translateX: tx.value }, { translateY: ty.value }, { scale: scale.value }],
  }));

  return (
    <GestureDetector gesture={composed}>
      <Animated.Image source={source} style={[{ width: "100%", height: "100%" }, style]} resizeMode="contain" />
    </GestureDetector>
  );
}
```

### 25. Pull-to-refresh

For a custom pull-to-refresh (when `RefreshControl` doesn't fit the design):

```tsx
import Animated, {
  useAnimatedScrollHandler, useSharedValue, useAnimatedStyle,
  interpolate, Extrapolation, withSpring, runOnJS,
} from "react-native-reanimated";

function CustomRefreshList({ onRefresh, children }: { onRefresh: () => Promise<void>; children: React.ReactNode }) {
  const scrollY = useSharedValue(0);
  const refreshing = useSharedValue(false);

  const scrollHandler = useAnimatedScrollHandler({
    onScroll: (e) => { scrollY.value = e.contentOffset.y; },
    onEndDrag: (e) => {
      if (e.contentOffset.y < -80 && !refreshing.value) {
        refreshing.value = true;
        runOnJS(onRefresh)().then(() => { refreshing.value = false; });
      }
    },
  });

  const indicatorStyle = useAnimatedStyle(() => ({
    opacity: interpolate(scrollY.value, [-80, 0], [1, 0], Extrapolation.CLAMP),
    transform: [{
      rotate: `${interpolate(scrollY.value, [-120, 0], [360, 0], Extrapolation.CLAMP)}deg`,
    }],
  }));

  return (
    <>
      <Animated.View style={[styles.indicator, indicatorStyle]}>{/* spinner */}</Animated.View>
      <Animated.ScrollView onScroll={scrollHandler} scrollEventThrottle={16}>
        {children}
      </Animated.ScrollView>
    </>
  );
}
```
