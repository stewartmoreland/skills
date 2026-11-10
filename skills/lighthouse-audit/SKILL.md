---
name: lighthouse-audit
description: >-
  Drive site development and automated auditing with Google Lighthouse (v13+),
  covering performance/Core Web Vitals, SEO, accessibility, best practices, and
  the new Agentic Browsing category (WebMCP, llms.txt, accessibility tree,
  agent-friendly UX). Use this skill whenever the user mentions Lighthouse,
  PageSpeed Insights, Core Web Vitals (LCP/INP/CLS), page speed, performance
  scores or budgets, SEO audits, WebMCP / navigator.modelContext, llms.txt,
  making a site "AI-agent-ready" or "agent-accessible", or wants CI-based
  quality gates (Lighthouse CI) — and also proactively when building or
  reviewing any website/webapp where performance, SEO, or agent readiness
  matters, even if they never say the word "Lighthouse".
---

# Lighthouse Audit & Agent-Ready Site Development

A skill for using Google Lighthouse as the quality backbone of site development: run audits, interpret the modern insight-based results, fix what matters (in weighted-impact order), build pages that pass on the first try, and wire audits into CI so quality never regresses. It also covers the 2026 frontier: making sites usable by AI agents via the Agentic Browsing category, WebMCP tools, llms.txt, and a well-formed accessibility tree.

## What changed recently (don't rely on stale training data)

- **Lighthouse 13 (Oct 2025)** replaced most legacy performance audits with consolidated **insight audits** whose IDs match Chrome DevTools (e.g. `cls-culprits-insight`, `lcp-discovery-insight`, `lcp-phases-insight`, `document-latency-insight`, `image-delivery-insight`, `third-parties-insight`, `render-blocking-insight`, `interaction-to-next-paint-insight`). Old audit IDs like `layout-shifts`, `uses-rel-preload`, `offscreen-images`, `first-meaningful-paint`, and `font-size` are **gone from the JSON**. Any automation keyed to old IDs is broken. Scoring math is unchanged.
- **Lighthouse 13.3 (May 2026)** added an **Agentic Browsing** category (marked "under development") that checks accessibility-tree well-formedness, WebMCP implementation, llms.txt guidelines, and layout stability for agents.
- Lighthouse 13 requires **Node 22.19+**.
- **INP** (Interaction to Next Paint, ≤200ms) is the responsiveness Core Web Vital. In lab runs Lighthouse can't measure real interactions, so **TBT** (Total Blocking Time) is the scored lab proxy.

When exact audit IDs, category IDs, or flags matter (they do, for automation), don't guess from memory — enumerate them from a real report JSON or `lighthouse --list-all-audits` / `--list-all-categories`. Lighthouse evolves fast and hardcoded IDs are the #1 cause of broken dashboards.

## Two modes of work

**1. Development mode — build it right the first time.** When writing or modifying site code, apply the best practices from the reference files *while coding*, then verify with an audit. Retrofitting performance is far more expensive than building for it. Before writing significant frontend code, skim the relevant reference file(s) below.

**2. Audit mode — measure, prioritize, fix, re-measure.** When asked to audit or improve an existing site, follow the audit loop below.

## Quick start: running an audit

```bash
# Requires Node 22.19+. Install once:
npm install -g lighthouse@latest

# Standard audit (mobile emulation is the default and what Google indexes by):
lighthouse https://example.com \
  --output=json --output-path=./report.json \
  --chrome-flags="--headless=new --no-sandbox" \
  --quiet

# Desktop run when the site is desktop-first:
lighthouse https://example.com --preset=desktop --output=json --output-path=./report-desktop.json --chrome-flags="--headless=new --no-sandbox"

# Limit categories to speed up iteration:
lighthouse https://example.com --only-categories=performance,seo --output=json --output-path=./report.json --chrome-flags="--headless=new --no-sandbox"
```

Notes that save time:

- Local dev servers work: `lighthouse http://localhost:3000/...`. Audit the **production build** (`next build && next start`, `vite build && vite preview`) — dev servers give meaningless performance numbers.
- `--headless=new` is required in containers/CI; add `--no-sandbox` only in sandboxed CI containers where Chrome can't create its own sandbox.
- If Chrome isn't installed, install `chromium` via the system package manager and point Lighthouse at it with `CHROME_PATH=/usr/bin/chromium`.
- Scores vary run-to-run (network, CPU contention). For any decision or CI gate, run **3–5 times and use the median**. Never conclude "my fix worked" from a single run showing a 2-point change.

