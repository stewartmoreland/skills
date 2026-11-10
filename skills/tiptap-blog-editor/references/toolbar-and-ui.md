# Toolbar & Menu UI (TipTap v3, React)

Because TipTap is headless, the toolbar, bubble menu, and any slash command UI are yours to build. This is the bulk of the work in a blog editor and where most implementations go wrong — usually on **reactive active states** (buttons that don't reflect the cursor's current formatting) or on **performance** (re-rendering the whole editor on every keystroke). Get the active-state pattern right and the rest is ordinary React.

## The core mental model

Two things flow between your UI and the editor:

1. **Commands** — what a button *does*. Run via the chained command API: `editor.chain().focus().toggleBold().run()`. Always `.focus()` first so the editor keeps the selection after a click; always `.run()` to execute.
2. **State** — what a button *shows* (active? disabled?). Read via `editor.isActive('bold')` and `editor.can().toggleBold()`. The catch: these are only meaningful if your component re-renders when the editor's selection/state changes.

## Reactive active states: use `useEditorState` (the right way in v3)

The naive approach is to force the editor to re-render on every transaction (`shouldRerenderOnTransaction: true`). That works but re-renders your entire toolbar (and anything else subscribed) on **every keystroke** — fine for a tiny demo, a performance problem in a real editor.

The v3 answer is **`useEditorState`** with a selector. It subscribes to editor changes but only re-renders the component when the *selected slice* actually changes — like a memoized selector in Redux/Zustand. This keeps toolbar highlights perfectly in sync without thrashing.

```tsx
'use client'

import { useEditor, useEditorState, EditorContent } from '@tiptap/react'

function Toolbar({ editor }: { editor: Editor }) {
  // Only re-renders when one of these derived values flips.
  const state = useEditorState({
    editor,
    selector: ({ editor }) => ({
      isBold: editor.isActive('bold'),
      isItalic: editor.isActive('italic'),
      isH2: editor.isActive('heading', { level: 2 }),
      isBulletList: editor.isActive('bulletList'),
      isLink: editor.isActive('link'),
      canBold: editor.can().chain().toggleBold().run(),
      canUndo: editor.can().undo(),
      canRedo: editor.can().redo(),
    }),
  })

  return (
    <div className="flex flex-wrap items-center gap-1 border-b p-2">
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleBold().run()}
        active={state.isBold}
        disabled={!state.canBold}
        label="Bold"
      >
        <BoldIcon className="h-4 w-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        active={state.isH2}
        label="Heading 2"
      >
        H2
      </ToolbarButton>
      {/* …more buttons, same pattern */}
    </div>
  )
}
```

Pass the `editor` from `useEditor` down to `Toolbar`. If you'd rather not prop-drill, wrap the tree in TipTap's `EditorContext` (provider exported from `@tiptap/react`) and read it with `useCurrentEditor()` — useful when the toolbar is far from the editor in the tree.

## A reusable toolbar button (shadcn/Radix-friendly)

A small presentational button keeps the toolbar declarative. This pairs with shadcn/ui `Button` + `Toggle` conventions; adapt classes to the project's design system.

```tsx
import { cn } from '@/lib/utils'

interface ToolbarButtonProps {
  onClick: () => void
  active?: boolean
  disabled?: boolean
  label: string
  children: React.ReactNode
}

export function ToolbarButton({ onClick, active, disabled, label, children }: ToolbarButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={active}
      title={label}
      // Prevent the button from stealing focus/selection from the editor.
      onMouseDown={(e) => e.preventDefault()}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'inline-flex h-8 min-w-8 items-center justify-center rounded-md px-2 text-sm',
        'transition-colors hover:bg-muted disabled:opacity-40 disabled:pointer-events-none',
        active && 'bg-muted text-foreground ring-1 ring-border',
      )}
    >
      {children}
    </button>
  )
}
```

> The `onMouseDown={e => e.preventDefault()}` is important: without it, clicking a toolbar button moves focus out of the editor and collapses the selection, so "bold the selected text" does nothing. Preventing the default mousedown keeps the selection alive while the `onClick` command runs.

## Heading / block-type dropdown

Authors expect a "Paragraph / Heading 2 / Heading 3 / Quote" selector. Drive its current value from `isActive` and its actions from `setNode`/`toggle` commands:

