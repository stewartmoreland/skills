# Datasets & Annotation

Everything upstream of training. Get this stage right and training "just works"; get it wrong and you lose
hours to silent failures. Read top-to-bottom the first time, then jump to the relevant section.

- [The YOLO dataset layout](#the-yolo-dataset-layout)
- [data.yaml](#datayaml)
- [Label formats per task](#label-formats-per-task)
- [Converting from other formats](#converting-from-other-formats)
- [Annotation tools](#annotation-tools)
- [Auto-annotation](#auto-annotation-bootstrap-labels-with-a-model)
- [Curating & debugging datasets with FiftyOne](#curating--debugging-with-fiftyone)
- [Common dataset failures](#common-dataset-failures)

## The YOLO dataset layout

Ultralytics expects images and labels in **parallel trees** where each image has a same-stem `.txt` label
beside it under a `labels/` mirror of `images/`:

```
datasets/mydata/
├── images/
│   ├── train/  img001.jpg  img002.jpg ...
│   ├── val/    ...
│   └── test/   ...            # optional
└── labels/
    ├── train/  img001.txt  img002.txt ...
    ├── val/    ...
    └── test/   ...
```

The resolver finds labels by replacing `images` with `labels` in the path and swapping the extension to
`.txt`. An image with **no objects** gets an empty `.txt` (this is a valid negative/background example, not
an error). Classification is the exception — see [tasks.md](tasks.md) (it uses `train/<class>/img.jpg`
folders, no label files).

## data.yaml

The dataset descriptor. Modern format uses a `path` root plus relative split paths and a `names` mapping:

```yaml
path: ../datasets/mydata      # dataset root (relative to the ultralytics settings 'datasets_dir', or absolute)
train: images/train           # relative to 'path'
val: images/val
test: images/test             # optional

names:                        # index -> class name; index is what appears in label files
  0: person
  1: bicycle
  2: car
```

`names` can also be a plain list (`["person","bicycle","car"]`) — index = position. `nc` (number of classes)
is inferred from `names` and usually omitted. **The `path` resolution trips people up:** relative `path` is
resolved against the Ultralytics `datasets_dir` setting, *not* the current working directory. Prefer an
**absolute `path`** in generated configs to remove ambiguity, or confirm `yolo settings` shows the expected
`datasets_dir`.

## Label formats per task

All coordinates are **normalized to [0, 1]** by image width/height. One line per object. First field is
always the 0-based class index. (Full per-task detail and metrics in [tasks.md](tasks.md).)

| Task | Line format |
|------|-------------|
| Detect | `cls cx cy w h` (box center + size) |
| Segment | `cls x1 y1 x2 y2 … xn yn` (polygon, ≥3 points) |
| Pose | `cls cx cy w h px1 py1 v1 px2 py2 v2 …` (`v`=visibility 0/1/2) |
| OBB | `cls x1 y1 x2 y2 x3 y3 x4 y4` (4 corners, not axis-aligned) |
| Classify | *no label files* — class is the parent folder name |

Example detection line (class 2, centered box covering middle 30%×40%):
`2 0.5 0.5 0.3 0.4`

## Converting from other formats

Use the built-in converters before writing your own — they handle the index remapping correctly.

```python
from ultralytics.data.converter import convert_coco

# COCO JSON -> YOLO txt. COCO category ids are 1-based with gaps; this remaps them to
# contiguous 0-based indices. Keep the resulting names order — it's now load-bearing.
convert_coco(labels_dir="path/to/coco/annotations/", save_dir="path/to/yolo/",
             use_segments=False, use_keypoints=False)
```

Other common sources:
- **COCO** → `convert_coco(...)` (set `use_segments=True` for seg, `use_keypoints=True` for pose).
- **Pascal VOC XML** → no first-party converter; parse XML, denormalize VOC's absolute pixel boxes to
  normalized `cx cy w h`. Verify with `scripts/verify_dataset.py` after.
- **Roboflow** → export directly in "YOLOv8/YOLO11" format; it ships a ready `data.yaml`. Just fix `path`.
- **DOTA (OBB)** → `convert_dota_to_yolo_obb(...)` in the same converter module.

After **any** conversion, run `scripts/verify_dataset.py` — conversions are the #1 source of off-by-one
class indices and un-normalized coordinates.

## Annotation tools

Match the tool to the situation rather than defaulting to one:

- **Roboflow** — fastest path from raw images to a trained-ready dataset for small/medium projects. Hosted
  labeling, augmentation, versioning, and one-click YOLO export. Good when the user wants minimal infra.
- **CVAT** — open-source, self-hostable, strong for video/sequential frames and large teams. Exports YOLO
  format directly. Best when data can't leave the user's infra.
- **Label Studio** — flexible, self-hostable, handles mixed modalities; YOLO export via its converter. Good
  when labeling more than just boxes, or integrating into an existing ML pipeline.
- **FiftyOne** — not primarily an annotator but the best tool for *inspecting, curating, and finding label
  errors* (see below); pairs with CVAT for a curate→relabel loop.

Don't hand-build a labeling UI. Pick one of the above and export to YOLO format.

## Auto-annotation (bootstrap labels with a model)

For large unlabeled sets, pre-label with a detector + SAM, then have humans correct — far faster than
labeling from scratch:

```python
from ultralytics.data.annotator import auto_annotate

auto_annotate(
    data="path/to/images",        # folder of unlabeled images
    det_model="yolo26x.pt",       # detector proposes boxes (use a large/accurate model here)
    sam_model="sam_b.pt",         # SAM refines to masks/precise regions
    output_dir="path/to/labels",  # YOLO-format labels written here
)
```

Then load the result into CVAT/Label Studio for human review. Open-vocabulary models (`yoloe-26*`) can
pre-label *novel* classes from a text prompt when you don't yet have a trained detector.

## Curating & debugging with FiftyOne

Before blaming the model, inspect the data. FiftyOne loads a YOLO dataset into an interactive app to spot
mislabels, class imbalance, duplicates, and annotation gaps:

```python
import fiftyone as fo
ds = fo.Dataset.from_dir(dataset_dir="datasets/mydata", dataset_type=fo.types.YOLOv5Dataset, split="train")
fo.launch_app(ds)
```

After training, load predictions alongside ground truth to find systematic failure clusters — this is
usually more productive than another round of hyperparameter tweaking.

## Common dataset failures

- **Wrong `path` resolution** → "0 images found". Use absolute `path` or check `yolo settings`.
- **`images`/`labels` not mirrored** → labels silently not found, model trains on nothing.
- **Class index ≥ len(names)** → crash or garbage; classic after a COCO/VOC conversion.
- **Un-normalized coords** (pixels instead of 0–1) → boxes off-image, NaN loss.
- **Reordered `names`** after labeling → every label now points at the wrong class.
- **Train/val leakage** (same images in both) → inflated mAP that collapses in production.

`scripts/verify_dataset.py` catches the first four mechanically. The last two need a human eye plus FiftyOne.
