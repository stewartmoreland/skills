---
name: tiptap-blog-editor
description: Build production-grade rich blog/article content editors with the TipTap editor (v3, built on ProseMirror). Use this whenever the user wants a WYSIWYG/rich-text editor, a blog or article composer, a CMS post editor, a "Notion-like" or "Medium-like" writing surface, a comment/markdown editor, or asks to add formatting toolbars, bubble menus, slash commands, image embedding, or persisted rich content to an app. Trigger this even when the user says only "rich text editor", "content editor", "WYSIWYG", "post editor", or names TipTap/ProseMirror, and even if they don't say the word "blog". Covers React/Next.js setup, SSR-safe initialization, the v3 extension catalog and its reorganized package imports, building toolbars/bubble menus with reactive active states, HTML/JSON/Markdown output, autosave/persistence, read-only publishing, styling with Tailwind typography, and image upload handling.
---

# TipTap Blog Editor

Build a rich content editor for blogs, articles, and CMS posts using **TipTap v3** — a headless, framework-agnostic rich text editor built on ProseMirror. "Headless" means TipTap ships behavior, schema, and commands but **no UI**: you own every pixel of the toolbar, menus, and content styling. That's the whole appeal — and the reason a good editor is mostly UI work layered on a small, well-behaved core.

This skill targets **React / Next.js** by default because that's where most blog editors live, but the editor core and extensions are identical across Vue and vanilla JS — only the binding layer (`@tiptap/react` vs `@tiptap/vue-3` vs `@tiptap/core`) changes. If the user is on a different framework, keep the architecture and swap the binding.

## Why version matters here (read this first)

TipTap v3 reorganized which package many extensions live in. Code written for v2 — including a lot of what's floating around in blog posts and model training data — **imports from packages that no longer export those names in v3**, and will fail at build time. Three rules prevent almost every version-related failure:

1. **Pin one version and keep every `@tiptap/*` package on the exact same version.** Mixing (e.g. `@tiptap/react@3.x` with `@tiptap/extension-link@2.x`) causes subtle schema and type breakage. After install, run `npm ls @tiptap/core` and confirm a single deduped version.
2. **`@tiptap/pm` is a required peer dependency.** It provides the ProseMirror primitives. Install it explicitly even though nothing imports it directly.
3. **When in doubt about an import path, verify against the installed package**, not memory. v3 consolidated several extensions (see below). If an import errors, check the package's `package.json` `exports` or the docs rather than guessing.

### v3 package consolidations you must know

These are the imports people most often get wrong. Memorize them:

- **Utility extensions** → `@tiptap/extensions` (a single package): `Placeholder`, `CharacterCount`, `Focus`, `Dropcursor`, `Gapcursor`, `TrailingNode`, `Selection`, `UndoRedo` (history). Example: `import { Placeholder, CharacterCount } from '@tiptap/extensions'`.
- **Lists** → `@tiptap/extension-list`: `BulletList`, `OrderedList`, `ListItem`, `ListKeymap`, `TaskList`, `TaskItem` all come from this one package now.
- **Tables** → `@tiptap/extension-table`: `Table`, `TableRow`, `TableCell`, `TableHeader` all from this one package.
- **Bubble & floating menus (React)** → `@tiptap/react/menus`, NOT `@tiptap/react`. This moved in v3 and is a top failure point: `import { BubbleMenu, FloatingMenu } from '@tiptap/react/menus'`.
- **StarterKit now bundles `Underline` and `Link`** out of the box. Don't add them separately. To use a *custom* configuration of a bundled extension, disable the default first: `StarterKit.configure({ link: false })` then add your own `Link`.

## Workflow

Work through these phases in order. Each builds on the last. Don't dump a 600-line editor on the user in one shot — scaffold the core, confirm it renders, then layer features.

1. **Confirm the deliverable.** Framework (default React/Next.js), and what "rich" means for *this* blog: which formatting do authors actually need? A dev blog needs code blocks with syntax highlighting; a recipe blog needs images and ordered lists; a news site needs blockquotes, links, and embeds. Don't install extensions nobody will use — each is schema surface and toolbar clutter.
2. **Install** with version pinning + `@tiptap/pm`. See "Install" below.
3. **Scaffold an SSR-safe core editor** that renders and is editable. See "Minimal working editor" below. Get this rendering before adding anything.
4. **Select and configure extensions** for the blog's needs. → `references/extensions.md`
5. **Build the toolbar and/or bubble menu** with reactive active states (this is the bulk of the work and where most editors go wrong on performance). → `references/toolbar-and-ui.md`
6. **Wire content I/O and persistence**: get content out (HTML/JSON/Markdown), save it (debounced autosave), load it back. → `references/content-and-persistence.md`
7. **Render published content** read-only / on the server, without shipping the whole editor. → `references/content-and-persistence.md`
8. **Style the content and chrome** with Tailwind typography (`prose`) and the project's design system. → `references/styling.md`
9. **Handle images** via upload-and-store-URL, never base64-in-the-document. → `references/content-and-persistence.md`

