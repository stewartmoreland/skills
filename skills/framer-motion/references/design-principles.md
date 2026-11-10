# Animation Design Principles

Animation is a design discipline before it's a code discipline. The library you use barely matters if the timing is wrong or the motion has no purpose. This file is for that layer — when to animate, how long, with what curve, in what order, and how to do it inclusively.

These principles apply to Motion (web) and Reanimated (native) equally.

## Table of contents

1. The four jobs of animation
2. Timing taxonomy
3. Easing — the curves that matter
4. Springs — why and when
5. Choreography & staggering
6. Direction and meaning
7. When NOT to animate
8. Accessibility & reduced motion
9. Common UI patterns and their timings
10. Quality smell tests

---

## 1. The four jobs of animation

Animation in product UI serves four purposes. If a proposed animation doesn't do at least one of these, cut it.

**1. Direct attention.** A new element fading in tells the user "look here." A pulse on a notification badge says "this is unread." Use sparingly — every claim on attention competes with every other.

**2. Signal causation.** When a user taps something and another thing changes, animation can show the connection. The expanded card grew from the thumbnail. The new screen slid in from the right because the user tapped "next." Without this link, the UI feels arbitrary.

**3. Soften change.** An element appearing instantly is a small visual shock. A 200ms fade is the same change wearing a softer edge. This is why fade-in feels "professional" — it reduces cognitive load even when the user doesn't notice.

**4. Express character.** A bouncy spring on a casual app feels playful. The same spring on a banking app feels unserious. Animation is one of the most legible carriers of brand voice; pick curves that match the product's tone.

If you're animating "to make it feel more dynamic" — stop. That's decoration, not communication.

## 2. Timing taxonomy

Most UI animations land in one of four duration buckets. Internalize these so you reach for the right one without thinking.

### 80–150ms — instant feedback

Tap acknowledgment, hover state, focus ring appearance, button press-in.

Below ~100ms the human visual system reads it as a state change rather than a transition. Above ~150ms it starts to feel slow for feedback. Default to **120ms**.

### 200–350ms — standard moves

Drawer open, modal enter, accordion expand, tooltip appear, card hover-lift, page section reveal.

This is the most common bucket. Default to **240ms**. The eye reads this as "intentional movement" — long enough to follow, short enough to not feel sluggish.

### 400–600ms — large moves

Full-screen transitions, shared element transitions, hero reveals, modal sheets sliding up from off-screen.

Default to **400ms**. The longer duration earns itself by giving the user time to track a large movement across the screen.

### >600ms — almost always wrong

Either you're showing off (decoration animation), or the user is waiting (this is a load state, not a transition). The exceptions are deliberate showpieces — a splash screen reveal, a celebration moment after a purchase — where the animation IS the content.

### Distance and duration

Larger distances on screen want longer durations, but not linearly. A useful rule of thumb: duration scales with the *square root* of distance. A move twice as long should be ~40% longer in duration, not 100%.

A 16px tooltip slide: ~140ms. A 100px drawer slide: ~280ms. A full-screen slide: ~400–500ms. Not because of math — because that's what reads as physically plausible.

## 3. Easing — the curves that matter

Linear motion looks wrong because nothing in the physical world starts and stops instantly at full speed. Pick curves intentionally.

### The three primary easings

**ease-out** (`cubic-bezier(0, 0, 0.2, 1)`) — fast start, slow end. Use for **entering** animations. The element arrives quickly, then settles. Reads as "delivered."

**ease-in** (`cubic-bezier(0.4, 0, 1, 1)`) — slow start, fast end. Use for **exiting** animations. The element lingers, then accelerates off-screen. Reads as "leaving."

**ease-in-out** (`cubic-bezier(0.4, 0, 0.2, 1)`) — slow at both ends. Use for **round trips** and for moves where both start and end are visible. Most CSS transitions default to this.

### Material's "standard" curve

`cubic-bezier(0.4, 0, 0.2, 1)` is Material Design's standard easing — slightly snappier than CSS `ease-in-out`. A workhorse default.

### The "soft confident" curve

`cubic-bezier(0.32, 0.72, 0, 1)` — fast launch, gentle settle. Reads as "polished and assured." Excellent for tween-driven fades and reveals in design-forward UI.

### When to use cubic-bezier vs spring

Use **cubic-bezier** when:
- You need a precise visual look (especially across platforms)
- The animation has no follow-through implication (a fade, a color shift)
- You're matching a designer-handoff curve from Figma

Use **spring** when:
- The element is moving (translation, scale)
- The motion should feel responsive to context
- You want overshoot, settling, or physical character

Most production UI uses both — springs for motion, beziers for fades and color transitions.

## 4. Springs — why and when

Springs are physics simulations: stiffness, damping, mass, optional initial velocity. They feel more alive than cubic-beziers because they respond to context — a spring driven by a fast gesture rebounds harder than one driven by a click.

### The three knobs

- **Stiffness** — how hard the spring pulls toward target. Higher = faster.
- **Damping** — how much the spring resists oscillation. Higher = less bounce.
- **Mass** — how much the element "weighs." Higher = heavier, slower feel.

