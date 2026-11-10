# Learning Design for Illustrated & Animated Media

The evidence base for teaching with words plus pictures. Read this for explainers, learning modules, onboarding, training, and any piece whose primary objective is *understanding, retention, or transfer*.

## Contents
- [The two theories underneath everything](#the-two-theories-underneath-everything)
- [Mayer's multimedia principles, with effect sizes](#mayers-multimedia-principles-with-effect-sizes)
- [Segmenting and pre-training: pacing dense content](#segmenting-and-pre-training-pacing-dense-content)
- [Emotional design: friendly without clutter](#emotional-design-friendly-without-clutter)
- [Putting it together: a learning-module pattern](#putting-it-together-a-learning-module-pattern)

## The two theories underneath everything

**Cognitive Load Theory (Sweller).** Working memory is small and easily swamped. Three loads compete: *intrinsic* (the inherent difficulty of the material), *extraneous* (load created by poor design — the only kind you can cut for free), and *germane* (the productive effort of building mental schemas). Good design strips extraneous load and protects capacity for germane processing. Overloaded, poorly sequenced material blocks schema formation, which is *why* chunking and sequencing matter.

**Cognitive Theory of Multimedia Learning (Mayer).** People process verbal and pictorial information through separate, limited channels, and learn by actively *selecting* relevant material, *organizing* it into coherent structures, and *integrating* it with prior knowledge. Design improves learning when it supports those three processes and avoids overloading either channel.

**Dual Coding (Paivio)** explains the upside: verbal and visual representations can reinforce each other when coordinated. This is *not* an argument for more media — it's an argument for **parallel but complementary encoding**. A concise voiceover paired with a simplified diagram beats full written narration pasted over a busy scene, every time.

## Mayer's multimedia principles, with effect sizes

These are the most directly actionable findings for the medium. Effect sizes are from the syntheses Mayer & colleagues report; treat them as relative priorities, not precise constants.

| Principle | What to do | Effect | Practical move |
|---|---|---|---|
| **Coherence** | Cut interesting-but-extraneous material — decorative images, background music, tangents | Strong | Every element earns its place or it goes |
| **Signaling** | Cue attention with arrows, highlights, headings, lesson maps | ~0.74 | Guide the eye to what matters in dense scenes |
| **Redundancy** | Don't add on-screen text that duplicates the narration when graphics are already demanding | ~0.69 | Narration + visual beats narration + visual + full text |
| **Spatial contiguity** | Place words next to the part of the image they describe | ~0.48 | Labels touch their referents; no legend-hunting |
| **Temporal contiguity** | Present corresponding words and pictures at the same time, not sequentially | Strong | Sync narration to the visual it explains |
| **Modality** | Offload words to the audio channel when the visual channel is busy | ~0.76 (median) | Narrate the diagram; don't caption it with full sentences |
| **Personalization** | Use conversational rather than formal language | Positive | "You'll notice…" not "It should be noted that…" |
| **Voice** | Human-sounding narration over machine-flat delivery | Positive | Warmth and competence; a guide, not a manual |

The redundancy and modality principles are the two most commonly violated in generated explainers, because the instinct is to reinforce the voiceover with matching on-screen text. When the graphic is already demanding, that *duplicate* text overloads the visual channel and *hurts* learning. Reserve on-screen text for keywords, labels, and signaling — not transcription.

> Note the boundary condition: modality and redundancy assume the graphic is doing real work. For a static screen with a single number or a short key term, on-screen text is fine. The harm comes from full-sentence text *competing with* a busy visual.

## Segmenting and pre-training: pacing dense content

When material is unfamiliar or complex, two principles carry most of the load (both strongly supported, median effect sizes around 0.75–0.79):

- **Segmenting** — break a continuous explanation into learner-paced chunks the audience can pause, tap, or mentally complete before the next step. Chunk by *meaning* (one concept per segment), not by production convenience. This is the multimedia version of chunking from cognitive load theory.
- **Pre-training** — introduce the essential components and terms *first*, then show the system in motion. If a lesson needs new vocabulary, relationships, or part-names, front-load them so working memory isn't simultaneously learning the parts and the process.

Practical sequence for a complex process: name the parts (pre-train) → show one segment of the process → pause/check → next segment → consolidate with a static recap.

## Emotional design: friendly without clutter

Research associated with Plass, Um & Mayer indicates that **warm colors, rounded shapes, and appealing treatments of essential elements** can foster positive emotion and, in some studies, improve motivation, engagement, and learning. Friendly, playful design supports persistence and attention — *as long as the emotional layer stays tied to the content and doesn't add clutter or compete for attention.*

The discipline: apply the appealing treatment to the *essential* elements (the character doing the teaching, the object being explained), not to decorative additions. Charm that lives on the content helps; charm bolted on beside the content is just more extraneous load wearing a smile.

## Putting it together: a learning-module pattern

A reliable default structure for an explainer or module:

1. **Pre-train** the essential terms/parts (static, labeled, spatially contiguous).
2. **Hook** with a question or curiosity gap (the macro-arc promise).
3. **Segment** the mechanism into meaningful chunks, each: one proposition, narrated, with signaling cues, on-screen text limited to labels.
4. **Retrieve** — a checkpoint, question, or branching choice. Passive viewing teaches far less than viewing plus retrieval; pieces like TED-Ed and Khan Academy succeed precisely because they couple explanation to learner action and practice.
5. **Consolidate** with a static recap panel the learner can compare and reread.

Measure both layers: leading indicators (completion, question-response rate, branch choices) *and* true outcomes (transfer, retention, behavior). A high-completion module can still teach poorly — see `production-measurement.md`.
