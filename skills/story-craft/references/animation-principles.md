# Animation Principles & Motion Craft

When to animate at all, and — once you've decided to — what makes the motion feel alive instead of robotic. Read this when deciding whether/how to animate or when judging motion quality.

## Contents
- [When animation helps and when it hurts](#when-animation-helps-and-when-it-hurts)
- [Motion is information architecture, not decoration](#motion-is-information-architecture-not-decoration)
- [Disney's twelve principles](#disneys-twelve-principles)
- [Timing, pacing, and easing](#timing-pacing-and-easing)
- [Motion quality checklist](#motion-quality-checklist)

## When animation helps and when it hurts

This is the first decision, and the most-skipped one. **Animation is not inherently better than a static visual.** Tversky, Morrison & Bétrancourt's review is the key corrective: many apparent animation "wins" vanish once you notice the animated version simply had better graphics, more interactivity, or a better study procedure than the static comparison — not because it moved. Höffler & Leutner's meta-analysis finds a *real but modest* average advantage for instructional animation (d ≈ 0.37) — meaningful, not magic, and conditional.

The rule that follows:

> **Animate when motion externalizes transient change that's hard to infer from a still frame. Don't animate when it merely decorates, repeats, or makes the viewer chase information they could inspect calmly in a static image.**

Strong candidates for motion: a process unfolding over time (circulation, an algorithm's flow, equipment operation), physical causality, the timing/sequence of events, branching consequences. Weak candidates: comparisons, reference material, anything the viewer needs to re-read or hold side by side — those usually read better as a static panel or a multi-panel graphic.

For ads, motion's job is different: compress concept and brand mnemonic into a few memorable transitions, not to fill every second with novelty. For LMS review screens, static recap panels often beat full-motion summaries because they let the eye compare and reread.

## Motion is information architecture, not decoration

Both major design systems converge here. Material Design treats motion as a way to reveal relationships, highlight outcomes, and guide focus. Apple's Human Interface Guidelines warn against frequent or gratuitous motion and distinguish *meaningful* animation from spectacle. The synthesis: every motion choice should answer "what does this *tell* the viewer?" — cause, transition, hierarchy, state change, or emotional beat. If the honest answer is "energy," cut it.

Accessibility is part of this: motion sensitivity is common, and platforms expect a reduced-motion path. When a user prefers reduced motion, replace parallax, spinning, auto-advancing, and large multi-axis moves with dissolves or simple fades — and ensure the *same information* survives the swap. Design the reduced-motion version at storyboard, not as a post-production patch.

## Disney's twelve principles

From Thomas & Johnston's *The Illusion of Life*. These are what give motion weight, life, and appeal. They apply far beyond character animation — UI motion, logo reveals, and motion-graphic explainers all read better when these are respected.

1. **Squash & stretch** — distortion under force conveys weight and flexibility; preserve volume (stretch one axis, contract the other). The single biggest "is this alive?" tell.
2. **Anticipation** — a small reverse move before an action prepares the eye (the wind-up before the pitch). Removes the "teleport" feeling.
3. **Staging** — direct attention like a film director: framing, lighting, composition, and removing clutter so the audience looks where the story is. One clear idea per shot.
4. **Straight-ahead vs. pose-to-pose** — draw frame-by-frame for fluid, unpredictable action; key poses first then fill for controlled, dramatic, on-model work. Most motion graphics are pose-to-pose (keyframe-driven).
5. **Follow-through & overlapping action** — parts keep moving after the body stops and settle at different rates (hair, cloth, trailing elements). Nothing in nature stops all at once.
6. **Slow in & slow out (ease)** — things accelerate and decelerate; they don't snap to constant velocity. Linear interpolation is the loudest "a machine made this" signal.
7. **Arcs** — natural movement follows curved paths, not straight lines. Limbs, thrown objects, and even UI elements feel organic on arcs.
8. **Secondary action** — supporting motion that enriches the main action without stealing from it (the swing of arms while walking). Adds humanity; must stay subordinate.
9. **Timing** — the number of frames an action takes encodes weight and mood; heavy things move slower, light things snap. Timing *is* characterization.
10. **Exaggeration** — push past literal reality just enough to read clearly and feel alive; total realism often reads as dull or stiff.
11. **Solid drawing** — respect volume, weight, balance, and dimensionality; avoid "twinning" (symmetrical, lifeless poses). In motion graphics: respect consistent perspective and depth cues.
12. **Appeal** — the design has charisma the eye *wants* to follow (heroes often angular/symmetrical; "aww" via round, childlike forms). Appeal is to animation what casting is to film.

**For non-character work**, the high-leverage four are usually: **ease (6)**, **anticipation (2)**, **follow-through/overlap (5)**, and **staging (3)**. Get those right and even a simple logo reveal or UI transition stops feeling robotic.

## Timing, pacing, and easing

Pacing is matched to message complexity and platform affordance — there is no universal "right" duration.

| Format | Pacing default | Notes |
|---|---|---|
| Static illustration | One focal idea per frame/panel; reveal via progressive disclosure if needed | Use when the audience inspects, compares, or revisits |
| Motion-graphics explainer | One proposition per beat; one primary transition purpose at a time | Segment complex processes into 3–7s conceptual chunks with clear visual resets, not continuous motion |
| Short social/video ad | Hook immediately; value early; explicit close | First ~3s carries the brand/value; recall impact front-loads heavily in the first ~6s (see `persuasion-platforms.md`) |
| Interactive module | Chunk by learning objective, not by production scene | Let users pause/tap/advance; pacing is theirs, not yours |

Easing presets worth defaulting to (hand off to the render skill with these intentions):
- **Ease-out** for entrances — fast in, settle. Feels responsive.
- **Ease-in** for exits — accelerate away. Feels decisive.
- **Ease-in-out** for moves between two resting states — the most natural general-purpose curve.
- **Overshoot/back** sparingly, for playful or emphatic beats — a small overshoot reads as energy; a large one reads as cartoonish (use intentionally).

Overlap and stagger: when multiple elements enter, offset their starts (a few frames apart) rather than moving them in unison. Unison reads as mechanical; staggered entrances read as choreographed.

## Motion quality checklist

When generating or critiquing motion:

- [ ] Does this motion *tell* the viewer something (cause/transition/hierarchy/emphasis), or is it energy?
- [ ] Is every meaningful property change eased — never linear?
- [ ] Is there anticipation before significant actions, and follow-through after?
- [ ] Do elements move on arcs and at weights appropriate to what they represent?
- [ ] Are entrances staggered/overlapped rather than moving in unison?
- [ ] Is there one clear focal action per beat, with secondary motion kept subordinate?
- [ ] Does a reduced-motion version preserve the same information?
- [ ] If complex, is the process segmented into chunks with visual resets rather than one continuous flow?
