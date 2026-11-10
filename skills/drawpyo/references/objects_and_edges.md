# Objects, Edges, Text & Style Catalogs

Verified against drawpyo 0.2.5. This file is the authoritative reference for manual placement. The shape-name and edge-style lists are exhaustive — drawpyo validates these and raises `ValueError` on unknown values, so copy names from here rather than guessing.

## Contents
- [Object](#object)
- [Positioning & geometry](#positioning--geometry)
- [object_from_library and the shape catalogs](#object_from_library-and-the-shape-catalogs)
- [Template objects & style strings](#template-objects--style-strings)
- [Containers & parent/child](#containers--parentchild)
- [Group](#group)
- [List (extended object)](#list-extended-object)
- [Edge](#edge)
- [Edge style values (complete)](#edge-style-values-complete)
- [Connection points & waypoints](#connection-points--waypoints)
- [TextFormat](#textformat)

---

## Object

`drawpyo.diagram.Object(value="", position=(0, 0), **kwargs)`

The base shape. Common kwargs (all optional):

| kwarg | meaning | default |
| --- | --- | --- |
| `page` | Page to attach to. **Omit to make an unrendered template.** | None |
| `value` | Text label (positional or kwarg) | "" |
| `position` | Top-left `(x, y)` in px | (0, 0) |
| `width`, `height` | size in px | 120, 80 |
| `fillColor`, `strokeColor` | `#RRGGBB`, `StandardColor`, `"none"`, `"default"` | None |
| `color_scheme` | `ColorScheme` setting fill+stroke+font at once | None |
| `text_format` | `TextFormat` object | `TextFormat()` |
| `rounded` | round corners (0/1 or bool) | 0 |
| `opacity` | 0–100 | None |
| `glass`, `shadow`, `sketch`, `comic` | style effects (bool) | None |
| `line_pattern` | stroke dash style (see line patterns below) | "solid" |
| `baseStyle` | raw Draw.io base style token | None |
| `parent` | parent `Object` (container) | None |
| `template_object` | another `Object` to copy style from | — |

`value` accepts simple HTML when the text format's `formattedText` is on (e.g. `<b>`, `<br>`).

`line_pattern` valid values: `solid`, `small_dash`, `medium_dash`, `large_dash`, `small_dot`, `medium_dot`, `large_dot`. (Setting `dashed`/`dashPattern` directly is also possible but `line_pattern` is the ergonomic path.)

### Useful classmethods
- `Object.create_from_template_object(template_object, value=None, position=None, page=None)`
- `Object.create_from_library(library, obj_name)`
- `obj.apply_style_string(style_str)` — apply a Draw.io *Edit Style* string to an existing object.
- `obj.apply_attribute_dict({...})` — set arbitrary style attributes; unknown keys become style attributes automatically.

## Positioning & geometry

- `obj.position` → `(x, y)` top-left. Settable.
- `obj.center_position` → `(x, y)` center. Settable; convenient for aligning columns/rows.
- `obj.width`, `obj.height`, `obj.size` (`(w, h)` tuple).
- `obj.geometry` is the underlying `Geometry`; you rarely touch it directly.
- y increases downward. A Page defaults to 850×1100 px (`page.width`, `page.height`) — handy for centering: `main_col = page.width / 2`.

## object_from_library and the shape catalogs

`drawpyo.diagram.object_from_library(library, obj_name, **kwargs)` — produces an `Object` pre-styled as a named shape. Any `Object` kwarg (e.g. `value`, `page`, `width`, `fillColor`) also works and overrides the library defaults.

```python
d = drawpyo.diagram.object_from_library(
    page=page, library="flowchart", obj_name="decision", value="Valid?")
```

### library = "general" (32 names)
`rectangle`, `rounded_rectangle`, `text`, `ellipse`, `square`, `circle`, `process`, `diamond`, `parallelogram`, `hexagon`, `triangle`, `cylinder`, `cloud`, `document`, `internal_storage`, `cube`, `step`, `trapezoid`, `tape`, `note`, `card`, `callout`, `actor`, `or`, `and`, `data_storage`, `container`, `labeled_container`, `labeled_horizontal_container`, `list`, `list_item` (plus `default`).

### library = "flowchart" (37 names)
`annotation_1`, `annotation_2`, `card`, `collate`, `data`, `database`, `decision`, `delay`, `direct_data`, `display`, `document`, `extract`, `measurement`, `internal_storage`, `loop_limit`, `manual_input`, `manual_operation`, `merge`, `storage`, `multi_document`, `off_page_ref`, `on_page_ref`, `or`, `tape`, `parallel_mode`, `predefined_process`, `preparation`, `process`, `sequential_data`, `sort`, `start_1`, `start_2`, `stored_data`, `summing_junction`, `terminator`, `transfer`.

### library = "infographics"
`pie`, `arc`. (Usually accessed indirectly via `PieChart`.)

A `dict` shape database can also be passed as `library` instead of a string name (e.g. one you imported yourself).

## Template objects & style strings

The single most useful manual-mode pattern: build a styled-but-unplaced object (no `page`), then stamp copies onto the page. Because it has no page, the template itself never renders.

```python
process = drawpyo.diagram.object_from_library(library="flowchart", obj_name="process", width=140, height=70)
data    = drawpyo.diagram.object_from_library(library="flowchart", obj_name="data",    width=140, height=70)

weigh = drawpyo.diagram.Object(template_object=process, value="Weigh beans", page=page)
weigh.center_position = (main_col, 200)
mass  = drawpyo.diagram.Object(template_object=data, value="Mass (g)", page=page)
mass.center_position = (main_col - 200, 200)
```

To reproduce a shape you styled in the Draw.io app, copy its *Edit Style* string:

```python
obj = drawpyo.diagram.Object(page=page, value="X")
obj.apply_style_string("shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;")
```

## Containers & parent/child

Set `parent=` (or assign `.parent`) to nest a shape inside another. With `autosize_to_children=True`, the parent grows to wrap its children (plus `autosize_margin`, default 20). `autocontract=True` also lets it shrink.

```python
box = drawpyo.diagram.object_from_library(page=page, library="general", obj_name="labeled_container", value="VPC")
box.autosize_to_children = True
web = drawpyo.diagram.Object(page=page, value="web", parent=box, position=(60, 100))
db  = drawpyo.diagram.Object(page=page, value="db",  parent=box, position=(60, 200))
```

`position` of a child is in page coordinates; `position_rel_to_parent` gives/sets it relative to the container's top-left. Containers for nesting: `container`, `labeled_container`, `labeled_horizontal_container`.

## Group

`drawpyo.diagram.Group(objects=[...])` is a lightweight Python-side helper to move a set of objects together — it is **not** a real Draw.io group (no grouping in the output). Use it to reposition a cluster: `group.add_object(obj_or_list)`, then set `group.position` or `group.center_position` and all members shift. Charts/legends use this internally and expose `.group`.

## List (extended object)

`drawpyo.diagram.extended_objects.List(title="List", list_items=[...], page=page)` renders a Draw.io list shape with a header and rows that auto-size.

```python
lst = drawpyo.diagram.extended_objects.List(page=page, title="Checklist", list_items=["Design", "Build", "Test"])
lst.add_item("Ship")
lst.remove_item("Design")
print(lst.list_items)  # ['Build', 'Test', 'Ship']
```

---

## Edge

`drawpyo.diagram.Edge(source=None, target=None, **kwargs)` — a connector/arrow. Pass `page=` to render it. Setting `source`/`target` auto-registers the edge on those objects (`obj.in_edges` / `obj.out_edges`), so removing an object cleans up its edges.

```python
drawpyo.diagram.Edge(
    page=page, source=a, target=b,
    label="yes",
    waypoints="orthogonal", connection="line", pattern="solid",
    line_end_target="classic", endFill_target=True)
```

Key kwargs:

| kwarg | meaning |
| --- | --- |
| `source`, `target` | the `Object`s the edge connects |
| `label` | text on the edge (alias of `value`) |
| `label_position` | along the edge: -1 source … 0 center … 1 target |
| `label_offset` | perpendicular offset in px |
| `waypoints` | routing style (see list) |
| `connection` | line vs arrow body (see list) |
| `pattern` | dash pattern (see list) |
| `line_end_target` / `line_end_source` | arrowhead at each end (see list) |
| `endFill_target` / `endFill_source` | fill the arrowhead (only for fillable ends) |
| `endSize` / `startSize` | arrowhead size (pt) |
| `strokeColor`, `strokeWidth` (1–999), `fillColor` | `#RRGGBB` / `"none"` / `"default"` |
| `rounded`, `sketch`, `shadow`, `flowAnimation` | style flags |
| `jumpStyle` (`arc`/`gap`/`sharp`/`line`), `jumpSize` | line-jump rendering |
| `opacity` | 0–100 |
| `entryX/entryY/entryDx/entryDy`, `exitX/exitY/exitDx/exitDy` | precise connection points |

Add manual bend points:
```python
e = drawpyo.diagram.Edge(page=page, source=a, target=b)
e.add_point(300, 150)            # x, y in px
e.add_point_pos((300, 250))      # via tuple
```

`edge.remove()` detaches it from source/target and deletes it.

## Edge style values (complete)

These come from drawpyo's internal `edge_styles.toml`; anything else raises `ValueError`.

- **waypoints**: `straight`, `orthogonal` (default), `vertical`, `horizontal`, `isometric`, `isometric_vertical`, `curved`, `entity_relation`.
- **connection**: `line` (default), `link`, `arrow` (filled block arrow), `simple_arrow`. (`None` also allowed → plain line.)
- **pattern**: `solid` (default), `dashed_small`, `dashed_medium`, `dashed_large`, `dotted_small`, `dotted_medium`, `dotted_large`.
- **line_end_target / line_end_source** (arrowheads): `classic`, `classicThin`, `open`, `openThin`, `openAsync`, `block`, `blockThin`, `async`, `oval`, `diamond`, `diamondThin`, `dash`, `halfCircle`, `cross`, `circlePlus`, `circle`, `baseDash`, `doubleBlock`, and the entity-relation ends `ERone`, `ERmandOne`, `ERmany`, `ERoneToMany`, `ERzeroToOne`, `ERzeroToMany`. Use `None`/`"none"`/`""` for no arrowhead. **Fillable** ends (respect `endFill_*`): `classic`, `classicThin`, `block`, `blockThin`, `async`, `oval`, `diamond`, `diamondThin`, `doubleBlock`. The rest ignore fill.

## Connection points & waypoints

`entryX`/`entryY` and `exitX`/`exitY` are fractions `0..1` over the target/source shape's bounding box (0,0 = top-left, 1,1 = bottom-right; 0.5,0.5 = center). `entryDx`/`entryDy` (and exit equivalents) nudge the point by pixels. This is how you make edges leave the bottom of one box and enter the top of the next:

```python
drawpyo.diagram.Edge(page=page, source=parent, target=child,
    exitX=0.5, exitY=1,   # leave bottom-center of source
    entryX=0.5, entryY=0) # enter top-center of target
```

## TextFormat

`drawpyo.diagram.text_format.TextFormat(**kwargs)` — attach via `text_format=` on an `Object`/`Edge`, or set `obj.text_format = TextFormat(...)`.

| kwarg | meaning |
| --- | --- |
| `bold`, `italic`, `underline` | bool flags (combined into Draw.io fontStyle) |
| `fontSize` | points |
| `fontColor` | `#RRGGBB` |
| `fontFamily` | typeface name as in Draw.io |
| `align` | `left` / `center` / `right` (horizontal) |
| `verticalAlign` | `top` / `middle` / `bottom` |
| `direction` | `horizontal` / `vertical` text |
| `textOpacity` | 0–100 |
| `labelPosition`, `labelBackgroundColor`, `labelBorderColor` | label box placement/colors |
| `spacing`, `spacingTop/Left/Bottom/Right` | inner text padding |
| `formattedText` | render `value` as HTML (enables `<b>`, `<br>`, etc.) |

```python
tf = drawpyo.diagram.text_format.TextFormat(bold=True, fontSize=14, fontColor="#222222",
                                            align="center", verticalAlign="middle")
node = drawpyo.diagram.Object(page=page, value="Header", text_format=tf)
```
