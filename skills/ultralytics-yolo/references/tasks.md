# Tasks: detect · segment · classify · pose · obb

The five tasks share one API but differ in label format, output structure, and the metric that matters.
Use this to pick the right model variant and read results correctly. Inference/`Results` parsing is in
[inference-and-tracking.md](inference-and-tracking.md); this file is about what each task *is*.

## Detection (default)

- **Weight:** `yolo26n.pt` · **Label:** `cls cx cy w h` (normalized).
- **Output:** `results[0].boxes` → `.xyxy`, `.xywhn`, `.conf`, `.cls`.
- **Primary metric:** **mAP50-95** (mean average precision averaged over IoU 0.5–0.95). `mAP50` is the
  lenient version. Also precision/recall per class.
- The bread-and-butter task. If the user just says "detect X", this is it.

## Instance segmentation

- **Weight:** `yolo26n-seg.pt` · **Label:** `cls x1 y1 x2 y2 … xn yn` (polygon, normalized).
- **Output:** `.boxes` **and** `.masks` (`.masks.xy` polygons, `.masks.data` binary mask tensors).
- **Metric:** mask mAP50-95 (plus box mAP). Watch the *mask* number, not just the box one.
- Use when the user needs pixel-precise outlines (area, overlap, shape) not just boxes. Heavier to label and
  train — push back gently if boxes would actually suffice.
- **Semantic** vs **instance:** YOLO26 supports both; instance (per-object masks) is the common case.
  Open-vocabulary segmentation of novel classes from a prompt → `yoloe-26*`.

## Classification

- **Weight:** `yolo26n-cls.pt` · **Data layout:** **no label files** — folders are classes:
  ```
  data/
  ├── train/  cat/ img1.jpg …   dog/ …
  └── val/    cat/ …            dog/ …
  ```
  Pass the dataset **root folder** as `data=`, not a yaml.
- **Output:** `results[0].probs` → `.top1`, `.top5`, `.top1conf`.
- **Metric:** top-1 / top-5 accuracy.
- Use for whole-image labels (no localization). Much cheaper than detection — if the user only needs "what
  is this image", don't reach for a detector.

## Pose / keypoint estimation

- **Weight:** `yolo26n-pose.pt` · **Label:** `cls cx cy w h px1 py1 v1 px2 py2 v2 …`
  - `v` = visibility: `0` not labeled, `1` labeled-but-occluded, `2` visible.
  - The keypoint **count and order are fixed by your `data.yaml`** via `kpt_shape: [num_kpts, dims]`
    (dims 2 = xy, 3 = xy+visibility). COCO human pose is 17 keypoints.
- **Output:** `.keypoints` → `.xy`, `.xyn`, `.conf`.
- **Metric:** pose mAP (OKS-based) plus box mAP.
- `data.yaml` needs the extra `kpt_shape` and (optionally) `flip_idx` so horizontal-flip augmentation swaps
  left/right keypoints correctly — **set `flip_idx` for human/animal pose or flips will corrupt training.**

## Oriented bounding boxes (OBB)

- **Weight:** `yolo26n-obb.pt` · **Label:** `cls x1 y1 x2 y2 x3 y3 x4 y4` (four corners, normalized).
- **Output:** `.obb` → `.xyxyxyxy`, `.xywhr` (center, size, rotation `r` in radians), `.conf`, `.cls`.
- **Metric:** mAP50-95 computed with rotated IoU.
- Use for rotated/aerial/document objects where an axis-aligned box wastes area or merges neighbors
  (satellite imagery, text, retail shelves at an angle). DOTA is the canonical dataset; convert via
  `convert_dota_to_yolo_obb`.

## Quick selection guide

| User goal | Task | Weight |
|-----------|------|--------|
| "Where are the objects?" (boxes) | detect | `yolo26n.pt` |
| "Outline each object precisely" | segment | `yolo26n-seg.pt` |
| "What is this whole image?" | classify | `yolo26n-cls.pt` |
| "Find body/joint positions" | pose | `yolo26n-pose.pt` |
| "Rotated / aerial / angled objects" | obb | `yolo26n-obb.pt` |
| "Detect a class I have no data for, from a text description" | open-vocab | `yoloe-26*` |

## Validation across tasks

`model.val()` returns a metrics object; the meaningful field differs by task (box vs mask vs pose mAP, or
top-1 acc). Always report the task-appropriate number — quoting box mAP for a segmentation model misleads
the user about mask quality. `model.val(split="test")` evaluates the held-out test split when present.
