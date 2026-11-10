# Content I/O, Persistence & Publishing (TipTap v3)

A blog editor is only useful if content gets out, gets saved, comes back intact, and renders for readers. This file covers the output formats and when to use each, autosave, loading, read-only/server rendering of published posts, and image uploads.

## Output formats: HTML vs JSON vs Markdown

TipTap can serialize the document three ways. Choose based on how you'll *store* and *render*, not by habit.

- **JSON** (`editor.getJSON()`) — the ProseMirror document tree. **The best default for storage.** It's lossless, unambiguous, and round-trips perfectly back into the editor (`setContent(json)`). Custom nodes/marks survive cleanly. The downside: to render it for readers you either load it back into a (read-only) editor or run it through the static renderer (below). Store JSON when the canonical home of the content is your editor.
- **HTML** (`editor.getHTML()`) — a serialized HTML string. Convenient because you can render it directly with `dangerouslySetInnerHTML` (after sanitizing). Good when content must interoperate with systems that expect HTML, or when you want dead-simple read rendering. Slightly lossy for exotic custom nodes if `parseHTML`/`renderHTML` aren't perfectly symmetric.
- **Markdown** (`@tiptap/markdown`) — v3 ships official Markdown support. Use it when authors or downstream systems want Markdown (e.g. an MDX pipeline, a docs repo, or git-stored posts). Note that rich features without Markdown equivalents (colored highlights, complex tables, custom embeds) degrade or drop — Markdown is a lossy target for a feature-rich editor.

**Recommendation for most blogs:** store **JSON** as the source of truth (so editing always round-trips), and either (a) render published posts by running that JSON through the **static renderer** server-side, or (b) additionally persist a rendered **HTML** snapshot at publish time for the fastest possible reader render. If the project is committed to an MDX/Markdown content pipeline, store Markdown instead and accept the feature ceiling.

## Reading content out + onUpdate (debounced autosave)

The `onUpdate` callback fires on every change. Don't save to the network on every keystroke — debounce it.

```tsx
'use client'

import { useEditor, EditorContent } from '@tiptap/react'
import { useCallback, useMemo, useRef } from 'react'
import debounce from 'lodash/debounce'

export function BlogEditor({ postId, initialContent }: { postId: string; initialContent?: object }) {
  const save = useCallback(
    async (json: object) => {
      await fetch(`/api/posts/${postId}`, {
        method: 'PATCH',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ content: json }),
      })
    },
    [postId],
  )

  // Debounce so we save ~1s after the author pauses, not on every keystroke.
  const debouncedSave = useMemo(() => debounce(save, 1000), [save])

  const editor = useEditor({
    extensions: blogExtensions, // stable reference — defined outside the component
    content: initialContent ?? '<p></p>',
    immediatelyRender: false,
    onUpdate: ({ editor }) => {
      debouncedSave(editor.getJSON())
    },
  })

  if (!editor) return null
  return <EditorContent editor={editor} />
}
```

Notes:
- **Save JSON, not the editor instance.** Serialize inside `onUpdate`.
- **Flush on unmount / route change** so a quick edit-then-leave doesn't lose the last change: `useEffect(() => () => debouncedSave.flush(), [debouncedSave])`.
- For real "never lose work" autosave, layer optimistic local persistence (e.g. write to local state / IndexedDB immediately) and reconcile with the server save. Don't use browser `localStorage` inside Claude.ai *artifacts* (unsupported there) — but it's fine in a real app the user deploys.
- Surface save status ("Saving… / Saved") from the debounced promise so authors trust it.

## Loading saved content

Pass stored content to `useEditor`'s `content` option (it accepts an HTML string or a ProseMirror JSON object). To swap content into an existing editor (e.g. switching posts), use `editor.commands.setContent(json)`. If you load content asynchronously after the editor mounts, set it once it arrives and guard against clobbering in-progress edits.

When `useEditor` depends on async-loaded content, pass a dependency array so the editor re-initializes when it changes — but prefer `setContent` for live swaps to preserve the instance.

## Publishing: render content for readers (read-only / server-side)

You usually do **not** want to ship the full editable editor to every reader — it's heavier than needed and editable by default. Options, lightest first:

### 1. Static renderer (best for server components / SSG)

`@tiptap/static-renderer` turns a JSON document into HTML (or React elements) **without instantiating an editor or ProseMirror** — ideal for Next.js Server Components, SSG, RSS, or email. You provide the same extensions so custom nodes render correctly.

```ts
// Server component / build-time render of stored JSON → HTML string
import { renderToHTMLString } from '@tiptap/static-renderer'
import { blogExtensions } from '@/lib/blog-extensions'

const html = renderToHTMLString({ extensions: blogExtensions, content: storedJson })
```

There's also a React-element renderer variant when you want real React nodes (e.g. to map images to `next/image`). Prefer this path for published pages — it's the lightest and most SSR-friendly.

### 2. Render stored HTML directly

If you persisted HTML at publish time, render it directly — **sanitize first**:

```tsx
import DOMPurify from 'isomorphic-dompurify'

<article
  className="prose prose-neutral dark:prose-invert max-w-none"
  dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(post.html) }}
/>
```

Always wrap reader content in the same `prose` (or custom) classes you styled the editor with, so published posts match the editing preview.

### 3. Read-only editor instance

Set `editable: false` (or `editor.setEditable(false)`) to reuse the exact editor rendering with zero divergence — handy for previews or comment threads, but heavier than the static renderer for high-traffic public pages.

```ts
const editor = useEditor({ extensions: blogExtensions, content: storedJson, editable: false, immediatelyRender: false })
```

**Match extensions across edit and render.** Whichever render path you choose, use the *same* extension set you authored with — custom nodes/marks need their schema present to deserialize and render correctly. A shared `blogExtensions` module imported by both the editor and the renderer prevents drift.

## Image uploads (never base64)

Store images by uploading the file and inserting the returned **URL** into the document — keep `Image.configure({ allowBase64: false })`. The pattern:

```tsx
async function uploadImage(file: File): Promise<string> {
  const body = new FormData()
  body.append('file', file)
  const res = await fetch('/api/upload', { method: 'POST', body })
  const { url } = await res.json()       // your endpoint stores to S3/R2/UploadThing/etc. and returns a URL
  return url
}

// Toolbar/floating-menu action:
async function addImage(editor: Editor, file: File) {
  const url = await uploadImage(file)    // show a loading placeholder while this runs
  editor.chain().focus().setImage({ src: url, alt: file.name }).run()
}
```

For **paste and drag-and-drop** uploads, add `@tiptap/extension-file-handler` and route `onDrop`/`onPaste` files through the same `uploadImage`. Insert a temporary placeholder node (or a loading decoration) while the upload is in flight, then replace its `src` with the final URL on success so the author sees immediate feedback. Always set `alt` text — it's an accessibility and SEO win that blogs care about.

## Round-trip check before shipping

Whatever you store, verify the loop end-to-end: type rich content (heading, list, image, code block, link, any custom node) → save → reload the page → confirm it comes back identical in the editor → confirm the published/read-only render matches. Most "lost formatting" bugs are an extension present at edit time but missing at render time, or an asymmetric custom-node `parseHTML`/`renderHTML`.
