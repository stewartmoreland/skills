# WebMCP: Exposing Site Actions as Tools for AI Agents

## Contents
1. Status & mental model (read this before promising anything to users)
2. Imperative API — `navigator.modelContext`
3. Declarative API — annotated forms
4. Lifecycle in SPAs
5. What tools to expose & how to describe them
6. Security model & server-side rules
7. Feature detection, polyfill, testing, and the Lighthouse audit

---

## 1. Status & mental model

**WebMCP (Web Model Context Protocol)** is a W3C Web Machine Learning Community Group draft (first announced Feb 10, 2026; Google + Microsoft co-authored) that lets a web page register JavaScript functions as structured **tools** that in-browser AI agents can discover and call — instead of screenshotting and simulated clicking. Think of the page as a client-side MCP server: same vocabulary as Anthropic's MCP (tools, descriptions, JSON Schema inputs) but browser-native (origins, permissions, tab lifecycle) and **not the same protocol**.

Status facts to state accurately (as of mid-2026, verify if it matters):
- Chrome shipped it behind a flag in 146 Canary, then a **public origin trial (Chrome 149+)**. Edge support signaled via co-authorship; Firefox/Safari participating in discussions, nothing shipped.
- It's a **Draft Community Group Report** — expect breaking changes. Notably, the earlier `provideContext()`/`clearContext()` surface was **removed in March 2026**; current surface is `registerTool()`/`unregisterTool()`. If training data or old blog posts show `provideContext`, that's the stale API.
- Tools are **page-scoped**: registered per document, cleared on navigation. No cross-site discovery mechanism yet (a `.well-known` manifest is future work).
- Tools run client-side **in the user's session** — the agent can do what the logged-in user can do, no separate auth.

Consequence for engineering advice: build WebMCP as **progressive enhancement over working UI**, never as the only path to functionality.

## 2. Imperative API

```js
if ('modelContext' in navigator) {
  navigator.modelContext.registerTool({
    name: 'search-flights',
    description:
      'Search available flights. Returns a list of flights with price, times, and a flightId usable with book-flight.',
    inputSchema: {
      type: 'object',
      properties: {
        origin:      { type: 'string', description: 'IATA airport code, e.g. AUS' },
        destination: { type: 'string', description: 'IATA airport code' },
        date:        { type: 'string', format: 'date', description: 'Departure date YYYY-MM-DD' },
        passengers:  { type: 'integer', minimum: 1, maximum: 9, default: 1 }
      },
      required: ['origin', 'destination', 'date'],
      additionalProperties: false
    },
    async execute({ origin, destination, date, passengers = 1 }) {
      const results = await flightApi.search({ origin, destination, date, passengers });
      renderResults(results);            // keep the UI in sync — user and agent share the page
      return {
        content: [{ type: 'text', text: JSON.stringify(results.slice(0, 10)) }]
      };
    }
  });
}
```

Principles baked into that example, worth preserving in any code you write:
- **Reuse existing application logic** (`flightApi.search`) — a tool is a thin adapter, not a parallel implementation.
- **Update the visible UI** inside `execute` — WebMCP's design goal is collaborative human+agent use of the same page; a tool that mutates invisible state breaks the shared-context contract.
- **Return structured, bounded results** (top 10, not 5,000 rows) as text content the model can read; include the IDs needed for follow-up tools.
- **Strict schemas**: `additionalProperties: false`, enums/min/max where applicable, per-property `description`. The schema is the agent's only manual.
- `unregisterTool('search-flights')` when the capability disappears (results page torn down, user logs out).

## 3. Declarative API

For classic forms, annotate the HTML and the browser derives the tool — no JS:

```html
<form action="/newsletter" method="post"
      toolname="subscribe-newsletter"
      tooldescription="Subscribe an email address to the weekly product newsletter">
  <label for="em">Email</label>
  <input id="em" name="email" type="email" required
         tooldescription="Email address to subscribe">
  <button type="submit">Subscribe</button>
</form>
```

Rules the Lighthouse WebMCP audit validates: annotations must match the expected schema — a `toolname` needs a `tooldescription`; annotated controls need names/descriptions. Gotchas observed in the wild: a `display:none` form still registers as a tool (remove it from the DOM or strip `toolname`); vague descriptions ("Submit form") give agents nothing — describe the user intent fulfilled. Attribute names are lowercase (`toolname`, `tooldescription`); verify exact surface against the current spec draft when generating code, since the API is evolving.

Use declarative for simple, stateless form submissions; imperative for anything with app logic, multi-step state, or dynamic availability.

## 4. Lifecycle in SPAs

Tools don't auto-scope to routes. The stale-tool bug — agent calls `add-to-cart` on a route where it no longer applies — is the most common WebMCP defect. Pattern:

```js
// React example: tie registration to component lifecycle
useEffect(() => {
  if (!('modelContext' in navigator)) return;
  navigator.modelContext.registerTool(checkoutTool);
  return () => navigator.modelContext.unregisterTool(checkoutTool.name);
}, [cartId]);
```

Register conditionally on state (expose `checkout` only when the cart is non-empty) — dynamic availability is itself a signal agents use.

## 5. What tools to expose & how to describe them

Expose the **top user tasks**, not the whole API: search/filter, add-to-cart/book/subscribe, get-status/lookup, contact/support-ticket. 3–8 well-described tools beat 40 thin ones (agents pay attention costs per tool). Naming: verb-noun kebab-case. Descriptions: what it does, what it returns, when to use it, relation to other tools ("use flightId from search-flights"). Mark read-only operations as such (the spec's read-only hints let browsers skip confirmation prompts for safe queries).

## 6. Security model & server-side rules

Threat model essentials (from the spec's security considerations):
- **Human-in-the-loop**: browsers confirm sensitive tool executions with the user; design tools assuming a confirmation step may interpose. For irreversible actions (payment, delete), keep your own explicit confirmation step too.
- **Session inheritance cuts both ways**: agents act with the user's cookies/login. Never expose tools that widen what the UI allows.
- **Client-side calls are untrusted, full stop.** Validate and authorize every tool-triggered request on the server exactly like any other request. An "agentInvoked" signal is telemetry, not a credential.
- **Parameter-based data extraction**: the spec flags sites designing greedy parameter schemas to phish personal data out of helpful agents (location, age, etc.). Don't request parameters you don't need — and expect browsers/agents to get stricter about this.
- **Prompt injection surface**: tool results you return are read by a model. Don't echo untrusted third-party content into tool results without sanitization/limits.
- Same-origin scoping applies; tools are only invocable in the page's own origin context.

## 7. Feature detection, polyfill, testing, and the Lighthouse audit

- Always feature-detect (`'modelContext' in navigator`). For cross-browser experiments there's a community polyfill (`@mcp-b/global`, from the MCP-B project that inspired the spec) — treat as experimental.
- Manual testing: Chrome with the WebMCP flag/origin trial enabled; DevTools → Application → WebMCP shows registered tools; the "Model Context Tool Inspector" Chrome extension inspects schemas and debugs calls.
- Automated: Lighthouse 13.3+ Agentic Browsing category (a) validates declarative annotations against the expected schema and (b) enumerates every registered tool on the page (declarative or imperative) — use that list in review to catch stale, duplicate, or unnamed tools.
- Origin trial deployment requires registering for the trial token; don't ship production dependencies on an origin-trial API — feature-detect and degrade gracefully.
