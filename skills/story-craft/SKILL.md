---
name: story-craft
description: Use this skill whenever the user is planning, scripting, storyboarding, directing, designing, or critiquing storytelling delivered through video, illustration, motion graphics, or animation. Triggers include "write a script for an explainer", "storyboard this", "make a beat sheet", "plan an animated ad", "direct a brand film", "design a learning module", "what's the hook for this video", "how should I structure this explainer", "review my animatic / storyboard / cut", "why does this feel flat", or any creative-direction question about pacing, story structure, visual hierarchy, motion, sound, or emotional impact for illustrated or animated media. Use it even when the user names a render tool (Remotion, Lottie, After Effects, Rive) but is asking what makes the piece compelling rather than how to render it — this is the creative-direction layer above the technical animation skills. Also trigger for critique — evaluating an existing video, board, or design against storytelling and learning-science principles.
---

# Story Craft

A skill for making illustrated, animated, and video storytelling *land* — before a single frame gets rendered. It is the creative-direction brain that sits above the technical render skills (`lottie-animation`, `framer-motion`, `remotion-skia`, After Effects, Rive). Those skills answer *how do I render this motion?* This one answers *what should the piece say, in what form, in what order, and why will anyone care?*

It draws on the durable evidence base for the medium — Mayer/Sweller/Paivio on how people learn from words-plus-pictures, Tversky and Höffler & Leutner on when motion actually helps, Disney's twelve principles on what gives motion life, Campbell/McKee/Pixar on narrative architecture, Cialdini/Kahneman and the Google/TikTok/Meta platform codes on persuasion, and Tufte/salience research on visual hierarchy — and turns it into decisions a small team can actually execute.

## Why this skill exists

Most generated creative direction fails the same way: it jumps to *style* before *goal*. It picks a look, fills every second with motion, stacks on-screen text over busy scenes, and buries the point until after the audience has scrolled away. The output is often beautiful and structurally useless — it doesn't teach, doesn't persuade, isn't memorable, and can't be measured.

The single most consistent finding across the literature is that the medium works when it does three things: **reduce extraneous cognitive load, make structure and change visible, and tie every visual/motion/sound decision to a clear objective.** "More animation" is not the lever. *Better alignment* — between message and medium, attention and structure, emotion and ethics, production and measurement — is the lever. This skill exists to force that alignment early, when it's still cheap to change.

## The core operating principle

**Goal-first, audience-aware, format-flexible.** Never start from "what should this look like?" Start from "what is this piece *for*, who is it for, and how will we know it worked?" The objective determines the structure, the format, the pacing, and the metric. Style serves the goal; it does not lead.

Two corollaries do most of the work:

1. **Match visual dynamism to information type.** Animation is not automatically better than a static illustration — the average instructional advantage is real but modest (d ≈ 0.37) and conditional. Motion earns its cost only when it externalizes change that's hard to infer from a still frame. (See `references/animation-principles.md` → "When animation helps and when it hurts.")

2. **Design at three nested time scales.** Every piece has a **macro-arc** (the whole promise), **scene beats** (the smallest meaningful claim or emotion shift), and a **frame focal point** (the one thing the eye should hit first). If you can't state all three in plain language, the design is too busy. This single test catches most overload before production.

## Workflow

Work through these in order for any generation task. Skip a step only when it genuinely doesn't apply — and say so.

1. **Establish the objective, audience, and promise.** Pin down the *primary* objective (most pieces have one that dominates), the audience, the platform(s), a one-sentence promise, and the success metric. If the brief leaves these unspecified, state your assumptions explicitly and proceed — don't stall. Use `assets/templates/creative-brief.md` to capture this.

2. **Choose the format by information type.** Use the decision table below. The format choice is downstream of the objective and the kind of information, not a style preference.

3. **Architect the story at three time scales.** Pick a structure template (`references/story-structures.md`), then write the macro-arc, the beats, and the focal point for each beat. The opening beat is disproportionately important — front-load the hook and, for anything persuasive, the brand/value cue.

4. **Apply the relevant principle set.** Pull only the reference you need (see the index below). A learning module leans on `learning-design.md`; an ad leans on `persuasion-platforms.md`; both lean on `animation-principles.md` and `visual-design.md` for the craft layer.

5. **Produce the deliverable** using the matching template in `assets/templates/`. Keep on-screen text minimal in dense animated scenes; prefer narration plus a clean visual over full sentences pasted on motion.

6. **Self-check against the rubric** (below) before delivering. The audience shouldn't be your first QA pass.

## Format selection by information type