When the user asks for one specific piece ("just help me add a bubble menu"), jump straight to the relevant reference — you don't have to march through every phase.

## Install

```bash
# Core React binding + ProseMirror primitives (peer) + the batteries-included kit
npm install @tiptap/react @tiptap/pm @tiptap/starter-kit
```

Add only the extra packages the blog actually needs, e.g.:

```bash
# Common blog additions (install the ones you'll use)
npm install @tiptap/extension-image @tiptap/extension-link \
            @tiptap/extension-table @tiptap/extension-list \
            @tiptap/extensions @tiptap/extension-code-block-lowlight lowlight \
            @tiptap/extension-typography @tiptap/extension-text-align
```

> ⚠️ **Build tooling:** TipTap v3 does not support Create React App. Use **Vite** or **Next.js**. If the user is on CRA, the right move is to migrate the build tool, not to fight TipTap.

## Minimal working editor (SSR-safe)

This is the smallest thing that renders and edits. Build this first, confirm it works in the browser, then layer features from the references. The `'use client'` directive and `immediatelyRender: false` are **not optional** in Next.js / any SSR framework.

```tsx
'use client'

import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'

export function BlogEditor() {
  const editor = useEditor({
    extensions: [StarterKit],
    content: '<p>Start writing…</p>',
    // Required for SSR (Next.js, Remix). Prevents the editor from rendering on
    // the server, which would cause a React hydration mismatch. The editor
    // initializes on the client after hydration.
    immediatelyRender: false,
    editorProps: {
      attributes: {
        // `prose` (Tailwind Typography) gives sensible default article styling.
        class: 'prose prose-neutral dark:prose-invert max-w-none focus:outline-none min-h-[300px]',
      },
    },
  })

  if (!editor) return null

  return <EditorContent editor={editor} />
}
```

### Why `immediatelyRender: false` is critical

Next.js renders components on the server by default. TipTap's default (`immediatelyRender: true`) tries to build the editor DOM during that server pass, but ProseMirror needs a real browser DOM. The result is the classic `"SSR has been detected, please set immediatelyRender explicitly to false"` warning followed by hydration mismatches. Setting it `false` defers editor creation to the client. The `if (!editor) return null` guard handles the brief window before the client editor exists.

## Critical gotchas (the ones that actually bite)

These recur across almost every TipTap blog editor. Internalize them; they're cheaper to prevent than to debug.

- **Toolbar buttons that don't light up / re-render storms.** The editor's `isActive()` only reflects current state if the component re-renders on selection change. The performant v3 answer is `useEditorState` with a selector — not forcing re-renders on every transaction. See `references/toolbar-and-ui.md`; this is the single most common quality problem.
- **Memoize the extensions array / editor config.** Defining `extensions: [...]` inline in a component that re-renders for other reasons can thrash the editor. Define extensions outside the component or `useMemo` them.
- **Images stored as base64 bloat the document** and the database, and break on copy/paste limits. Upload the file, store the returned URL in the document. See `references/content-and-persistence.md`.
- **No styling at all? You forgot `prose`.** Headless means no default content styles. Author content (`h2`, `blockquote`, `ul`) renders unstyled until you add Tailwind Typography's `prose` classes or your own CSS. See `references/styling.md`.
- **Sanitize HTML on output if it will be rendered as raw HTML elsewhere.** TipTap's schema constrains what's *in* the editor, but if you render stored HTML with `dangerouslySetInnerHTML`, sanitize it (e.g. with `isomorphic-dompurify`) to be safe against content from other sources.
- **Don't reach for Pro/Cloud features unless asked.** Collaboration, Comments, AI Toolkit, and DOCX conversion are real but are paid/Cloud or heavier add-ons. A blog editor rarely needs them. Mention them as options, don't bake them in by default.

## Reference files

Load the one relevant to the current phase rather than reading everything up front:

- **`references/extensions.md`** — The blog-relevant v3 extension catalog with correct import paths and configuration: headings, lists, links, images, code blocks with syntax highlighting, blockquotes, tables, embeds (YouTube), placeholder, character count, typography, text alignment, highlight. Read when selecting/configuring features (phase 4).
- **`references/toolbar-and-ui.md`** — Building the toolbar and bubble/floating menus, reactive active states with `useEditorState`, command patterns, a shadcn/Radix-friendly button component, and slash-command/floating-menu patterns. Read for phase 5 (the biggest phase).
- **`references/content-and-persistence.md`** — Getting content out (HTML vs JSON vs Markdown — when to use which), debounced autosave, loading saved content, read-only and server-side rendering of published posts, and the image-upload pattern. Read for phases 6, 7, 9.
- **`references/styling.md`** — Tailwind Typography (`prose`) setup, dark mode, styling custom nodes, placeholder CSS, and applying a design system (including glass/neon aesthetics) to both content and editor chrome. Read for phase 8.
