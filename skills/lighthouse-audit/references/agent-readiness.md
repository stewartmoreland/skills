# Agent Readiness: The Agentic Browsing Category & Agent-Friendly Site Design

## Contents
1. The Lighthouse Agentic Browsing category (13.3+)
2. How agents consume pages — the mental model
3. Accessibility tree well-formedness
4. Layout stability for agents
5. llms.txt authoring
6. Design patterns for agent-operable sites
7. Honest framing for users

---

## 1. The Agentic Browsing category

Lighthouse **13.3** (May 2026) introduced an **Agentic Browsing** category auditing how well AI agents can use a site. Key facts:

- It's explicitly marked **"under development"** — audits, weights, and IDs will change. Never hardcode its audit IDs in CI without version-pinning Lighthouse; enumerate them from the report JSON (`jq '.categories | keys'` then the category's `auditRefs`).
- A site is **not penalized for lacking AI features** — a plain, well-built page (example.com) scores green. Absent llms.txt or WebMCP isn't a failure; *malformed* ones are.
- As of mid-2026 it ships in the npm CLI / Chrome Canary; PageSpeed Insights and DevTools may lag on older Lighthouse versions.

Its checks, as shipped:
1. **Accessibility tree is well-formed** — derived from the existing accessibility audit data (§3).
2. **WebMCP validation** — checks declarative form annotations against the expected schema, and surfaces all tools registered on the page whether declarative or via `navigator.modelContext.registerTool` (details in `references/webmcp.md`).
3. **llms.txt follows recommendations** — if present: has an H1, isn't too short, contains links (§5).
4. **Layout stability** — the CLS data re-surfaced through an agent lens (§4).

## 2. How agents consume pages

Google's agent-friendly-site guidance (web.dev "ai-agent-site-ux") identifies three consumption formats, and each maps to a discipline:

| Agent input | What it rewards |
|---|---|
| **Screenshots** | Stable layout (low CLS), visible state, legible text, no critical info only in hover states |
| **Raw HTML** | Content present without JS execution, semantic markup, sane DOM size |
| **Accessibility tree** | Correct roles, names, labels, heading structure — everything screen-reader accessibility rewards |

The unifying insight to convey to users: **agent readiness ≈ accessibility + performance + crawlability done properly**. There is very little agent-specific work; the agent-specific surfaces (llms.txt, WebMCP) sit on top of fundamentals that already pay for human users. This is why the skill treats accessibility failures as agent-blocking bugs, not compliance checkboxes.

## 3. Accessibility tree well-formedness

The accessibility tree is the browser's simplified semantic representation of the page — far cheaper for an agent to process than HTML or pixels. Agents using it hit exactly the same walls as screen readers. What to enforce:

- **Real interactive elements**: `<button>`, `<a href>`, `<input>`, `<select>` — never `<div onclick>`. A div-button has no role, no name, no keyboard activation; it's invisible as an action to the agent.
- **Accessible names on everything interactive**: visible `<label for>` on inputs (placeholder is not a label), `aria-label` on icon-only buttons, meaningful link text. An agent literally cannot distinguish two unnamed icon buttons.
- **Heading hierarchy**: one `h1`, no skipped levels — agents use it as the page outline for navigation and extraction.
- **Landmarks**: `<header>`, `<nav>`, `<main>`, `<footer>` (one `<main>`); lets agents jump to content and ignore chrome.
- **Correct ARIA, sparingly**: wrong ARIA is worse than none (e.g. `role="button"` without keyboard handling lies to the agent). Prefer native elements; validate `aria-*` attributes match the role.
- **State exposed semantically**: `aria-expanded`, `aria-selected`, `disabled`, `aria-current` — an agent can't infer state from your CSS class names.
- **Images**: `alt` text that conveys function/content; empty `alt=""` for decorative.

Lighthouse's accessibility category (axe-core subset) is the automated floor — it catches missing names, contrast, ARIA misuse. Remember and communicate: automated checks find roughly a third of accessibility problems; keyboard-only walkthrough of key flows is the cheap high-value manual supplement, and it's also a direct simulation of how many agents drive pages.

## 4. Layout stability for agents

CLS ≤ 0.1 matters doubly for agents: an agent may act faster than a human, clicking coordinates from a screenshot taken moments earlier — a late-loading banner that shifts the button means the agent clicks the wrong thing. Fix patterns live in `references/performance.md` (cls-culprits-insight section). Additional agent-specific rules: don't move focus or open modals uninvited during load; make cookie/consent banners dismissible via the accessibility tree (real buttons with names); avoid infinite spinners with no semantic loading state (`aria-busy`, status roles).

## 5. llms.txt authoring

`/llms.txt` is a proposed markdown manifest telling LLM agents what the site is and where the important content lives. The format Lighthouse validates against:

```markdown
# Site or Project Name

> One-to-three sentence summary of what this site/product is and who it serves.

Optional paragraphs with key context an agent should know (pricing model,
main capabilities, constraints).

## Docs

- [Getting started](https://example.com/docs/start): what this covers
- [API reference](https://example.com/docs/api): endpoints and auth

## Optional

- [Blog](https://example.com/blog): secondary material agents can skip
```

Rules the Lighthouse audit checks: **must start with an H1**, must not be trivially short, must contain links. Conventions beyond that: blockquote summary right after the H1; H2 sections grouping curated links with one-line descriptions; an `## Optional` section for skippable material; plain markdown, no HTML. Optionally provide markdown mirrors of key pages at `page-url.md` and a full `/llms-full.txt` for docs sites.

Set expectations: adoption by AI crawlers is still limited; it's a cheap, standards-track bet — worth shipping for content/docs/product sites, not worth agonizing over.

## 6. Design patterns for agent-operable sites

Beyond passing audits, these make task completion by agents reliable:

- **State in the URL.** Search filters, pagination, selected tab, product variant — as query params/paths. Agents (and users) can then deep-link, retry, and verify state. App-state-only-in-JS-memory is a dead end for an agent that navigates.
- **Deterministic, idempotent flows.** Same inputs → same result; a retried GET must not mutate. Use POST for mutations with clear success/failure pages or ARIA live-region confirmation.
- **Errors as text, in the DOM, associated with the field** (`aria-describedby`), not toast-only or color-only.
- **Forms that say what they want**: input `type`/`autocomplete` attributes, visible constraints ("YYYY-MM-DD"), server-side validation regardless (agents will send weird input; so do humans).
- **Don't gate content behind interaction theatrics**: hover-only menus, scroll-triggered reveal of critical info, and canvas-rendered text are all invisible or unreliable for agents.
- **Progressive enhancement**: if core content and primary actions work without JS, every consumption mode works. This is the single highest-leverage principle.
- **Machine-readable duplicates where cheap**: structured data (see `references/seo.md`), and WebMCP tools for the top user tasks (see `references/webmcp.md`).
- **Bot policy coherence**: if the goal is agent traffic, ensure robots.txt/WAF/bot-detection aren't blocking AI user agents; many "agent-ready" projects fail here at the infrastructure layer, not the markup layer.

## 7. Honest framing for users

When reporting on agent readiness: distinguish (a) **fundamentals** — accessibility tree, stability, crawlable content — proven, benefit humans today; (b) **emerging surfaces** — llms.txt, WebMCP — cheap and standards-aligned but with limited real-world agent adoption so far; and (c) **the category score itself** — under active development, so treat it as directional, not contractual. Recommend investing in (a) unconditionally and (b) proportionally to how much the user's strategy bets on agent traffic.