| The information challenge | Default format | Why |
|---|---|---|
| Multiple items must be compared or revisited at once | Static illustration / multi-panel graphic | Stills let the eye inspect and re-read; motion forces a pace |
| A causal process unfolds over time | 2D motion graphics with cueing + segmentation | Externalizes transient change; segment into 3–7s conceptual chunks |
| Rotation, occlusion, or embodied spatial understanding is central | 3D or pseudo-3D | Only when it reduces inference burden enough to justify the cost |
| Audience should reflect, choose, attempt, or retry | Interactive module / branching scenario | Aligns narrative with retrieval and practice |
| Paid social needs efficient thumb-stop impact | Short vertical ad, brand/value early, clear CTA | Reach and recall reward repetition and early clarity |

Default under uncertainty: **clean 2D illustrated system + functional motion only where it clarifies change + one accessibility-ready master that re-cuts into short social assets.** Reserve 3D for genuine spatial reasoning.

## Reference index — read only what the task needs

| Read this when… | File | Covers |
|---|---|---|
| You need story structure, narrative tension, character, or emotional arc | `references/story-structures.md` | Campbell, McKee, Pixar economy, transportation, structure templates, the three time scales |
| You're deciding *whether/how* to animate, or judging motion quality | `references/animation-principles.md` | Disney's 12 principles, when animation helps vs. hurts, timing/pacing, motion-as-information |
| It's a learning module, explainer, onboarding, or training | `references/learning-design.md` | Mayer's multimedia principles, cognitive load, dual coding, segmenting/pre-training, emotional design |
| You're setting hierarchy, color, type, or composition | `references/visual-design.md` | Salience & focal path, hierarchy, color, typography, contrast/WCAG, motion-design systems |
| It's an ad, brand film, or anything that must persuade or be recalled | `references/persuasion-platforms.md` | Cialdini, Kahneman, narrative persuasion, durations, Google ABCDs, TikTok/Meta codes, brand codes |
| You're planning the pipeline, shipping, or measuring | `references/production-measurement.md` | Small-team workflow, checklists, accessibility/localization, measurement & A/B tests, ethics |

## Critique mode

When the user hands you an existing piece (script, board, animatic, cut, or design) and asks for review, run it against the same principles you'd build from, and **lead with the highest-leverage fixes** rather than a top-to-bottom commentary. Structure the critique like this:

1. **Restate the apparent objective and audience.** If you can't infer them from the piece, that's itself the first finding — ambiguous goal is the most common root cause of flat work.
2. **Run the three-time-scale test.** Can you state the macro-arc, the beats, and each frame's focal point? Where it fails, that's where the piece is overloaded or unfocused.
3. **Diagnose by principle set**, in priority order: Is the goal/format matched (right dynamism for the information)? Is the hook early and the value/brand cue early? Is extraneous load present (decorative motion, duplicated text, split attention)? Does motion carry meaning or just energy? Is hierarchy legible (one dominant focal point per frame)? Is it accessible and ethical (captions, contrast, reduced-motion, no coercive patterns)?
4. **Give specific, rankable fixes**, each tied to the principle it serves and the outcome it should move. Avoid vague praise; Stewart wants the diagnosis, not reassurance.

## Self-check rubric

Before delivering any generated direction — or as the backbone of a critique — confirm:

- [ ] **One dominant objective** is named, and every beat serves it.
- [ ] **Three time scales** are each stateable in plain language.
- [ ] **The hook lands first**; for persuasion, brand/value appears early (first ~3s on social).
- [ ] **Format matches information type** — motion only where it externalizes change.
- [ ] **Extraneous load is stripped** — no decorative motion, no full-sentence text over busy scenes, words sit near what they label.
- [ ] **Motion carries meaning** (cause, transition, hierarchy, emphasis) and degrades gracefully under reduced-motion.
- [ ] **It works muted** if the platform is sound-off; narration is intelligible if sound-on.
- [ ] **Accessibility & localization are designed in** — captions/transcript planned, live text over baked-in text, contrast ≥ 4.5:1 for body text, locale-sensitive symbols/RTL considered.
- [ ] **It's ethical** — affective devices clarify genuine stakes rather than coerce; people are shown with agency, not as tokens; disclosure where needed.
- [ ] **It's measurable** — leading indicators (completion, hook rate) are separated from true outcomes (transfer, recall, conversion, behavior).

## A note on house style

When producing the actual artifacts, default to Stewart's deliverable conventions: structured and copy-pasteable, tables/matrices where they clarify, plain labeled sections, and a single explicit next step at the close. Match the brand voice to the brief — practitioner-first and outcome-oriented for stewmore.dev/plotr.ai work, adapted otherwise. Don't pad with flattery or hedging; give the decision and the reason.