Most springs you write should have **stiffness in 200–400** and **damping in 20–40**. Mass usually stays at 1; tweak only if you want a deliberately heavy or floaty feel.

### Common spring presets

```ts
// Snappy — fast UI feedback, hover states
{ stiffness: 400, damping: 30, mass: 0.8 }

// Confident — default for most moves
{ stiffness: 260, damping: 28, mass: 0.9 }

// Gentle — large moves, hero reveals
{ stiffness: 180, damping: 24, mass: 1.0 }

// Bouncy — playful microinteractions, celebrations
{ stiffness: 300, damping: 14, mass: 1.0 }

// Heavy — momentum-driven drags
{ stiffness: 150, damping: 30, mass: 1.4 }
```

### The duration-based spring (Motion v12, Reanimated 4+)

Both libraries now support specifying duration + bounce/dampingRatio. This is often easier to reason about:

```ts
// Motion
{ type: "spring", duration: 0.4, bounce: 0.2 }

// Reanimated
withSpring(100, { duration: 400, dampingRatio: 0.7 })
```

`bounce: 0` (Motion) / `dampingRatio: 1` (Reanimated) = no overshoot. Higher bounce / lower dampingRatio = more oscillation. The duration is approximate (springs settle when they settle), but it gives you a useful "this is how long the user perceives it" knob.

### When NOT to spring

- Fades and color shifts — springs on opacity look weird because there's no physical motion to "feel"
- Synchronized timing across many elements where you need precision (use tween-based variants)
- Crossfades where overshoot would cause flickering

## 5. Choreography & staggering

When multiple elements move at the same time, *how* they're related matters as much as the motion itself.

### Stagger gap

The pause between sibling animations. **50–80ms** reads as "intentional sequence." Less than 30ms looks accidental; more than 120ms feels slow.

Default: **60ms** between list items. Tune down for very long lists (40ms keeps the total reasonable) and up for short featured sequences (80ms gives each item its moment).

### When to stagger

- **Lists entering the viewport** — every time, almost without exception
- **Grid items in a reveal** — stagger by row, sometimes by row + column for a wave effect
- **Multi-step UI reveals** — header, then content, then CTA
- **Form fields appearing in a modal** — top to bottom

### When NOT to stagger

- Two elements that should feel like a single unit (a card and its shadow)
- Elements that are conceptually equivalent and simultaneous (toggle states, simultaneous chart bars)
- Anything happening in <200ms total — no time for stagger to read

### Direction-aware stagger

For lists entering from below, stagger top-to-bottom (or out-from-center). For lists exiting, stagger bottom-to-top — the visual order of departure should match the visual order of arrival in reverse, mostly.

### Lead-in / lead-out

When a parent and child both animate, decide whether the parent leads or the child leads. Usually:
- **Parent enters first**, then children — the container "delivers" the content
- **Children exit first**, then parent — the content "leaves" before the container does

Motion makes this explicit via `transition: { when: "beforeChildren" | "afterChildren" }`.

## 6. Direction and meaning

Movement direction carries semantic weight. Violating these conventions creates subtle disorientation.

- **Down** — appearing, settling, arriving. New content drops in from above. Modals on small screens slide up from below (which is actually "appearing" — they come from out of view *toward* the user).
- **Up** — leaving, dismissing, ascending. Dismissed sheets slide back down (off the screen). Acknowledged notifications fade up and away.
- **Right** — forward in a flow, progress, next step. New screens enter from the right in left-to-right reading languages.
- **Left** — back, return, retreat. Previous screens slide in from the left.

For right-to-left languages, mirror these — RTL convention reverses forward/back. Both Motion and Reanimated honor `I18nManager.isRTL` (RN) and `dir="rtl"` (web) at the CSS level if you use logical properties, but for transform-based animations, you handle direction yourself.

**Scale up** = importance, focus, selection. **Scale down** = de-emphasis, dismissal.

**Opacity up** = becoming present. **Opacity down** = becoming absent. Both are weaker signals than motion — combine with translation when you want the change to feel significant.

## 7. When NOT to animate

The hardest discipline. Resist the urge.

**Don't animate to "add polish."** If you can't articulate what the animation tells the user, it's decoration. Cut it.

**Don't animate inline content shifts.** When text or images load and the page jumps, the user wants to know where to look — animating the jump makes it harder to find. Use skeletons or reserve space instead.

**Don't animate the user's input.** When they type, scroll, or drag, their input should map 1:1 to motion. Adding interpolation or delay makes the UI feel laggy. (Springs *on release* are different — those signal "your gesture ended, now I'm taking over.")

**Don't animate every state change.** Toggling a checkbox doesn't need a 300ms motion. A 80ms color shift is enough. Save the bigger moves for bigger transitions.

**Don't animate purely vertical lists on mobile during scroll.** The scroll itself is the motion. Adding entrance animations to items as they enter the viewport on a scroll fights the scroll gesture.

**Don't animate the same element twice in 200ms.** If a button has a tap state and immediately afterward triggers a layout change, pick one — they'll fight visually.

## 8. Accessibility & reduced motion

Some users — those with vestibular disorders, motion sensitivity, or just a preference — have system-wide reduced motion enabled. Both libraries expose this; honor it always.

