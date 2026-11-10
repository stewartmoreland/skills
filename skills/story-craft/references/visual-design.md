# Visual Design: Hierarchy, Color, Type, Composition

The frame-level craft — making any single image or scene instantly legible. Read this when setting visual hierarchy, color, typography, or composition for illustrated and animated work.

## Contents
- [Salience and the focal path](#salience-and-the-focal-path)
- [Visual hierarchy](#visual-hierarchy)
- [Color](#color)
- [Typography](#typography)
- [Data and information density (Tufte)](#data-and-information-density-tufte)
- [Contrast and accessibility baselines](#contrast-and-accessibility-baselines)

## Salience and the focal path

The Itti–Koch–Niebur saliency model explains why some compositions read instantly and others feel noisy: conspicuous locations — created by contrast, scale, position, motion, and feature difference — compete for attention. When several elements are equally conspicuous, the eye has no path and the viewer works to parse the scene. When one element clearly wins, the eye lands, then moves.

The operating rule: **every scene poses one dominant attentional question and offers one dominant focal answer.** Decide, for each frame, what the eye should hit first — then make sure nothing else competes at that weight. This is the frame-level version of "one idea per beat."

## Visual hierarchy

| Layer | Role | How to set it |
|---|---|---|
| Dominant | The one thing seen first | Most contrast, largest scale, motion, or isolation |
| Secondary | The supporting element | Clearly subordinate — smaller, lower contrast, off the optical center |
| Tertiary (optional) | A detail for the lingering eye | Quiet enough to ignore on first read |

The failure mode is the **equal-weight composition** — everything the same size, contrast, and emphasis, so everything shouts and nothing leads. If you can't name the dominant element, the hierarchy isn't built yet. This pairs directly with Disney's *staging* principle (`animation-principles.md`): remove clutter, frame the subject, light the point.

## Color

Use color **functionally first, decoratively second.** Its jobs, in priority:

1. **Grouping** — same color = same category or system.
2. **Emphasis** — a saturated accent against a muted field pulls the eye (this is a salience lever; spend it sparingly).
3. **Status / state** — success/warning/error, active/inactive, before/after.
4. **Affect** — warm/rounded palettes for friendliness (see emotional design in `learning-design.md`); cool/desaturated for calm or seriousness.

Two guardrails: **never rely on color alone to carry meaning** (pair it with shape, label, icon, or position for colorblind users and grayscale contexts), and **preserve contrast** so the color choice doesn't sacrifice legibility (see baselines below). A limited, intentional palette with one or two accents almost always outperforms a rainbow.

## Typography

- **Prefer live text over baked-in raster text.** Live text resizes, reflows, stays legible, and — critically — can be localized and updated without re-rendering art. WCAG explicitly discourages images of text when live text would serve. For animated pieces, this means keeping titles and labels as text layers, not flattened into the artwork, wherever the pipeline allows.
- **Strong scale contrast** between levels (display / heading / body / caption) does most of the hierarchy work; don't rely on weight alone.
- **Consistent, semantic use of styles** — a style means the same thing every time it appears. Inconsistent type is read as noise.
- **Personality cannot cost legibility.** A characterful display face for a title is fine; the same face for body copy at small sizes is not. Resizability and localization-friendliness outrank flourish.

## Data and information density (Tufte)

When the piece carries data or quantitative comparison, Edward Tufte's principles apply: maximize the data-ink ratio (cut chartjunk, gridlines, and decoration that don't encode information), respect the data's real structure, and let density serve clarity rather than impressiveness. A clean static chart that the eye can interrogate usually beats an animated data sequence that forces a pace — return to the dynamism-vs-information rule (`animation-principles.md`): comparison wants stillness.

## Contrast and accessibility baselines

These are the non-negotiable legibility floors (WCAG 2.2). Design to them from the first style frame, not at QA:

| Requirement | Threshold |
|---|---|
| Body / normal text contrast (AA) | **4.5 : 1** against its background |
| Large text contrast (AA) | **3 : 1** |
| Background audio under foreground speech (AAA) | at least **20 dB** lower, if present at all |
| Text presentation | Live text over images of text; support resize/reflow |

Background music and ambience routinely sabotage narration intelligibility — if speech is carrying the meaning, keep the bed well under it or drop it. And remember the muted case: on sound-off platforms the visual must carry the message alone, so don't let critical information live only in the voiceover.

Full media-accessibility and localization handling (captions, transcripts, audio description, RTL, locale-sensitive symbols) lives in `production-measurement.md`.
