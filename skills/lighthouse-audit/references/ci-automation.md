# Automated Auditing: Lighthouse CI, Budgets, and Programmatic Use

## Contents
1. Choosing the automation approach
2. Lighthouse CI (@lhci/cli) — the default answer
3. Assertions & performance budgets
4. GitHub Actions patterns
5. Programmatic Node API
6. PageSpeed Insights API (remote + field data)
7. Variance control & anti-flake rules
8. Lighthouse 13 migration notes for existing pipelines

---

## 1. Choosing the approach

| Need | Use |
|---|---|
| PR gate: "don't merge regressions" | **Lighthouse CI** with assertions |
| Track scores over time, compare commits | Lighthouse CI + LHCI server or temporary-public-storage |
| Custom orchestration (auth flows, multi-step, custom metrics) | **Programmatic Node API** |
| Audit production remotely + get field (CrUX) data | **PageSpeed Insights API** |
| One-off local check | plain `lighthouse` CLI |

## 2. Lighthouse CI

```bash
npm i -D @lhci/cli
```

`lighthouserc.js` at repo root:

```js
module.exports = {
  ci: {
    collect: {
      // Static build:
      staticDistDir: './dist',
      // OR a server: startServerCommand: 'npm run start', url: ['http://localhost:3000/', 'http://localhost:3000/pricing'],
      numberOfRuns: 3,
      settings: {
        chromeFlags: '--headless=new --no-sandbox',
        // preset: 'desktop',            // if desktop-first
        // onlyCategories: ['performance','seo','accessibility','best-practices'],
      },
    },
    assert: {
      preset: 'lighthouse:recommended',   // strict; or 'lighthouse:no-pwa'
      assertions: {
        // Category floors:
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.95 }],
        'categories:seo': ['error', { minScore: 0.95 }],
        // Metric budgets (ms / unitless):
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'total-blocking-time': ['error', { maxNumericValue: 300 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        // Downgrade noisy checks:
        'third-parties-insight': ['warn', {}],
      },
    },
    upload: { target: 'temporary-public-storage' }, // or your LHCI server / filesystem
  },
};
```

Run: `lhci autorun`. It builds nothing itself — collect against a **production build**. Audit 2–5 representative URLs (home, one content page, one heavy template), not the whole sitemap.

`numberOfRuns: 3` makes assertions run against the median — this is the main flake defense; never gate on 1 run.

## 3. Assertions & budgets

Two complementary layers:

- **Assertions** (above): scores, metric values, and per-audit pass/fail. Assertion keys are **audit IDs** — with Lighthouse 13 that means insight IDs (`cls-culprits-insight`, not `layout-shifts`). Get valid IDs from a fresh report: `jq '.audits | keys' report.json`.
- **Resource budgets** (`budgets.json`, passed via `settings.budgets` or `--budget-path`): caps on byte sizes and request counts per resource type — the earliest tripwire for dependency creep:

```json
[{
  "path": "/*",
  "resourceSizes": [
    { "resourceType": "script",     "budget": 300 },
    { "resourceType": "image",      "budget": 500 },
    { "resourceType": "stylesheet", "budget": 100 },
    { "resourceType": "total",      "budget": 1200 }
  ],
  "resourceCounts": [
    { "resourceType": "third-party", "budget": 10 }
  ]
}]
```

(Sizes in KiB.) Budget results appear in the report's `performance-budget` / `timing-budget` sections.

Budget-setting method: measure current medians, set budgets ~10% above current (ratchet, don't aspire), tighten quarterly. Aspirational budgets that fail from day one get deleted by the team within a month.

## 4. GitHub Actions

```yaml
name: Lighthouse CI
on: [pull_request]
jobs:
  lhci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22 }   # Lighthouse 13 needs >= 22.19
      - run: npm ci && npm run build
      - run: npx @lhci/cli autorun
        env:
          LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}  # optional: PR status checks
```

Alternative: the maintained `treosh/lighthouse-ci-action` wraps collect+assert+upload with artifact storage. For monorepos, run per-app with separate configs. CI runners are slow and shared — expect worse absolute numbers than local; budget against CI's own baseline, and consider `settings.throttlingMethod: 'devtools'` consistency issues before comparing across runner types.

## 5. Programmatic Node API

For custom flows (authenticated pages, warm-cache runs, scripted navigation):

```js
import { launch } from 'chrome-launcher';
import lighthouse from 'lighthouse';

const chrome = await launch({ chromeFlags: ['--headless=new'] });
const { lhr } = await lighthouse('https://example.com', {
  port: chrome.port,
  output: 'json',
  onlyCategories: ['performance', 'seo'],
});
console.log(lhr.categories.performance.score * 100);
await chrome.kill();
```

`lhr` is the same object as the JSON report (`lhr.audits[id].numericValue`, `.score`, `.details.items`). For authenticated audits: launch Puppeteer/Playwright, perform login, then run Lighthouse against the same browser via its port — or use Lighthouse user flows (`lighthouse` `startFlow` API) for multi-step timespan/snapshot audits that can capture real interactions (the only lab way to approximate INP).

## 6. PageSpeed Insights API

```bash
curl "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://example.com&strategy=mobile&category=performance&category=seo&key=$API_KEY"
```

Returns `lighthouseResult` (lab, possibly an older Lighthouse version than npm) plus `loadingExperience` (CrUX field data — real-user LCP/INP/CLS). Use for production monitoring and for the field data that lab runs can't provide. Rate-limited; get an API key for anything scheduled.

## 7. Variance control & anti-flake rules

- Median of ≥3 runs, always.
- Pin the Lighthouse/@lhci version in package.json; upgrade deliberately (major versions change audits — see §8).
- Same machine class per comparison; don't compare laptop numbers to CI numbers.
- Warm the server before collecting (LHCI's startServerCommand waits for the port, but do one throwaway request for JIT/caches).
- Assert on metrics and scores (stable) more than on individual audit pass/fail (churny), except where an audit encodes a hard requirement.
- Quarantine known-noisy third parties with `warn` severity rather than deleting the assertion — visibility without flake.

## 8. Lighthouse 13 migration notes

If maintaining an existing pipeline: (1) old audit IDs are gone from JSON — remap assertions to insight IDs; (2) removed-with-no-replacement audits (`uses-rel-preload`, `offscreen-images`, `first-meaningful-paint`, `font-size`, `preload-fonts`, `no-document-write`, `uses-passive-event-listeners`, `third-party-facades`) must be deleted from configs or LHCI errors on unknown keys; (3) scores are unaffected — dashboards tracking category scores need no change; (4) combined insights can't be partially disabled (disabling one former sub-audit means deciding about the whole insight); (5) Node 22.19+ in CI images; (6) the Agentic Browsing category (13.3+) is under development — surface it as informational, don't gate on it yet.
