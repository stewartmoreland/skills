# Extension Catalog for Blog Editors (TipTap v3)

TipTap is a small core plus extensions. Each extension adds nodes (block content like headings), marks (inline styling like bold), or functionality (placeholders, counters). For a blog editor, start from `StarterKit` and add only what authors need.

> **Import-path reminder (v3):** Several extensions moved packages in v3. The most-missed ones are listed inline below. When an import errors, verify the path against the installed package rather than guessing — v2 paths are widespread online and won't work.

## StarterKit — what you get for free

`StarterKit` is the batteries-included bundle and the right default base for a blog. In **v3** it includes the document/paragraph/text schema plus these editing features:

- **Marks:** `Bold`, `Italic`, `Strike`, `Code`, `Underline` *(new in v3)*, `Link` *(new in v3)*
- **Nodes:** `Heading`, `BulletList`, `OrderedList`, `ListItem`, `Blockquote`, `CodeBlock`, `HorizontalRule`, `HardBreak`
- **Functionality:** `UndoRedo` (history), `Dropcursor`, `Gapcursor`, list keymaps

Configure or disable any bundled extension through `StarterKit.configure({ ... })`. Pass `false` to drop one, or an options object to tune it:

```ts
StarterKit.configure({
  heading: { levels: [2, 3, 4] }, // blogs rarely need H1 in the body (the post title is the H1)
  link: false,                    // disable the bundled Link so you can add a custom-configured one
  codeBlock: false,               // disable plain code block to swap in the syntax-highlighted version
})
```

A useful blog convention: reserve `<h1>` for the post title (rendered outside the editor) and let authors use `H2`–`H4` inside the body. Limiting `heading.levels` enforces that.

## The blog essentials

### Links (custom configuration)

The bundled `Link` is fine for basics. Configure a custom one when you want controlled attributes (e.g. `rel`, target, allowed protocols). Disable the StarterKit link first.

```ts
import Link from '@tiptap/extension-link'

Link.configure({
  openOnClick: false,      // don't navigate while editing
  autolink: true,          // turn typed URLs into links
  defaultProtocol: 'https',
  HTMLAttributes: { rel: 'noopener noreferrer nofollow', target: '_blank' },
})
```

Pair this with a link-edit UI in the bubble menu (see `references/toolbar-and-ui.md`) so authors can set/clear the href on a selection.

### Images

```ts
import Image from '@tiptap/extension-image'

Image.configure({
  inline: false,            // block-level images read better in articles
  allowBase64: false,       // force upload-and-URL; keeps the document and DB lean
  HTMLAttributes: { class: 'rounded-lg' },
})
```

> ⚠️ Keep `allowBase64: false`. Pasting/dropping images as base64 embeds the raw bytes in the document JSON/HTML, which bloats storage, blows past column/size limits, and slows every save. Wire an upload handler that stores the file and inserts the returned URL — see the image-upload section in `references/content-and-persistence.md`.

For drag-and-drop / paste-to-upload, add `@tiptap/extension-file-handler` and route dropped files through your uploader.

### Code blocks with syntax highlighting

A plain `CodeBlock` (in StarterKit) gives you a styled `<pre>` but no token coloring. For a dev blog, use the lowlight variant. Disable the StarterKit `codeBlock` first to avoid two competing nodes.

```ts
import { CodeBlockLowlight } from '@tiptap/extension-code-block-lowlight'
import { createLowlight, common } from 'lowlight'

const lowlight = createLowlight(common) // bundles common languages

// in extensions:
CodeBlockLowlight.configure({ lowlight, defaultLanguage: 'plaintext' })
```

`lowlight` emits `hljs`-style class names on tokens; you still need a highlight.js CSS theme (or your own token CSS) for colors. See `references/styling.md`.

### Lists (including task lists)

In v3 all list pieces come from **`@tiptap/extension-list`**. `BulletList`/`OrderedList`/`ListItem` are already in StarterKit; add task lists for checklists:

```ts
import { TaskList, TaskItem } from '@tiptap/extension-list'

TaskList,
TaskItem.configure({ nested: true }),
```

### Tables

In v3 the four table pieces come from **one** package, `@tiptap/extension-table`:

```ts
import { Table, TableRow, TableHeader, TableCell } from '@tiptap/extension-table'

Table.configure({ resizable: true }),
TableRow,
TableHeader,
TableCell,
```

Tables need supporting CSS (borders, header background, the resize handle, a selected-cell highlight) or they look broken — covered in `references/styling.md`.

### Placeholder, character/word count (utility — from `@tiptap/extensions`)

These moved into the consolidated `@tiptap/extensions` package in v3.

```ts
import { Placeholder, CharacterCount } from '@tiptap/extensions'

Placeholder.configure({ placeholder: 'Tell your story…' }),
CharacterCount.configure({ limit: 50000 }), // optional hard cap
```

Placeholder is rendered purely via CSS (`.is-editor-empty::before { content: attr(data-placeholder) }`) — add that rule or nothing shows. Read counts live in editor storage: `editor.storage.characterCount.characters()` and `.words()` — handy for a "1,240 words · 6 min read" footer.

### Typography (smart punctuation)

```ts
import Typography from '@tiptap/extension-typography'
// Converts -- to em-dashes, ... to ellipses, straight to curly quotes, etc.
```

Low-effort, high-polish for prose. Recommended for any writing surface.

### Text alignment

```ts
import TextAlign from '@tiptap/extension-text-align'

TextAlign.configure({ types: ['heading', 'paragraph'] }),
```

### Highlight

```ts
import Highlight from '@tiptap/extension-highlight'

Highlight.configure({ multicolor: true }),
```

### Embeds (YouTube)

```ts
import Youtube from '@tiptap/extension-youtube'

Youtube.configure({ width: 640, height: 360, nocookie: true }),
```

Insert with `editor.commands.setYoutubeVideo({ src: url })`. For other providers (Twitter/X, CodePen, Vimeo) without an official extension, write a small custom node — see "Custom nodes" below.

## A representative blog extension set

A solid, opinionated starting set for a general-purpose blog editor:

```ts
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Image from '@tiptap/extension-image'
import { CodeBlockLowlight } from '@tiptap/extension-code-block-lowlight'
import { createLowlight, common } from 'lowlight'
import { TaskList, TaskItem } from '@tiptap/extension-list'
import { Placeholder, CharacterCount } from '@tiptap/extensions'
import Typography from '@tiptap/extension-typography'
import TextAlign from '@tiptap/extension-text-align'

const lowlight = createLowlight(common)

// Define OUTSIDE the component (or useMemo) so the array is stable across renders.
export const blogExtensions = [
  StarterKit.configure({
    heading: { levels: [2, 3, 4] },
    link: false,       // custom Link below
    codeBlock: false,  // CodeBlockLowlight below
  }),
  Link.configure({
    openOnClick: false,
    autolink: true,
    defaultProtocol: 'https',
    HTMLAttributes: { rel: 'noopener noreferrer nofollow', target: '_blank' },
  }),
  Image.configure({ allowBase64: false, HTMLAttributes: { class: 'rounded-lg' } }),
  CodeBlockLowlight.configure({ lowlight, defaultLanguage: 'plaintext' }),
  TaskList,
  TaskItem.configure({ nested: true }),
  Placeholder.configure({ placeholder: 'Tell your story…' }),
  CharacterCount,
  Typography,
  TextAlign.configure({ types: ['heading', 'paragraph'] }),
]
```

Trim this to what the specific blog needs. Every extension you add is more schema, more toolbar surface, and more to style.

## Custom nodes and marks (when no extension exists)

For blog-specific blocks the catalog doesn't cover — callout/admonition boxes, image-with-caption (`figure`/`figcaption`), pull quotes, embeds for unsupported providers — author a custom node. Two routes:

- **`Node.create({...})`** with `parseHTML`/`renderHTML` for static blocks (a callout, a figure). Define the schema, the HTML serialization, and an input rule or command to insert it.
- **React node views** (`ReactNodeViewRenderer` + `NodeViewWrapper` from `@tiptap/react`) when the block needs interactive React UI inside the editor (a live embed, an editable caption, a settings popover).

Keep `parseHTML` and `renderHTML` symmetric so content round-trips cleanly through save/load and through the static renderer used for publishing. If you build a custom node, verify it survives `getHTML()` → reload and `getJSON()` → render before shipping.