## Reading the report (as an agent, never eyeball the raw JSON)

A Lighthouse JSON report is 500KB–2MB. Do not `cat` it into context. Use the bundled summarizer:

```bash
node scripts/summarize_report.mjs ./report.json            # scores + failing audits, weighted
node scripts/summarize_report.mjs ./report.json --all      # include passing audits
node scripts/summarize_report.mjs ./report.json --category performance
node scripts/summarize_report.mjs ./report.json --audit lcp-phases-insight   # full detail for one audit
```

It prints category scores, the key metrics with values, and failing/informative audits sorted by score-weight impact, plus each audit's `details` items (the specific URLs/nodes/bytes to fix). If you need something the summarizer doesn't surface, query the JSON surgically with `jq` (e.g. `jq '.audits | keys'`, `jq '.audits["cls-culprits-insight"]'`).

Score bands: **0–49 poor, 50–89 needs improvement, 90–100 good**. Performance score weights (v10+): **TBT 30%, LCP 25%, CLS 25%, FCP 10%, Speed Index 10%** — this ordering tells you where to spend effort.

## The audit loop

1. **Baseline.** Run 3 audits, take the median report. Summarize it. Record the numbers before touching anything.
2. **Prioritize.** Fix in order of (metric weight × distance from "good"). A TBT of 1,800ms outranks a missing meta description every time. Within performance, use the insight audits' estimated savings.
3. **Fix one class of problem at a time**, consulting the matching reference file (below) for the concrete fix patterns.
4. **Re-audit and compare** against the baseline. Attribute changes honestly — a ±3 point swing is noise.
5. **Lock it in.** Once targets are met, set up Lighthouse CI with assertions/budgets so regressions fail the build (see `references/ci-automation.md`).

When reporting results to the user, show before → after for each category score and each Core Web Vital, and list what was changed. Numbers without the causal story aren't useful.

## Reference files — read the one matching the task

| File | Read when |
|---|---|
| `references/performance.md` | Fixing performance scores, Core Web Vitals (LCP/INP/CLS/TBT), insight audits, image/JS/CSS/font optimization, framework-specific patterns |
| `references/seo.md` | SEO category audits, crawlability, structured data, rendering strategy (SSR/SSG), and AI-search/answer-engine visibility |
| `references/agent-readiness.md` | Agentic Browsing category, accessibility-tree quality, llms.txt authoring, designing pages AI agents can operate |
| `references/webmcp.md` | Implementing or validating WebMCP — declarative form annotations or `navigator.modelContext` tools, lifecycle, security |
| `references/ci-automation.md` | Lighthouse CI, performance budgets, assertions, GitHub Actions, programmatic Node API, PageSpeed Insights API |

For a full-site build or comprehensive audit, expect to consult several. For accessibility specifically: Lighthouse's accessibility category is automated-checks-only (axe-core subset) and catches roughly a third of real issues — treat 100/100 as "no detected failures", not "accessible". The agent-readiness reference covers why this matters doubly for AI agents.

## Development-mode checklist (apply while writing code)

Performance: set explicit `width`/`height` (or `aspect-ratio`) on images and embeds; use modern formats (AVIF/WebP) and responsive `srcset`; lazy-load below-the-fold images but **never** the LCP image (give it `fetchpriority="high"`); self-host fonts with `font-display: swap` and preload the one or two that render above the fold; code-split routes and defer non-critical JS; keep third-party scripts out of the critical path (async/defer, or load post-interaction).

SEO: one `<title>` and `<meta name="description">` per page, unique and descriptive; real `<a href>` links (not click-handler divs); `robots.txt` valid; canonical URLs; structured data where content types match schema.org.

Agent readiness: semantic HTML first (real `<button>`, `<label for>`, `<nav>`, headings in order); state reflected in the URL; stable layout (CLS ≤ 0.1); llms.txt if the site has content agents should discover; WebMCP tools for the site's key actions if agent interaction is a goal.

These are the compressed versions — the reference files carry the reasoning, thresholds, and code patterns.
