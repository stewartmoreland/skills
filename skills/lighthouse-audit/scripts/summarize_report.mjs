#!/usr/bin/env node
/**
 * summarize_report.mjs — Compact, agent-readable summary of a Lighthouse JSON report.
 *
 * Lighthouse reports are 500KB–2MB; never load them into an LLM context raw.
 * This prints: category scores, key metrics, and failing/informative audits
 * sorted by weighted impact, with the top detail items (URLs, bytes, ms) per audit.
 *
 * Usage:
 *   node summarize_report.mjs <report.json> [--all] [--category <id>] [--audit <id>] [--top <n>]
 *     --all            include passing audits in the listing
 *     --category <id>  only summarize one category (performance, seo, accessibility,
 *                      best-practices, or e.g. the agentic browsing category id)
 *     --audit <id>     print full JSON details for a single audit and exit
 *     --top <n>        detail items to show per audit (default 5)
 */

import { readFileSync } from 'node:fs';

const args = process.argv.slice(2);
const file = args.find((a) => !a.startsWith('--'));
if (!file) {
  console.error('Usage: node summarize_report.mjs <report.json> [--all] [--category <id>] [--audit <id>] [--top <n>]');
  process.exit(1);
}
const flag = (name) => {
  const i = args.indexOf(`--${name}`);
  return i !== -1 ? args[i + 1] : undefined;
};
const showAll = args.includes('--all');
const onlyCategory = flag('category');
const onlyAudit = flag('audit');
const topN = parseInt(flag('top') ?? '5', 10);

let lhr;
try {
  lhr = JSON.parse(readFileSync(file, 'utf8'));
} catch (e) {
  console.error(`Could not read/parse ${file}: ${e.message}`);
  process.exit(1);
}
// LHCI wraps reports sometimes; PSI nests under lighthouseResult.
if (lhr.lighthouseResult) lhr = lhr.lighthouseResult;
if (!lhr.audits || !lhr.categories) {
  console.error('This does not look like a Lighthouse report (missing .audits/.categories).');
  process.exit(1);
}

if (onlyAudit) {
  const a = lhr.audits[onlyAudit];
  if (!a) {
    console.error(`No audit "${onlyAudit}". Available ids:\n` + Object.keys(lhr.audits).sort().join('\n'));
    process.exit(1);
  }
  console.log(JSON.stringify(a, null, 2));
  process.exit(0);
}

const pct = (s) => (s == null ? 'n/a' : Math.round(s * 100));
const band = (s) => (s == null ? '·' : s >= 0.9 ? 'GOOD' : s >= 0.5 ? 'NEEDS WORK' : 'POOR');

console.log(`# Lighthouse summary`);
console.log(`URL: ${lhr.finalDisplayedUrl || lhr.finalUrl || lhr.requestedUrl}`);
console.log(`Lighthouse: v${lhr.lighthouseVersion}  |  Fetched: ${lhr.fetchTime}  |  Form factor: ${lhr.configSettings?.formFactor ?? '?'}`);
if (lhr.runWarnings?.length) console.log(`Run warnings: ${lhr.runWarnings.join(' | ')}`);
console.log('');

// ---- Category scores ----
console.log('## Category scores');
for (const [id, cat] of Object.entries(lhr.categories)) {
  console.log(`- ${cat.title} (${id}): ${pct(cat.score)}  [${band(cat.score)}]`);
}
console.log('');

// ---- Key metrics ----
const metricIds = [
  'first-contentful-paint',
  'largest-contentful-paint',
  'total-blocking-time',
  'cumulative-layout-shift',
  'speed-index',
  'interactive',
  'interaction-to-next-paint',
];
const metrics = metricIds.map((id) => lhr.audits[id]).filter(Boolean);
if (metrics.length) {
  console.log('## Key metrics');
  for (const m of metrics) {
    console.log(`- ${m.title}: ${m.displayValue ?? m.numericValue ?? 'n/a'}  (score ${pct(m.score)})`);
  }
  console.log('');
}