### What "reduced" means

Reduced motion ≠ no animation. The goal is to remove **movement** (translation, rotation, scale, parallax) while preserving **state change indication** (fade, color shift, instant snap).

A modal that slides up by 200px in normal mode should *fade in* in reduced mode. Same meaning, no vestibular trigger.

### The general rule

When `useReducedMotion()` returns true:
- Replace translate / scale / rotate with opacity transitions
- Cut durations roughly in half (motion that's not happening doesn't need timing)
- Skip stagger — if there's no motion, there's nothing to stagger
- Disable parallax entirely (this is the most common motion-sickness trigger)
- Disable infinite/looping animations (pulses, spinners that aren't loading indicators)

### Don't forget keyboard and focus

Animation is not just a visual concern. Modal exit animations should not delay focus restoration — focus the element that *would* be active after the modal closes *first*, then animate the modal away. A 300ms delay on focus return strands keyboard users.

Auto-playing carousels that animate without user input should pause when an element inside them gets focus. Marquees should pause on hover.

### Accessible defaults

Build the accessible path first. If your animation looks fine with `prefers-reduced-motion: reduce`, you have a baseline that works for everyone. Then layer the full motion on top.

## 9. Common UI patterns and their timings

A reference for getting the duration and curve right on common patterns.

| Pattern | Duration | Curve | Notes |
|---------|----------|-------|-------|
| Button hover | 120ms | spring (snappy) | Scale 1.0 → 1.03, not more |
| Button press (active) | 80ms | tween linear | Scale 1.0 → 0.96 |
| Focus ring appear | 120ms | ease-out | Opacity + slight scale |
| Tooltip enter | 160ms | ease-out | Small slide + fade |
| Tooltip exit | 100ms | ease-in | Faster than enter |
| Dropdown open | 180ms | spring (snappy) | Scale-from-top-y origin |
| Modal enter | 280ms | spring (confident) | Fade + scale 0.96 → 1 |
| Modal exit | 200ms | ease-in | Fade + scale 1 → 0.98 |
| Drawer (side panel) | 320ms | spring (confident) | Slide from edge |
| Bottom sheet (mobile) | 400ms | spring (heavy) | Slide up, momentum-aware |
| Toast enter | 200ms | spring (snappy) | Slide in + fade |
| Toast exit | 240ms | ease-in | Slide out + fade, can stagger if multiple |
| Page route transition | 400ms | spring (gentle) | Crossfade or slide |
| Shared element (hero) | 500ms | spring (gentle) | Position + size, no fade |
| List item reveal | 320ms total + 60ms stagger | spring | Fade + 12–16px translate |
| Accordion expand | 240ms | ease-out | Height animation (layout) |
| Tab switch (content) | 200ms | tween | Crossfade, no slide |
| Tab indicator move | 280ms | spring (snappy) | Slide along tab bar |
| Pull-to-refresh | follows gesture | gesture + spring on release | Spinner appears at ~80px |
| Image zoom open | 360ms | spring (confident) | Shared element, slight delay |
| Toggle switch | 180ms | spring (snappy) | Thumb position + color |
| Reveal-on-scroll | 600ms enter | spring (gentle) | Once per element, fade + 20px translate |
| Stagger between scroll-reveal siblings | 80–120ms | n/a | Longer than list stagger — they're further apart visually |
| Scroll progress bar | continuous | useSpring smoothing | `{stiffness: 100, damping: 30}` for smoothness |
| Parallax hero | continuous | n/a | Half the scroll distance is plenty — more feels disorienting |
| Notification badge pulse | 1.2s loop | ease-in-out | Cut entirely on reduced motion |
| Loading spinner | 1s linear loop | linear | This is one of the few legitimate uses of linear easing |

## 10. Quality smell tests

When an animation feels "off" but you can't pinpoint why, run through these:

**Does it match the size of the move?** Small moves want short durations (120–200ms). Large moves want longer (300–500ms). A modal that takes 600ms feels broken; a tooltip that takes 400ms feels sluggish.

**Is the easing right for the direction?** Entering: ease-out. Exiting: ease-in. Round trip: ease-in-out or spring. Linear is almost never right.

**Is it staggered when it should be?** Multiple elements moving in unison feel like a hard cut. Add 60ms between them.

**Is it staggered when it shouldn't be?** A card and its shadow stagger? That's two parts of the same thing — they should move together.

**Does direction match meaning?** Forward in a flow should move right (in LTR). Back should move left. A "next" button that triggers a leftward motion is wrong.

**Does the motion fight the user's input?** Adding springs to direct-manipulation moves makes UIs feel laggy. Reserve springs for *after* the input ends.

**Is anything animating that shouldn't be?** If you can't explain what the animation tells the user, cut it.

**Does it work with reduced motion?** Turn on the OS setting and use the UI. If it's still pleasant and functional, you're done. If it's broken, you've been hiding behind motion.

**Is the timing the same as your competition?** If everyone in the category uses 240ms drawer animations and yours is 400ms, you'll feel slow even if your animation is "better designed." Match the category default unless you have reason to differ.
