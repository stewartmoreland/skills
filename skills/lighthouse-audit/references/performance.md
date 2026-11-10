# Performance: Core Web Vitals & Lighthouse Insight Audits

## Contents
1. Metrics & targets
2. Lab vs field data
3. The insight audits (Lighthouse 13+) and how to fix each
4. Fix patterns by resource type
5. Framework-specific notes
6. Prioritization heuristics

---

## 1. Metrics & targets

| Metric | Good | Poor | What it measures | Perf score weight (lab) |
|---|---|---|---|---|
| LCP (Largest Contentful Paint) | ≤ 2.5s | > 4.0s | Loading — when the biggest above-fold element renders | 25% |
| INP (Interaction to Next Paint) | ≤ 200ms | > 500ms | Responsiveness — worst interaction latency (field only) | — (TBT is lab proxy) |
| CLS (Cumulative Layout Shift) | ≤ 0.1 | > 0.25 | Visual stability | 25% |
| TBT (Total Blocking Time) | ≤ 200ms | > 600ms | Lab proxy for INP — main-thread blocking after FCP | 30% |
| FCP (First Contentful Paint) | ≤ 1.8s | > 3.0s | First render | 10% |
| Speed Index | ≤ 3.4s | > 5.8s | Visual completeness over time | 10% |

Core Web Vitals (the field trio Google uses as a ranking signal) = **LCP, INP, CLS**, measured at the 75th percentile of real users. INP replaced FID in March 2024.

Lighthouse scores are log-normal curves per metric, combined by the weights above. Practical consequence: **TBT, LCP, and CLS control 80% of the performance score.** Chasing FCP or Speed Index in isolation is usually wasted effort.

## 2. Lab vs field data

- **Lab (Lighthouse):** controlled, reproducible, throttled (default: mobile emulation, slow 4G, 4× CPU slowdown). Great for debugging and CI gates. Cannot measure INP.
- **Field (CrUX / RUM):** what real users experience; what search ranking uses. Check via PageSpeed Insights (which shows CrUX field data above the Lighthouse lab run) or the CrUX API.

If lab and field disagree, field wins for prioritization. Common case: great lab LCP but poor field INP — lab can't see post-load interaction jank; go hunt long tasks and heavy event handlers.

## 3. Insight audits (Lighthouse 13+) and fixes

Lighthouse 13 consolidated legacy performance audits into insight audits shared with the DevTools Performance panel. The performance **score** comes only from the six metrics; insights are the non-scored diagnostics telling you *why* metrics are bad. Confirmed insight IDs and their fix directions:

**`lcp-discovery-insight`** — Was the LCP resource discoverable early? Failures: LCP image lazy-loaded, injected by JS, or hidden behind CSS background-image. Fixes: put the LCP image in initial HTML as `<img>`, add `fetchpriority="high"`, never `loading="lazy"` on it; if it must be a background, add `<link rel="preload" as="image">`.

**`lcp-phases-insight`** — Breaks LCP into TTFB → load delay → load time → render delay. Fix the dominant phase: high TTFB → server/CDN/caching (see document-latency); load delay → discovery (above); load time → image size/format/CDN; render delay → render-blocking resources or client-side rendering of the hero.

**`cls-culprits-insight`** — Which nodes shifted and why (consolidates old `layout-shifts` + causes). Fixes: explicit dimensions or `aspect-ratio` on images/video/iframes/ads; reserve space for dynamic content (skeletons with fixed size); `font-display: swap` + font metric overrides (`size-adjust`, `ascent-override`) to prevent swap-shift; never insert content above existing content except on user interaction; animate with `transform`, not layout properties. (`unsized-images` and `non-composited-animations` still exist as separate diagnostics.)

**`interaction-to-next-paint-insight`** — Interaction latency causes. Fixes: break long tasks (>50ms) with `scheduler.yield()` / `setTimeout` chunking; debounce input handlers; move heavy work to Web Workers; reduce DOM size so style/layout recalc is cheap; `content-visibility: auto` for off-screen sections; avoid re-rendering entire component trees on keystroke (memoize, split state).

**`document-latency-insight`** — Consolidates redirects + server response time + text compression. Fixes: eliminate redirect chains (audit every marketing link and http→https→www hop); TTFB < 600ms via CDN, edge rendering, or caching HTML; enable Brotli/gzip for all text responses.