// ---- Per-category audit listing ----
const fmtBytes = (b) => (b >= 1048576 ? (b / 1048576).toFixed(1) + ' MiB' : (b / 1024).toFixed(0) + ' KiB');
const itemLabel = (item) => {
  const parts = [];
  const urlish = item.url || item.source?.url || item.node?.selector || item.node?.snippet || item.name || item.label || item.origin || item.entity;
  if (urlish) parts.push(String(urlish).slice(0, 110));
  if (typeof item.wastedBytes === 'number') parts.push(`wasted ${fmtBytes(item.wastedBytes)}`);
  else if (typeof item.totalBytes === 'number') parts.push(fmtBytes(item.totalBytes));
  if (typeof item.wastedMs === 'number') parts.push(`~${Math.round(item.wastedMs)}ms`);
  if (typeof item.blockingTime === 'number' && item.blockingTime > 0) parts.push(`blocking ${Math.round(item.blockingTime)}ms`);
  if (typeof item.score === 'number') parts.push(`shift ${item.score}`);
  return parts.join('  |  ') || JSON.stringify(item).slice(0, 110);
};

for (const [catId, cat] of Object.entries(lhr.categories)) {
  if (onlyCategory && catId !== onlyCategory) continue;

  const rows = (cat.auditRefs || [])
    .map((ref) => ({ ref, audit: lhr.audits[ref.id] }))
    .filter(({ audit }) => audit);

  const failing = rows.filter(({ audit }) => {
    if (audit.scoreDisplayMode === 'notApplicable' || audit.scoreDisplayMode === 'manual') return false;
    if (audit.scoreDisplayMode === 'informative') return (audit.details?.items?.length ?? 0) > 0;
    if (audit.scoreDisplayMode === 'error') return true;
    return audit.score != null && audit.score < 0.9;
  });
  const passing = rows.filter((r) => !failing.includes(r) && r.audit.scoreDisplayMode !== 'notApplicable' && r.audit.scoreDisplayMode !== 'manual');

  // weighted impact: weight * (1 - score); informative/error get weight-order fallback
  failing.sort((a, b) => {
    const impact = ({ ref, audit }) => (ref.weight || 0.001) * (1 - (audit.score ?? 0));
    return impact(b) - impact(a);
  });

  console.log(`## ${cat.title} — ${pct(cat.score)} (${failing.length} flagged / ${rows.length} audits)`);
  for (const { ref, audit } of failing) {
    const mode = audit.scoreDisplayMode === 'informative' ? 'INFO' : audit.scoreDisplayMode === 'error' ? 'ERROR' : `score ${pct(audit.score)}`;
    const weight = ref.weight ? `, weight ${ref.weight}` : '';
    console.log(`\n### ✗ ${audit.id} — ${audit.title} (${mode}${weight})`);
    if (audit.displayValue) console.log(`   ${audit.displayValue}`);
    if (audit.errorMessage) console.log(`   error: ${audit.errorMessage}`);
    const items = audit.details?.items ?? [];
    for (const item of items.slice(0, topN)) console.log(`   - ${itemLabel(item)}`);
    if (items.length > topN) console.log(`   … ${items.length - topN} more (use --audit ${audit.id} for full detail)`);
  }
  if (showAll && passing.length) {
    console.log(`\nPassing: ${passing.map((r) => r.audit.id).join(', ')}`);
  }
  console.log('');
}

// ---- Budgets, if present ----
for (const id of ['performance-budget', 'timing-budget']) {
  const a = lhr.audits[id];
  if (a?.details?.items?.length) {
    console.log(`## ${a.title}`);
    for (const item of a.details.items) console.log(`- ${itemLabel(item)}`);
    console.log('');
  }
}

console.log('Tip: full detail for any audit: --audit <id>. List all ids: jq ".audits | keys" ' + file);
