---
name: drawpyo
description: Generate Draw.io / diagrams.net (.drawio) diagrams programmatically in Python with the drawpyo library. Use this whenever the user wants to build, script, or auto-generate .drawio files, diagrams.net charts, flowcharts, tree/hierarchy diagrams, org charts, bar/pie charts, legends, or network/architecture diagrams from Python or from structured data (dicts, JSON, CSV). Trigger this even when the user doesn't name drawpyo — e.g. "make a flowchart in Python and save it as .drawio", "turn this dict into a tree diagram I can open in draw.io", "script a diagrams.net file", "render an architecture diagram with AWS/Azure icons as a drawio file", or "programmatically create editable draw.io shapes and edges". Prefer this over hand-writing mxGraph XML or generating static images when the deliverable must open and stay editable in the Draw.io app.
---

# drawpyo

drawpyo builds **editable** Draw.io / diagrams.net files from Python. Unlike Mermaid or an exported PNG, the output `.drawio` is plaintext XML that opens in the Draw.io app where every shape and edge can still be moved and restyled by hand. That makes it ideal for documentation diagrams that live in a repo and need to stay human-editable.

This skill covers the verified API for drawpyo (PyPI `drawpyo`, tested against 0.2.5). Read the reference files listed below when a task goes beyond the core workflow — don't guess at shape names, edge style values, or color enums, because drawpyo validates many of them and raises `ValueError` on anything it doesn't recognize.

## Install

```bash
pip install drawpyo
```

Pure Python, no heavy dependencies (only `toml` on Python < 3.11). The output file opens at https://app.diagrams.net or in the Draw.io desktop app.

## The mental model

Four object layers, top to bottom: a **File** contains one or more **Pages**; each Page holds **Objects** (shapes) and **Edges** (connectors). You build the tree in Python, then call `file.write()` to emit the XML. Nothing renders unless it's attached to a page (see the template-object trick below — that's a deliberate use of "no page = not drawn").

```python
import drawpyo

file = drawpyo.File(file_name="diagram.drawio", file_path="/path/to/output")
page = drawpyo.Page(file=file)

a = drawpyo.diagram.Object(page=page, value="Start", position=(160, 40))
b = drawpyo.diagram.Object(page=page, value="End",   position=(160, 200))
drawpyo.diagram.Edge(page=page, source=a, target=b, label="next")

file.write()   # returns the full path written
```

If `file_path` is omitted it defaults to `~/Drawpyo Charts`. Always pass an explicit `file_path` so output lands where the user expects. `write()` accepts `file_path=`, `file_name=`, and `overwrite=` (default `True`) to emit variants.

## Quieting the logger

drawpyo logs an INFO line for every file, page, and object it creates, which floods stdout on large diagrams. Silence it at the top of any script:

```python
import logging, drawpyo
drawpyo.logger.setLevel(logging.WARNING)
```

## Choosing your approach

drawpyo has two distinct modes. Pick based on what the user is making:

1. **Manual placement** (`Object` + `Edge`) — full control over position and style. Use for flowcharts, architecture diagrams, network diagrams, wireframes, anything spatial. You set every `position`. → see `references/objects_and_edges.md`
2. **Automatic diagram types** — you supply data/relationships and drawpyo computes the layout. Use for hierarchies and charts:
   - `TreeDiagram` / `BinaryTreeDiagram` — org charts, taxonomies, decision/file trees (auto-laid-out). Can build straight from a nested dict.
   - `BarChart`, `PieChart`, `Legend` — data charts from a `{label: value}` dict.
   → see `references/diagram_types.md`

These can be mixed: build a chart or tree, then drop more manual objects on the same page.

## Core patterns you'll reach for constantly

**Shapes from the built-in libraries** (proper flowchart/diagram shapes, not bare rectangles):

```python
proc = drawpyo.diagram.object_from_library(
    page=page, library="flowchart", obj_name="process", value="Validate input")
```

Built-in libraries: `"general"` (rectangle, ellipse, diamond, cylinder, cloud, document, container, …), `"flowchart"` (process, decision, terminator, data, …), `"infographics"` (pie, arc). The full shape-name catalogs are in `references/objects_and_edges.md` — using a wrong `obj_name` raises `ValueError`, so consult the list.

