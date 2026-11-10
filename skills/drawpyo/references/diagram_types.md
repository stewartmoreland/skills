# Automatic Diagram Types

Verified against drawpyo 0.2.5. These classes compute layout for you. Two groups: **trees** (`TreeDiagram`, `BinaryTreeDiagram`) which own their own File+Page and lay nodes out hierarchically, and **charts** (`BarChart`, `PieChart`, `Legend`) which build a `Group` of objects you add onto an existing Page.

Import from `drawpyo.diagram_types`:
```python
from drawpyo.diagram_types import (
    TreeDiagram, NodeObject,
    BinaryTreeDiagram, BinaryNodeObject,
    BarChart, PieChart, Legend,
)
```

## Contents
- [TreeDiagram + NodeObject](#treediagram--nodeobject)
- [TreeDiagram.from_dict](#treediagramfrom_dict)
- [BinaryTreeDiagram + BinaryNodeObject](#binarytreediagram--binarynodeobject)
- [BarChart](#barchart)
- [PieChart](#piechart)
- [Legend](#legend)

---

## TreeDiagram + NodeObject

The original reason drawpyo exists: hierarchical directed trees with automatic layout. `TreeDiagram` creates its **own** `File` and `Page` internally — you do not create them yourself. You add `NodeObject`s, call `auto_layout()`, then `write()`.

```python
from drawpyo.diagram_types import TreeDiagram, NodeObject

tree = TreeDiagram(file_path="/path/out", file_name="org.drawio", direction="down")

ceo = NodeObject(tree=tree, value="CEO")
cto = NodeObject(tree=tree, value="CTO", tree_parent=ceo)
cfo = NodeObject(tree=tree, value="CFO", tree_parent=ceo)
NodeObject(tree=tree, value="Eng Lead", tree_parent=cto)
NodeObject(tree=tree, value="QA Lead",  tree_parent=cto)

tree.auto_layout()   # penultimate step — computes positions
tree.write()
```

`TreeDiagram` kwargs:

| kwarg | meaning | default |
| --- | --- | --- |
| `direction` | growth direction: `up`, `down`, `left`, `right` | `down` |
| `link_style` | edge routing: `orthogonal`, `straight`, `curved` | `orthogonal` |
| `level_spacing` | px between levels | 60 |
| `item_spacing` | px between groups within a level | 15 |
| `padding` | px between objects within a group | 10 |
| `file_name`, `file_path` | output location | — |

`NodeObject(tree=, value=, tree_parent=, **Object kwargs)` — a node is an `Object`, so all styling kwargs (`fillColor`, `color_scheme`, `text_format`, `base_style`, width/height) apply. Defaults to a rounded rectangle.

- A node has **one** `tree_parent` and any number of children. Multiple parents are **not** supported by auto-layout.
- `parent.add_child(node)` is an alternative to passing `tree_parent=`.
- `node.add_peer(other)` draws a dashed non-hierarchical link between two nodes (rendered after layout).
- You can still add arbitrary `Edge`s between any nodes on `tree.page`; they just may need manual cleanup in the app.

Always call `auto_layout()` before `write()`, or every node sits at the origin.

## TreeDiagram.from_dict

Build an entire tree from a nested `dict`/`list` in one call — no manual `NodeObject`s.

```python
data = {
    "Company": {
        "Engineering": ["Backend", "Frontend", "Infra"],
        "Sales": {"AMER": ["East", "West"], "EMEA": ["UK"]},
    }
}
tree = TreeDiagram.from_dict(
    data,
    file_path="/path/out", file_name="company.drawio",
    direction="down",
    colors=["#DAE8FC", "#D5E8D4", "#FFE6CC", "#F8CECC"],
    coloring="depth",
)
tree.write()   # from_dict already runs auto_layout()
```

Conversion rules:
- **dict** → each key becomes a node; its value becomes that node's children (recurse).
- **list / tuple** → siblings under the current parent (the list itself is not a node).
- **str / int / float** → a leaf node.
- Top level must be a `dict`.

`colors` is an optional palette (list of hex strings, `StandardColor`s, or `ColorScheme`s). `coloring` selects how the palette maps to nodes:
- `"depth"` (default) — color by tree depth.
- `"hash"` — stable color from a hash of the node's text.
- `"type"` — color by node role (category / list_item / leaf).

`from_dict` already calls `auto_layout()`, so just `write()` afterward.

## BinaryTreeDiagram + BinaryNodeObject

A `TreeDiagram` specialized so each node has at most two children, exposed as `.left` / `.right`. Defaults differ: `level_spacing=80`, `item_spacing=20`, `link_style="straight"`.

```python
from drawpyo.diagram_types import BinaryTreeDiagram, BinaryNodeObject

bt = BinaryTreeDiagram(file_path="/path/out", file_name="bst.drawio")
root  = BinaryNodeObject(tree=bt, value="50")
left  = BinaryNodeObject(tree=bt, value="30")
right = BinaryNodeObject(tree=bt, value="70")
bt.add_left(root, left)
bt.add_right(root, right)
bt.auto_layout()
bt.write()
```

- `node.left` / `node.right` are gettable/settable; assigning enforces the two-child limit and re-parents cleanly.
- `bt.add_left(parent, child)` / `bt.add_right(parent, child)` are the convenience attach methods (both must be `BinaryNodeObject`).
- `BinaryTreeDiagram.from_dict(data, colors=, coloring=)` works like the tree version, with an extra `coloring="directional"` mode (index 0 colors left children, index 1 colors right). In dict form the **first** key/element of a node is the left child, the second is the right; a list node may have at most two elements.

## BarChart

`BarChart(data: dict[str, float], **kwargs)` builds a bar chart as a `Group`. It does **not** own a page — call `chart.add_to_page(page)`.

```python
from drawpyo.diagram_types import BarChart

file = drawpyo.File(file_name="sales.drawio", file_path="/path/out")
page = drawpyo.Page(file=file)

bar = BarChart(
    {"Q1": 120, "Q2": 240, "Q3": 180, "Q4": 300},
    title="2025 Revenue ($k)",
    show_axis=True,
    bar_colors=["#66ccff", "#ff9966", "#99cc66", "#cc99ff"],
    rounded=True,
)
bar.add_to_page(page)
file.write()
```

Kwargs: `position=(0,0)`, `bar_width=40`, `bar_spacing=20`, `max_bar_height=200`, `bar_colors=[...]` (cycles if shorter than data; accepts hex / `StandardColor` / `ColorScheme`), `title`, `title_text_format`, `base_text_format`, `inside_text_format`, `axis_text_format` (all `TextFormat`), `base_label_formatter` / `inside_label_formatter` (callables `(label, value) -> str`), `background_color`, `show_axis=False`, `axis_tick_count=5`, `glass=False`, `rounded=False`.

Mutable after creation: `bar.update_data({...})`, `bar.update_colors([...])`, `bar.move((x, y))`. Negative values are not supported. The bar's data dict keys must be strings and values numeric (else `TypeError`).

## PieChart

`PieChart(data: dict[str, float], **kwargs)` — same add-to-page model.

```python
from drawpyo.diagram_types import PieChart
pie = PieChart(
    {"Direct": 45, "Search": 30, "Social": 25},
    title="Traffic sources",
    size=240,
    slice_colors=["#DAE8FC", "#D5E8D4", "#FFE6CC"],
)
pie.add_to_page(page)
```

Kwargs: `position`, `size=200` (diameter), `slice_colors=[...]`, `title`, `title_text_format`, `label_text_format`, `background_color`, `label_formatter` (callable `(label, value, total) -> str`; default shows `"label: NN.N%"`). Mutable: `update_data`, `update_colors`, `move`.

## Legend

`Legend(mapping: dict[str, color], **kwargs)` — a color/label key as a `Group`.

```python
from drawpyo.diagram_types import Legend
legend = Legend(
    {"Pass": "#D5E8D4", "Fail": "#F8CECC", "Skipped": "#FFF2CC"},
    title="Test status",
)
legend.add_to_page(page)
```

Kwargs: `position`, `title`, `title_text_format`, `label_text_format`, `glass=False`, `rounded=False`, `background_color`. Mutable: `update_mapping`, `move`. Colors may be hex, `StandardColor`, or `ColorScheme`.

Charts and legends are ordinary objects once added — you can place several on one page (set distinct `position`s or call `move`) alongside manual shapes.
