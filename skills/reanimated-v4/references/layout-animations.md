# Layout Animations

Layout animations handle the lifecycle of view appearance and position: a component mounting, unmounting, or shifting because of surrounding changes. They're declarative — you attach `entering`, `exiting`, or `layout` props on `Animated.View` and the library handles the rest.

This layer covers most cases that aren't gestures or scroll-driven motion and aren't simple CSS-style transitions. The most common use is animating list items: things appearing in a feed, removed from a todo list, reordering after a sort.

## When to use this layer

- An item appears in a list and you want it to slide/fade in
- An item is removed and you want it to fade/slide out before vanishing
- The order or position of items changes and you want surrounding items to animate to their new spots
- A modal/sheet/toast mounts and unmounts and you want a tasteful enter/exit

Don't use this for state toggles within a stable component (use CSS transitions) or anything driven by a gesture (use worklets).

## Three props on `Animated.View`

```tsx
<Animated.View
  entering={FadeIn.duration(200)}    // when the view is added
  exiting={FadeOut.duration(150)}    // when the view is removed
  layout={LinearTransition.springify()} // when its layout position changes
/>
```

All three are optional. Combine them as needed.

## Entering animations

Presets, all importable from `react-native-reanimated`. Each has standard chainable modifiers.

### Common presets

- **Fade family**: `FadeIn`, `FadeInUp`, `FadeInDown`, `FadeInLeft`, `FadeInRight`
- **Slide family**: `SlideInUp`, `SlideInDown`, `SlideInLeft`, `SlideInRight`
- **Zoom family**: `ZoomIn`, `ZoomInRotate`, `ZoomInEasyDown`, `ZoomInEasyUp`, `ZoomInLeft`, `ZoomInRight`, `ZoomInDown`, `ZoomInUp`
- **Bounce family**: `BounceIn`, `BounceInUp`, `BounceInDown`, `BounceInLeft`, `BounceInRight`
- **Flip family**: `FlipInEasyX`, `FlipInEasyY`, `FlipInXDown`, `FlipInXUp`, `FlipInYLeft`, `FlipInYRight`
- **Stretch family**: `StretchInX`, `StretchInY`
- **Rotate family**: `RotateInDownLeft`, `RotateInDownRight`, `RotateInUpLeft`, `RotateInUpRight`
- **Light speed**: `LightSpeedInLeft`, `LightSpeedInRight`
- **Roll**: `RollInLeft`, `RollInRight`
- **Pinwheel**: `PinwheelIn`

### Modifiers

```tsx
FadeIn
  .duration(300)              // ms
  .delay(100)                 // ms before starting
  .easing(Easing.out(Easing.cubic))
  .springify()                // switch from timing to spring
  .damping(15)                // spring config (after .springify())
  .mass(1)                    //
  .stiffness(200)             //
  .overshootClamping(false)   //
  .restDisplacementThreshold(0.01)
  .restSpeedThreshold(2)
  .withInitialValues({ opacity: 0.5, transform: [{ scale: 0.8 }] })
  .withCallback((finished) => {
    'worklet';
    if (finished) { /* ... */ }
  })
  .reduceMotion(ReduceMotion.System)   // 'System' | 'Always' | 'Never'
```

Modifiers compose. Order doesn't matter for most.

### Examples

```tsx
// Stagger items in a list with delay based on index
{items.map((item, i) => (
  <Animated.View
    key={item.id}
    entering={FadeInDown.duration(300).delay(i * 50)}
  >
    {/* row */}
  </Animated.View>
))}

// Springy zoom-in for a hero element
<Animated.View entering={ZoomIn.springify().damping(15).mass(0.8)} />

// Custom initial values
<Animated.View entering={FadeIn.withInitialValues({
  opacity: 0,
  transform: [{ scale: 0.5 }, { rotate: '-45deg' }],
})} />
```

## Exiting animations

Same naming, replace `In` with `Out`: `FadeOut`, `SlideOutLeft`, `ZoomOut`, `BounceOutDown`, etc. Same modifier set.

```tsx
<Animated.View
  entering={FadeIn}
  exiting={FadeOut.duration(150)}
/>
```

Important: the component remains mounted in the React tree during the exit animation. After the animation completes, it unmounts.

## Layout transitions

Animate position/size changes that result from layout shifts (siblings adding, removing, resizing).

### Presets

- `LinearTransition` — straightforward interpolation, default
- `FadingTransition` — cross-fades between positions
- `SequencedTransition` — animates X first, then Y (or configurable)
- `JumpingTransition` — adds a small "jump" arc, playful
- `CurvedTransition` — curved path between positions
- `EntryExitTransition` — combines an exit at old position with an entry at new

```tsx
<Animated.View layout={LinearTransition} />
<Animated.View layout={LinearTransition.springify().damping(18).stiffness(200)} />
```

### When layout transitions fire

Whenever the on-screen rectangle of the `Animated.View` changes due to surrounding layout. Common triggers:

- A sibling above is added or removed (this view's `y` shifts)
- A flex container reflows
- The component's own size changes (if its style changes width/height through state)

They do *not* fire for transform-driven movement (translateX/Y are layout-free).

## Combining entering + layout + exiting on lists

The classic animated-list setup:

```tsx
function AnimatedTodoList({ todos }: { todos: Todo[] }) {
  return (
    <Animated.View>
      {todos.map((todo) => (
        <Animated.View
          key={todo.id}
          entering={FadeInDown.duration(250)}
          exiting={FadeOutUp.duration(200)}
          layout={LinearTransition.springify()}
          style={styles.row}
        >
          <Text>{todo.text}</Text>
        </Animated.View>
      ))}
    </Animated.View>
  );
}
```

Adding a todo at the top: it fades-in-down; siblings spring to their new positions. Removing one: it fades-up-out; siblings collapse upward. Reordering: items spring to their new spots.

## Custom layout/entering animations with `Keyframe`

For when presets don't cut it. `Keyframe` lets you define percentages of style snapshots.

```tsx
import { Keyframe, Easing } from 'react-native-reanimated';

const customEnter = new Keyframe({
  0: {
    opacity: 0,
    transform: [{ translateY: 30 }, { rotate: '-8deg' }, { scale: 0.9 }],
  },
  60: {
    opacity: 0.9,
    transform: [{ translateY: -4 }, { rotate: '2deg' }, { scale: 1.02 }],
    easing: Easing.out(Easing.cubic),
  },
  100: {
    opacity: 1,
    transform: [{ translateY: 0 }, { rotate: '0deg' }, { scale: 1 }],
  },
}).duration(450);

<Animated.View entering={customEnter} />
```

Per-keyframe `easing` is optional and only valid between two adjacent keyframes.

## Custom layout animations from scratch

The `LayoutAnimationConfig` API and writing full custom layout animations is rarely needed and the API has some sharp edges; reach for it only when presets + `Keyframe` aren't expressive enough. The official docs at https://docs.swmansion.com/react-native-reanimated/docs/layout-animations/custom-animations cover the four functions you need to implement (`initialValues`, `animations`, `callback`, plus the entering/exiting/layout variants).

## Disabling layout animations in subtrees

Sometimes layout animations cascade in ways you don't want — for example, during navigation transitions, or when initial mount triggers entering animations you'd rather skip on first paint.

```tsx
import { LayoutAnimationConfig } from 'react-native-reanimated';

<LayoutAnimationConfig skipEntering>
  {/* children mount without entering animations on first render */}
  {/* later changes inside this subtree still animate */}
</LayoutAnimationConfig>

<LayoutAnimationConfig skipExiting>
  {/* children don't animate on unmount */}
</LayoutAnimationConfig>
```

This is the typical solution for "I don't want the whole screen to fade in every time it mounts."

## FlatList and virtualization caveats

FlatList virtualizes — it mounts/unmounts rows as you scroll. Entering animations on row items will fire every time a row scrolls back into view, which looks janky.

Mitigations:

- **Disable entering on FlatList rows** unless you genuinely want re-fire on each remount. Use plain `Animated.View` with `layout` only, no `entering`.
- **Use `itemLayoutAnimation` on `Animated.FlatList`** for built-in row layout animations that handle the lifecycle correctly:
  ```tsx
  <Animated.FlatList
    data={items}
    itemLayoutAnimation={LinearTransition.springify()}
    renderItem={({ item }) => <Row item={item} />}
  />
  ```
- **Use `keyExtractor` with stable IDs** — otherwise React unmounts and remounts rows on every change, defeating layout animations.

For long lists with reordering, FlashList from Shopify has its own layout animation integration and is often a better choice than FlatList.

## Reduced motion

All presets respect the system Reduce Motion setting by default. To override:

```tsx
import { ReduceMotion } from 'react-native-reanimated';

FadeIn.reduceMotion(ReduceMotion.Always)   // always shortened/skipped
FadeIn.reduceMotion(ReduceMotion.Never)    // ignore the system setting
FadeIn.reduceMotion(ReduceMotion.System)   // default — honor the setting
```

Be thoughtful — decorative animations should respect the system setting; critical visual feedback (e.g., a button that confirms an action) may need `Never` to remain understandable.

## Common gotchas

- **Entering animations on first render of the whole screen** — annoying, fires on navigation in. Wrap with `<LayoutAnimationConfig skipEntering>` or set a state-driven trigger.
- **Mixing `transform` styles with layout animations on the same element** — the layout animation animates layout properties (left, top, width, height); a `useAnimatedStyle` transform on the same view can compose, but be careful with mid-animation interrupts.
- **`exiting` on Modal contents** — modal portals can interfere. Test on both platforms.
- **`layout` not firing** — confirm the on-screen rectangle is actually changing. Transform-only movement doesn't trigger layout transitions.
- **Web target** — entering/exiting animations have partial parity on web; some presets may not run identically. Test if web is a target.
