# SEO: Lighthouse Audits, Crawlability, and AI-Search Visibility

## Contents
1. What the Lighthouse SEO category actually checks (and doesn't)
2. Fixing each audit class
3. Rendering strategy — the SEO decision Lighthouse can't see
4. Structured data
5. AI search / answer-engine visibility (AEO/GEO)

---

## 1. Scope of the Lighthouse SEO category

Lighthouse SEO is a **baseline technical hygiene check**, not an SEO analysis. It verifies a crawler can fetch, parse, and understand the page. A 100 score means "not technically broken", nothing about content quality, authority, or rankings. Never tell a user that 100/100 means their SEO is "done".

The category checks cluster into: crawlability (HTTP status, `is-crawlable`/robots blocking, valid `robots.txt`), content basics (`document-title`, `meta-description`, descriptive `link-text`, `crawlable-anchors`), internationalization (`hreflang`), canonicalization (`canonical`), and mobile-friendliness (viewport, legible content). Structured data is a **manual** audit — Lighthouse lists it but doesn't validate it; use the Rich Results Test / schema.org validator.

Enumerate the current audit set from a report (`jq '.categories.seo.auditRefs' report.json`) rather than assuming — the set shifts between versions (e.g. `font-size` was removed in v13 as no longer a signal).

## 2. Fixing each audit class

**Crawlability**
- Page must return 200 (not soft-404s: a "not found" page served with 200 confuses crawlers and agents alike).
- `is-crawlable` fails on `<meta name="robots" content="noindex">` or `X-Robots-Tag` headers — a routine leak from staging configs. Check the deployment pipeline, not just the HTML.
- `robots.txt` must parse; don't block CSS/JS (Google renders pages; blocked assets = broken rendered view).
- Every navigable destination needs a real `<a href="...">`. `onClick`-only divs and `href="#"` + JS routing are invisible to crawlers and to AI agents reading the accessibility tree. Client-side routers: use their Link components which render real anchors.

**Content basics**
- `<title>`: unique per page, front-load the distinctive part, ~50–60 chars visible.
- Meta description: unique, ~150–160 chars, written as the answer/pitch that earns the click. Auto-generate sensibly for templated pages (product name + differentiator), never duplicate site-wide.
- Link text: "read the pricing guide" not "click here" — descriptive anchors are also how agents decide where to navigate.
- One `<h1>` per page describing the page (also required by llms.txt conventions and heading-order accessibility checks — the same discipline pays three times).

**Canonical & i18n**
- `rel="canonical"`: absolute URL, self-referencing on canonical pages, one per page, consistent with sitemap and internal links. Paginated/filtered/UTM'd URLs canonicalize to the clean version.
- `hreflang`: bidirectional (every referenced page links back), include `x-default`, use correct ISO codes.

## 3. Rendering strategy — the decision Lighthouse can't see

Lighthouse audits the rendered page it loaded, so a client-side-rendered SPA can score 100 on SEO while being fragile in real indexing (render queue delays, timeouts, non-Google crawlers and most AI crawlers that don't execute JS at all).

Rule of thumb for pages whose content should be discoverable (marketing, docs, blog, product pages): **content must be in the initial HTML response** — SSG for stable content, SSR/ISR for dynamic. Reserve pure CSR for authenticated app surfaces where indexing is irrelevant. Verify with `curl` or "view source" (not DevTools elements panel): if the content isn't in the raw HTML, most AI crawlers never see it.

## 4. Structured data

Add JSON-LD (in `<head>` or body) for types the page genuinely is: `Article`, `Product` (+ `Offer`, `AggregateRating`), `FAQPage`, `HowTo`, `Organization`, `BreadcrumbList`, `SoftwareApplication`, `LocalBusiness`. Benefits: rich results in classic search *and* cleaner entity extraction for AI systems.

Rules: describe only content visible on the page (invisible-content markup risks manual actions); validate with the Rich Results Test; keep `@id`/`url` consistent with canonicals; templatize so every entity page emits it automatically.

## 5. AI search / answer-engine visibility

AI assistants and answer engines are now a meaningful discovery channel. The practices that help are mostly "classic SEO done honestly", plus a few new surfaces:

- **Be parseable without JS** (see §3) — most LLM crawlers fetch raw HTML.
- **Semantic structure**: proper headings, lists, tables; self-contained sections that make sense when quoted in isolation (answer-shaped content gets cited).
- **Entity clarity**: consistent naming, an About/Organization page, `Organization` + `sameAs` structured data — helps models attribute facts to you.
- **robots.txt policy for AI crawlers**: decide deliberately whether to allow `GPTBot`, `ClaudeBot`, `PerplexityBot`, `Google-Extended`, etc. Blocking them removes you from AI answers; that's a business decision, make it explicit rather than by default.
- **llms.txt**: a proposed markdown manifest at `/llms.txt` pointing agents to your key content. Adoption by AI tools is limited so far, but Lighthouse's Agentic Browsing category now checks its format — see `references/agent-readiness.md` for authoring rules.
- **WebMCP**: exposing site actions as tools makes the site *operable*, not just readable, by agents — see `references/webmcp.md`.

Keep expectations honest with users: llms.txt and WebMCP are early-stage, low-cost, forward-looking bets, not proven traffic drivers. Crawlable content, structured data, and fast pages are the proven part.
