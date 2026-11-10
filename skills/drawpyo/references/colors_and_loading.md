# Colors, Page Sizes, External Libraries & Loading

Verified against drawpyo 0.2.5.

## Contents
- [Color inputs](#color-inputs)
- [ColorScheme](#colorscheme)
- [StandardColor palette](#standardcolor-palette)
- [Page sizes](#page-sizes)
- [Multi-page files](#multi-page-files)
- [External shape libraries (AWS/Azure/GCP)](#external-shape-libraries-awsazuregcp)
- [Loading existing .drawio files](#loading-existing-drawio-files)
- [Version gotchas](#version-gotchas)

---

## Color inputs

Anywhere a color is accepted (`fillColor`, `strokeColor`, `fontColor`, chart colors), three forms are valid:
1. A hex string `"#RRGGBB"` — **exactly** 6 hex digits with a leading `#`. `"#fff"` shorthand is rejected.
2. A `drawpyo.StandardColor` enum member (see palette below).
3. The special strings `"none"` (no fill/stroke) or `"default"` (Draw.io theme default).

`None` means "unset" (Draw.io decides). Invalid hex raises `ValueError` when going through `ColorScheme`; raw `Object` color setters silently drop malformed values to `None`, so prefer `ColorScheme` or validated hex.

## ColorScheme

Bundle fill + stroke + font so a whole object (or chart slice / node) is themed at once.

```python
cs = drawpyo.ColorScheme(
    fill_color="#DAE8FC",
    stroke_color="#6C8EBF",
    font_color=drawpyo.StandardColor.BLUE9,   # mix hex and enum freely
)
drawpyo.diagram.Object(page=page, value="Node", color_scheme=cs)
```

Methods: `set_fill_color`, `set_stroke_color`, `set_font_color`. `ColorScheme.is_valid_hex(s)` is a handy static validator. When an object gets a `color_scheme` and no explicit `fontColor`, the scheme's font color flows into its `TextFormat`.

These three Draw.io "blue/green/orange/red/purple/gray" themes are common defaults:
- Blue:   fill `#DAE8FC`, stroke `#6C8EBF`
- Green:  fill `#D5E8D4`, stroke `#82B366`
- Orange: fill `#FFE6CC`, stroke `#D79B00`
- Red:    fill `#F8CECC`, stroke `#B85450`
- Purple: fill `#E1D5E7`, stroke `#9673A6`
- Yellow: fill `#FFF2CC`, stroke `#D6B656`
- Gray:   fill `#F5F5F5`, stroke `#666666`

## StandardColor palette

`drawpyo.StandardColor` (also `drawpyo.utils.StandardColor`) is a string enum of 118 named colors. Each family runs light→dark as `NAME1`…`NAME9`. Access with `StandardColor.BLUE5`, and `.value` gives the hex.

```
NONE      = none
BLACK     = #000000      WHITE = #FFFFFF
GRAY1-9   = #E6E6E6 #CCCCCC #B3B3B3 #999999 #808080 #666666 #4D4D4D #333333 #1A1A1A
RED1-9    = #FFCCCC #FF9999 #FF6666 #FF3333 #FF0000 #CC0000 #990000 #660000 #330000
ORANGE1-9 = #FFE6CC #FFCC99 #FFB366 #FF9933 #FF8000 #CC6600 #994C00 #663300 #331A00
YELLOW1-9 = #FFFFCC #FFFF99 #FFFF66 #FFFF33 #FFFF00 #CCCC00 #999900 #666600 #333300
LIME1-9   = #E6FFCC #CCFF99 #B3FF66 #99FF33 #80FF00 #66CC00 #4D9900 #336600 #1A3300
GREEN1-9  = #CCFFCC #99FF99 #66FF66 #33FF33 #00FF00 #00CC00 #009900 #006600 #003300
EMERALD1-9= #CCFFE6 #99FFCC #66FFB3 #33FF99 #00FF80 #00CC66 #00994D #006633 #00331A
CYAN1-9   = #CCFFFF #99FFFF #66FFFF #33FFFF #00FFFF #00CCCC #009999 #006666 #003333
BLUE1-9   = #CCE5FF #99CCFF #66B2FF #3399FF #007FFF #0066CC #004C99 #003366 #001933
INDIGO1-9 = #CCCCFF #9999FF #6666FF #3333FF #0000FF #0000CC #000099 #000066 #000033
PURPLE1-8 = #E5CCFF #CC99FF #B266FF #9933FF #7F00FF #6600CC #330066 #190033
MAGENTA1-9= #FFCCFF #FF99CC #FF66CC #FF33FF #FF00FF #CC00CC #990099 #660066 #330033
CRIMSON1-8= #FFCCE6 #FF66B3 #FF3399 #FF0080 #CC0066 #99004D #660033 #33001A
```
(PURPLE and CRIMSON have 8 members, not 9.)

## Page sizes

`drawpyo.PageSize` is an enum of `(width, height)` presets. Pass via `size_preset=` on a Page — it overrides `width`/`height`.

```python
page = drawpyo.Page(file=file, size_preset=drawpyo.PageSize.A4LANDSCAPE)
```

Available presets: `USLETTERPORTRAIT`/`USLETTERLANDSCAPE`, `USLEGAL…`, `USTABLOID…`, `USEXECUTIVE…`; `A0`–`A7` each in `…PORTRAIT`/`…LANDSCAPE`; `B4`/`B5` portrait/landscape; and aspect presets `ASPECT16BY9` (1600×900), `ASPECT16BY10` (1920×1200), `ASPECT4BY3` (1600×1200). Each member also exposes `.width` and `.height`.

Other Page kwargs: `name`, `grid` (0/1), `grid_size`, `guides`, `tooltips`, `scale`, `math`, `shadow`.

## Multi-page files

One `File` can hold several pages — they appear as tabs in the Draw.io app.

```python
file = drawpyo.File(file_name="book.drawio", file_path="/path/out")
overview = drawpyo.Page(file=file, name="Overview")
detail   = drawpyo.Page(file=file, name="Detail")
# add objects to each page independently...
file.write()
```

`file.remove_page(page_or_name_or_index)`, `page.remove()`, and `file.stats()` (returns a "Pages: N | Objects: M" summary) are available.

## External shape libraries (AWS/Azure/GCP)

Draw.io ships icon sets as `.xml` mxlibrary files. Register one (from a local path or URL) under a name, then use it exactly like a built-in library.

```python
drawpyo.register_mxlibrary("aws", "/path/to/aws17.xml")          # or an https URL
ec2 = drawpyo.diagram.object_from_library(page=page, library="aws", obj_name="EC2")
```

- `register_mxlibrary(name, source)` raises/logs if the file can't be loaded or has no valid shapes.
- `drawpyo.load_mxlibrary(source)` returns the raw shape dict if you want to inspect available `obj_name`s before placing — e.g. `print(list(load_mxlibrary(src).keys())[:20])`. Shape names come from each entry's title in the library file.
- Shapes lacking a `baseStyle` log a warning and may render unstyled; that's a property of the source library, not a bug.

Where to get library XML: the Draw.io desktop app and the `jgraph/drawio` repo ship the standard icon sets; you can also export any custom library from the app (Edit → … → Export).

## Loading existing .drawio files

```python
parsed = drawpyo.load_diagram("existing.drawio")
parsed.shapes          # list of Object
parsed.edges           # list of Edge
parsed.element_count   # len(shapes) + len(edges)
parsed.get_by_id("abc123")   # element by its Draw.io cell id, or None
```

To bring a loaded diagram onto a fresh page (version-safe, works everywhere), attach each element by setting its `.page`:

```python
out = drawpyo.File(file_name="copy.drawio", file_path="/path/out")
pg = drawpyo.Page(file=out)
for s in parsed.shapes:
    s.page = pg
for e in parsed.edges:
    e.page = pg
out.write()
```

Some builds (notably GitHub `main`) add `parsed.add_to(page, offset=(dx, dy))` to do this in one call **and** shift positions, but it is **not present in PyPI 0.2.5** — prefer the manual loop above unless you've confirmed `add_to` exists (`hasattr(parsed, "add_to")`).

## Version gotchas

drawpyo's GitHub `main` and the PyPI release have drifted; loading/parsing is the least mature area. Concretely, on PyPI 0.2.5:

- **`load_diagram` can crash on edges that carry an `endFill` style attribute** (`AttributeError: property 'endFill' of 'Edge' object has no setter`). If you must round-trip files containing filled arrowheads, wrap the load in `try/except`, or pre-process by stripping `endFill=` tokens from edge styles, or pin a version where it's fixed. Diagrams without filled arrowheads load fine.
- `ParsedDiagram.add_to` / `add_to_page` exist on GitHub but not on 0.2.5 (see above).

When precise behavior matters, check the installed version (`drawpyo.__version__`) and gate features with `hasattr` rather than assuming parity with the GitHub source. For authoring (the common case — creating new diagrams), the API is stable and fully covered by this skill.