**Template objects** — define a style once, stamp it many times. A template has no `page`, so it isn't drawn; only the stamped copies are:

```python
tmpl = drawpyo.diagram.object_from_library(library="flowchart", obj_name="process", width=140, height=70)
step1 = drawpyo.diagram.Object(template_object=tmpl, value="Step 1", page=page)
step1.center_position = (300, 80)
step2 = drawpyo.diagram.Object(template_object=tmpl, value="Step 2", page=page)
step2.center_position = (300, 200)
```

**Style strings copied from the Draw.io app** — right-click any shape in Draw.io → *Edit Style*, paste the string here to reproduce it exactly:

```python
obj = drawpyo.diagram.Object(page=page, value="Box")
obj.apply_style_string("rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;")
```

**Positioning**: `position` is the top-left corner `(x, y)`; `center_position` is the center. Both are `(x, y)` tuples in pixels, y increasing downward. Set `width`/`height` at creation or via the properties.

**Containers / grouping** — make one shape the visual parent of others and have it auto-resize:

```python
box = drawpyo.diagram.object_from_library(page=page, library="general", obj_name="container", value="Subsystem")
box.autosize_to_children = True
child = drawpyo.diagram.Object(page=page, value="inner", parent=box, position=(60, 80))
```

## Colors

Pass `fillColor` / `strokeColor` as `#RRGGBB` hex (exactly 6 digits), a `drawpyo.StandardColor` enum member, or bundle all three with a `ColorScheme`:

```python
cs = drawpyo.ColorScheme(fill_color="#DAE8FC", stroke_color="#6C8EBF", font_color="#FFFFFF")
drawpyo.diagram.Object(page=page, value="Node", color_scheme=cs)
```

`ColorScheme` rejects malformed hex with a `ValueError`. The full `StandardColor` palette and the special values `"none"` / `"default"` are documented in `references/colors_and_loading.md`.

## Text formatting

```python
tf = drawpyo.diagram.text_format.TextFormat(bold=True, fontSize=16, align="center", verticalAlign="middle")
drawpyo.diagram.Object(page=page, value="Title", text_format=tf)
```

## External icon libraries (AWS / Azure / GCP, etc.)

Register a Draw.io `.xml` shape library (local path or URL) once, then use it like a built-in:

```python
drawpyo.register_mxlibrary("azure", "https://example.com/azure-icons.xml")
vm = drawpyo.diagram.object_from_library(page=page, library="azure", obj_name="Virtual-Machine")
```

Details and how to discover shape names are in `references/colors_and_loading.md`.

## Loading and modifying existing diagrams

```python
parsed = drawpyo.load_diagram("existing.drawio")   # → ParsedDiagram(.shapes, .edges, .get_by_id(), .element_count)
```

Loading support is the least mature part of the library and is version-sensitive — read the "Loading" section of `references/colors_and_loading.md` before relying on it (there's a known loader crash on certain edge styles in some releases, and a version-safe re-attach pattern).

## Reference files

Load these as needed — they contain verified API signatures, complete enumerated value lists, and full worked examples:

- `references/objects_and_edges.md` — `Object`, `Edge`, `TextFormat`, `Group`, `List`; every shape-library name; all valid edge `waypoints`/`connection`/`pattern`/line-end values; connection points (entry/exit) and waypoints.
- `references/diagram_types.md` — `TreeDiagram` + `NodeObject`, `BinaryTreeDiagram`, `from_dict` rules and coloring modes, `BarChart`, `PieChart`, `Legend`.
- `references/colors_and_loading.md` — `ColorScheme`, full `StandardColor` palette, `PageSize` presets, external mxlibraries, loading/parsing, and version gotchas.

## Verify your output

After writing a file, confirm it's well-formed before handing it back. A quick sanity check that it's valid XML and has the expected page/object counts:

```python
import xml.dom.minidom; xml.dom.minidom.parse("diagram.drawio")  # raises if malformed
```

When producing a deliverable for the user, write the `.drawio` to a path they can access and tell them it opens in the Draw.io app or at app.diagrams.net.
