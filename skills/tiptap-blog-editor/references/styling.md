# Styling the Editor (TipTap v3)

Headless means **no default styles for content**. A fresh editor renders `h2`, `blockquote`, `ul`, `code` as unstyled HTML — authors type a heading and see plain text. You style two distinct things: the **content** (what's inside the editor and what readers see) and the **chrome** (toolbar, menus, container). Style content once and reuse it for both editing and published pages so the preview matches the result.

## Content styling: Tailwind Typography (`prose`)

The fastest path to good-looking article content is the official Tailwind Typography plugin. It styles a whole tree of semantic HTML from one class.

```bash
npm install -D @tailwindcss/typography
```

Tailwind v4 (CSS-first config):
```css
@import "tailwindcss";
@plugin "@tailwindcss/typography";
```

Tailwind v3 (`tailwind.config.js`): add `require('@tailwindcss/typography')` to `plugins`.

Apply `prose` to the editor's content area and to the published article — the same classes in both places guarantee the editing surface looks like the final post:

```tsx
editorProps: {
  attributes: {
    class: 'prose prose-neutral dark:prose-invert max-w-none focus:outline-none',
  },
}
```

- `prose-neutral` (or `prose-slate`, etc.) picks the gray ramp; swap for your brand.
- `dark:prose-invert` gives a correct dark-mode ramp — essential for a dark editor.
- `max-w-none` removes Typography's default measure cap so the editor fills its container; keep a sensible reading width on the *published* page instead (e.g. `prose` without `max-w-none`, or a wrapper `max-w-2xl`).
- `focus:outline-none` drops the browser focus ring on the editable region (you'll usually style focus on the container instead).

Tune individual elements with Typography's modifiers (e.g. `prose-headings:font-semibold prose-a:text-primary prose-img:rounded-xl prose-code:before:content-none`) rather than fighting it with overrides.

## When you're not using Tailwind Typography

Style the `.tiptap` content root directly (TipTap adds `class="tiptap"` to the editable element, and you can add your own via `editorProps.attributes.class`). Target the semantic elements:

```css
.tiptap { line-height: 1.7; }
.tiptap h2 { font-size: 1.5rem; font-weight: 600; margin: 1.5em 0 0.5em; }
.tiptap blockquote { border-left: 3px solid var(--border); padding-left: 1rem; color: var(--muted-foreground); }
.tiptap pre { background: #0b0f19; color: #e5e7eb; border-radius: 0.5rem; padding: 1rem; overflow-x: auto; }
.tiptap code { font-family: ui-monospace, monospace; }
.tiptap img { border-radius: 0.5rem; max-width: 100%; height: auto; }
.tiptap ul { list-style: disc; padding-left: 1.25rem; }
.tiptap ol { list-style: decimal; padding-left: 1.25rem; }
```

## Placeholder CSS (required, or the placeholder is invisible)

The Placeholder extension only sets a `data-placeholder` attribute and empty-state classes — the visible hint is pure CSS you must add:

```css
.tiptap p.is-editor-empty:first-child::before {
  content: attr(data-placeholder);
  color: var(--muted-foreground);
  float: left;
  height: 0;
  pointer-events: none;
}
```

Use `.is-empty::before` (without `:first-child`) if you configured per-line placeholders.

## Code block syntax highlighting colors

`lowlight`/highlight.js emit `hljs`-classed `<span>`s but ship no colors. Either import a highlight.js theme CSS (`import 'highlight.js/styles/github-dark.css'`) or define token colors yourself:

```css
.tiptap pre code .hljs-keyword { color: #c678dd; }
.tiptap pre code .hljs-string  { color: #98c379; }
.tiptap pre code .hljs-comment { color: #7f848e; font-style: italic; }
.tiptap pre code .hljs-function,
.tiptap pre code .hljs-title   { color: #61afef; }
/* …etc. — match your design system */
```

## Table CSS (tables look broken without it)

```css
.tiptap table { border-collapse: collapse; width: 100%; }
.tiptap th, .tiptap td { border: 1px solid var(--border); padding: 0.5rem 0.75rem; }
.tiptap th { background: var(--muted); font-weight: 600; text-align: left; }
.tiptap .selectedCell { background: color-mix(in srgb, var(--primary) 12%, transparent); }
.tiptap .column-resize-handle { background: var(--primary); width: 3px; }
```

## Styling the chrome (toolbar, menus, container)

The toolbar and bubble/floating menus are your own components — style them with the project's design system (shadcn/ui tokens like `bg-popover`, `border`, `text-muted-foreground`, `ring`). A common, clean container treatment:

```tsx
<div className="rounded-xl border bg-card shadow-sm">
  <Toolbar editor={editor} />        {/* sticky top toolbar */}
  <EditorContent editor={editor} className="px-4 py-3" />
  <EditorFooter editor={editor} />    {/* word count, save status */}
</div>
```

Make the toolbar `sticky top-0 z-10 bg-card/80 backdrop-blur` so it stays reachable in a long post.

## Glass / neon / frosted aesthetics

For a frosted-glass editor surface, layer translucency + blur on the chrome while keeping the *content* on a readable, high-contrast backdrop (glass behind body text hurts legibility — apply it to chrome, not the reading column):

```tsx
// Frosted toolbar / bubble menu
className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-md shadow-lg
           supports-[backdrop-filter]:bg-white/5"
```

```css
/* Neon focus accent on the container when the editor is focused */
.editor-shell:focus-within {
  border-color: color-mix(in srgb, var(--primary) 60%, transparent);
  box-shadow: 0 0 0 1px var(--primary), 0 0 24px -6px var(--primary);
}
/* Subtle neon active state for toolbar buttons (pairs with the active class) */
.toolbar-btn[aria-pressed="true"] {
  color: var(--primary);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--primary) 50%, transparent);
}
```

Keep contrast accessible: neon glows belong on borders, focus rings, and active states — not under paragraph text. Test the dark and light ramps, and respect `prefers-reduced-motion` for any animated glow or transitions.

## Dark mode

If you support theme switching, drive both content and chrome from the same tokens. With Tailwind Typography, `dark:prose-invert` handles content; for the chrome, use your design tokens (`bg-card`, `text-foreground`, etc.) which already flip with the theme. Verify code-block and table colors in *both* themes — hand-rolled token colors are the usual thing that looks wrong in one mode.