```tsx
const blockType = useEditorState({
  editor,
  selector: ({ editor }) => {
    if (editor.isActive('heading', { level: 2 })) return 'h2'
    if (editor.isActive('heading', { level: 3 })) return 'h3'
    if (editor.isActive('blockquote')) return 'quote'
    return 'paragraph'
  },
})

const setBlock = (value: string) => {
  const chain = editor.chain().focus()
  if (value === 'paragraph') chain.setParagraph().run()
  else if (value === 'h2') chain.toggleHeading({ level: 2 }).run()
  else if (value === 'h3') chain.toggleHeading({ level: 3 }).run()
  else if (value === 'quote') chain.toggleBlockquote().run()
}
```

## Bubble menu (format-on-selection)

A bubble menu floats over selected text — the Medium-style inline toolbar. **In v3 it's imported from `@tiptap/react/menus`, not `@tiptap/react`** (a frequent v2→v3 break).

```tsx
import { BubbleMenu } from '@tiptap/react/menus'

<BubbleMenu editor={editor} options={{ placement: 'top' }}>
  <div className="flex items-center gap-1 rounded-lg border bg-popover p-1 shadow-md">
    <ToolbarButton onClick={() => editor.chain().focus().toggleBold().run()} active={state.isBold} label="Bold">
      <BoldIcon className="h-4 w-4" />
    </ToolbarButton>
    <ToolbarButton onClick={() => editor.chain().focus().toggleItalic().run()} active={state.isItalic} label="Italic">
      <ItalicIcon className="h-4 w-4" />
    </ToolbarButton>
    <ToolbarButton onClick={() => setLink()} active={state.isLink} label="Link">
      <LinkIcon className="h-4 w-4" />
    </ToolbarButton>
  </div>
</BubbleMenu>
```

Use `shouldShow` in `options` to control when it appears (e.g. hide it inside code blocks or when the selection is empty). A bubble menu is the natural home for a **link editor**: on click, read the current href with `editor.getAttributes('link').href`, prompt for a value, and apply:

```ts
function setLink() {
  const prev = editor.getAttributes('link').href
  const url = window.prompt('URL', prev)            // replace with a proper popover input in production
  if (url === null) return                          // cancelled
  if (url === '') return editor.chain().focus().extendMarkRange('link').unsetLink().run()
  editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
}
```

`extendMarkRange('link')` makes the command apply to the whole link even if only part is selected — without it you get half-linked text.

## Floating menu (insert-on-empty-line)

The floating menu appears on an empty line — a clean place for "insert image / heading / list / code block" without a slash command.

```tsx
import { FloatingMenu } from '@tiptap/react/menus'

<FloatingMenu editor={editor} options={{ placement: 'left' }}>
  <div className="flex items-center gap-1 rounded-lg border bg-popover p-1 shadow-md">
    <ToolbarButton onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} label="Heading">H2</ToolbarButton>
    <ToolbarButton onClick={() => editor.chain().focus().toggleBulletList().run()} label="Bullet list"><ListIcon className="h-4 w-4" /></ToolbarButton>
    <ToolbarButton onClick={() => addImage()} label="Image"><ImageIcon className="h-4 w-4" /></ToolbarButton>
  </div>
</FloatingMenu>
```

## Slash commands (`/` menu)

For a Notion-like insert menu, build on `@tiptap/suggestion` (the same primitive that powers mentions). The flow: register a `Suggestion` plugin keyed on `/`, render a filtered command list in a popup (a `tippy`/Floating UI element or a React portal), and run the chosen command on select. This is more involved than the menus above — reach for it when the user specifically wants a slash menu, and lean on the official `@tiptap/suggestion` docs for the plugin wiring. Keep each command's action a normal chained command (`editor.chain().focus().setImage(...).run()`), so the slash menu is just another trigger for the same commands your toolbar uses.

## Keyboard shortcuts

Most StarterKit marks/nodes already bind the expected shortcuts (⌘B, ⌘I, ⌘⇧7 for ordered list, etc.). Add custom ones via an extension's `addKeyboardShortcuts()` or a small standalone `Extension.create({ addKeyboardShortcuts() { … } })`. Document the shortcuts in a tooltip or help affordance — authors discover formatting through them.

## Word/read-time footer

A nice touch for a writing surface, using the CharacterCount storage:

```tsx
const counts = useEditorState({
  editor,
  selector: ({ editor }) => ({
    words: editor.storage.characterCount.words(),
    chars: editor.storage.characterCount.characters(),
  }),
})
// e.g. `${counts.words} words · ${Math.max(1, Math.ceil(counts.words / 200))} min read`
```