**`image-delivery-insight`** — Consolidates format/sizing/optimization/animated-content audits. Fixes: AVIF or WebP with fallbacks (`<picture>`); `srcset`/`sizes` so devices download appropriately-sized files; compress (quality 60–80 usually indistinguishable); replace animated GIFs with `<video muted autoplay loop playsinline>`; use an image CDN for on-the-fly transforms.

**`render-blocking-insight`** — CSS/JS blocking first paint. Fixes: inline critical CSS, load the rest with `media="print" onload` swap or split by route; `defer`/`async` all scripts (or `type="module"`, deferred by default); remove unused CSS (coverage tab / PurgeCSS-class tooling).

**`third-parties-insight`** — Cost of each third-party origin. Fixes: remove what isn't earning its keep (measure!); load tag managers/chat/analytics after load or on interaction ("facade" pattern for embeds like YouTube); self-host critical third-party assets; `preconnect` only to origins actually used pre-load.

**Other consolidated insights** cover DOM size, duplicated JavaScript (multiple bundle copies of the same lib — fix dedupe/aliasing in the bundler), font display, legacy JavaScript (drop old polyfills/transpilation targets; set browserslist to modern baseline), network dependency trees (flatten critical chains; `preconnect`/`preload` the deep links), caching (long `max-age` + content-hashed filenames for static assets), HTTP/2+ and modern HTTPS, and viewport configuration (`<meta name="viewport" content="width=device-width, initial-scale=1">` — its absence also adds a 300ms tap delay penalty to INP).

**Removed in 13 (do not reference, do not assert on):** `first-meaningful-paint`, `font-size`, `offscreen-images`, `preload-fonts`, `uses-rel-preload`, `no-document-write`, `uses-passive-event-listeners`, `third-party-facades`.

To enumerate what a given Lighthouse version actually ships: `jq '.audits | keys' report.json` or `lighthouse --list-all-audits`.

## 4. Fix patterns by resource type

**Images** (usually the biggest LCP lever): serve ≤ the rendered size × DPR; AVIF/WebP; CDN; explicit dimensions; lazy-load below the fold only; `fetchpriority="high"` + eager on the hero.

**JavaScript** (usually the biggest TBT/INP lever): ship less — route-level code splitting, dynamic `import()` for below-fold/interaction-gated features, tree-shakeable imports (`import { x } from 'lib'`), audit bundle with a visualizer before optimizing; hydrate less (islands/server components); defer everything non-critical.

**CSS:** critical CSS inline (< 14KB ideally), rest async; avoid `@import` chains; contain expensive selectors; `content-visibility: auto` for long pages.

**Fonts:** self-host (third-party font CSS adds a connection + redirect chain); WOFF2 only; `font-display: swap` (or `optional` for non-brand fonts); preload only above-fold-critical faces; subset (unicode-range) large families.

**HTML/server:** compress (Brotli); stream HTML early; cache at the edge; `103 Early Hints` where supported; avoid client-side-only rendering for content pages.

## 5. Framework-specific notes

- **Next.js:** use `next/image` (handles sizing/format/lazy automatically — set `priority` on the LCP image), `next/font` (self-hosts + metric overrides = zero font CLS), `next/script` with `strategy="lazyOnload"` or `afterInteractive` for third parties. Prefer Server Components / SSG for content; keep `"use client"` boundaries small. `next build && next start` before auditing.
- **Vite/React SPA:** SPAs start with an LCP/SEO handicap on content pages — consider prerendering or SSR (e.g. vite-ssg, React Router framework mode/Remix) if content pages matter. `React.lazy` + route splitting; audit `vite build` output with rollup-plugin-visualizer.
- **Astro:** islands architecture is already the right default; watch third-party scripts and image sizing.
- **WordPress/other CMS:** page cache + Brotli, image CDN plugin, defer plugin JS, limit plugin count — third-parties-insight will name the offenders.

## 6. Prioritization heuristics

1. Read the metric values first, not the audit list. Fix the worst-scoring heavy-weight metric (TBT/LCP/CLS).
2. Within a metric, the matching insight audit lists culprits with estimated savings — fix the top items, ignore sub-100ms opportunities until the big ones are done.
3. One change class per re-audit cycle, or you can't attribute improvements.
4. Stop optimizing lab score at ~90–95; past that, invest in field data (RUM) and INP instead — a 100 lab score with poor field INP is a worse outcome than 92 with green CWV.
