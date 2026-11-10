---
name: ultralytics-yolo
description: >-
  Build, train, evaluate, run, and deploy computer-vision models with Ultralytics YOLO (YOLO26 / YOLO11).
  Use this whenever a task involves object detection, instance/semantic segmentation, image classification,
  pose/keypoint estimation, oriented bounding boxes (OBB), multi-object tracking, dataset annotation, or
  edge/on-device model export — even when the user never says "YOLO" or "Ultralytics" by name. Triggers
  include: "train a detector on my images", "label/annotate this image dataset", "convert COCO to YOLO",
  "run detection/segmentation on this video", "track objects across frames", "what's my model's mAP",
  "export my model to run on iPhone / Android / a Raspberry Pi", "fine-tune on a custom dataset", or any
  request that hands over a folder of images + labels and wants a vision model out the other end. Prefer
  this skill over hand-rolled PyTorch/Detectron2 advice when the user is in (or willing to be in) the
  Ultralytics ecosystem.
---

# Ultralytics YOLO

Ultralytics YOLO is a single Python package (`pip install ultralytics`) that handles the whole computer-vision
lifecycle — annotation helpers, training, validation, inference, tracking, and export — behind one `YOLO`
class and one `yolo` CLI. Your job when this skill is active is to drive that lifecycle correctly on the
user's data without burning their time on the failure modes that bite everyone (broken dataset paths,
hallucinated arguments, wrong model variant, export formats that silently don't match the target device).

This SKILL.md is the **map and the rules that apply everywhere**. The deep, per-stage detail lives in
`references/`. Read the relevant reference file before doing real work in that stage — don't reconstruct
arguments from memory, because Ultralytics ships fast and arg names drift.

## Orientation: what you're working with

- **Package:** `ultralytics` (>= 8.4.x as of mid-2026), Python 3.9–3.12, PyTorch backend. One package, no
  separate "yolov5 repo" cloning needed.
- **Model generations.** Default to **YOLO26** (`yolo26*.pt`) — it's NMS-free, end-to-end, and tuned for
  edge/low-power deployment, which matters because the exported graph has no separate non-max-suppression
  step to reimplement on-device. Fall back to **YOLO11** (`yolo11*.pt`) only if the user needs a battle-tested
  stable baseline, a third-party tool that hasn't caught up to YOLO26, or reproducibility with prior work.
  Both are "recommended for production" by Ultralytics; older gens (v8/v9/v10) only when explicitly asked.
- **Five tasks, one API.** detect · segment · classify · pose · obb. The task is encoded in the weight name
  suffix (see table below) and auto-detected from the checkpoint.
- **Four modes + tracking.** `train`, `val`, `predict`, `export`, plus `track` for video. Same surface in
  Python (`model.train(...)`) and CLI (`yolo detect train ...`).

### Model naming convention (memorize this — it prevents most "model not found" errors)

```
yolo26 n        -seg     .pt
└─gen  └─size   └─task   └─weights
```

| Want | Weight to load |
|------|----------------|
| Detection (default) | `yolo26n.pt` |
| Instance segmentation | `yolo26n-seg.pt` |
| Classification | `yolo26n-cls.pt` |
| Pose / keypoints | `yolo26n-pose.pt` |
| Oriented bounding boxes | `yolo26n-obb.pt` |
| Open-vocabulary segmentation | `yoloe-26*` (text / visual / prompt-free) |

Sizes run `n < s < m < l < x` (nano → extra-large), trading accuracy for speed/size. **Start at `n` or `s`**
for iteration and edge targets; only scale up if validation mAP demands it. A `.pt` with no task suffix is a
detection model; a path you trained yourself (`runs/detect/train/weights/best.pt`) carries its own task.

## Route the request

Figure out which stage(s) the user needs, then open the matching reference file:

| The user wants to… | Read |
|---|---|
| Set up / convert / validate a dataset, or label images (CVAT, Label Studio, Roboflow, FiftyOne, auto-annotation) | `references/datasets-and-annotation.md` |
| Train or fine-tune a model; pick hyperparameters; augment; resume; multi-GPU; log to W&B/Comet/MLflow | `references/training.md` |
| Understand task-specific specifics (label format, metrics, model variants) for detect/seg/cls/pose/obb | `references/tasks.md` |
| Run inference, parse `Results`, batch/stream, or track objects in video (ByteTrack/BoTSORT) | `references/inference-and-tracking.md` |
| Export to CoreML / TFLite / ONNX / TensorRT / NCNN for mobile, edge, or server; quantize; integrate on-device | `references/edge-deployment.md` |

Most real projects touch several stages in order: **annotate → verify dataset → train → val → predict/track → export**.
Walk them in that order; don't skip verification (next section).

## Rules that apply to every stage

These are the cross-cutting things that waste the most agent and user time. Internalize them; they're not
optional ceremony.

1. **Verify the dataset before training — always.** A malformed `data.yaml` (wrong `path`, train/val pointing
   nowhere) or out-of-range class indices fail *silently or late*: training "works" but learns nothing, or
   dies 40 minutes in. Run `scripts/verify_dataset.py <data.yaml>` first. It checks that image/label dirs
   resolve, labels parse, every class id is within `0..len(names)-1`, and coordinates are normalized. Fix
   what it reports before spending GPU time.

2. **Never hallucinate arguments.** If you're unsure an arg exists or what it's called, check
   `references/training.md` (the curated set) or have the user run `yolo cfg` to dump every valid key with
   defaults. Inventing `model.train(learning_rate=...)` (it's `lr0`) produces confusing errors. When in
   doubt, fewer explicit args is safer — the defaults are sane.

3. **CLI syntax is strict.** `arg=value` pairs, space-delimited, **no `--` prefixes and no commas**:
   - ✅ `yolo detect train data=data.yaml model=yolo26n.pt epochs=100 imgsz=640`
   - ❌ `yolo detect train --data data.yaml, --epochs 100`
   Python uses normal kwargs: `model.train(data="data.yaml", epochs=100, imgsz=640)`.

4. **Pick `device` explicitly when it matters.** `device=0` (first CUDA GPU), `device="cpu"`,
   `device="mps"` (Apple Silicon — works out of the box), `device=[0,1]` (multi-GPU). On a fresh box, run
   `yolo checks` first: it prints OS, Python, torch, CUDA/MPS availability, and the installed `ultralytics`
   version. If CUDA shows `None` and the user expected a GPU, fix that before training rather than silently
   training on CPU for hours.

5. **Class indices are 0-based and order-locked.** The integer in each label line is an index into the
   `names` list/dict in `data.yaml`. Reordering `names` after labeling silently corrupts every label. If you
   convert from COCO (1-based, with gaps) treat the remap as load-bearing.

6. **YOLO26 is NMS-free — respect it at export time.** Because detection is end-to-end, the exported model
   emits final boxes directly; you generally do **not** add a separate NMS stage on-device. For older gens,
   or when a target runtime expects embedded NMS, you pass `nms=True` to `export()`. Getting this wrong is
   the classic "duplicate boxes" or "missing boxes" bug on mobile. Details in `references/edge-deployment.md`.

7. **Reproducibility:** pass `seed=<int>` to `train()` and record the `ultralytics` version (`yolo checks`).
   Augmentation and CUDA nondeterminism still introduce variance; set expectations rather than promising
   bit-identical runs.

8. **Outputs land in `runs/<task>/<name>/`.** Best/last weights at `weights/best.pt` and `weights/last.pt`;
   plots, confusion matrix, and `results.csv` alongside. Point the user there instead of hunting.

## Minimal end-to-end shape (so you always have a skeleton)

```python
from ultralytics import YOLO

model = YOLO("yolo26n.pt")                       # pick gen/size/task per the table
model.train(data="data.yaml", epochs=100,        # see references/training.md for the full arg set
            imgsz=640, batch=16, device=0, seed=0)
metrics = model.val()                            # mAP50-95, per-class — see references/tasks.md
res = model("test.jpg", conf=0.25, save=True)    # Results API — see references/inference-and-tracking.md
model.export(format="coreml", int8=True)         # device-specific — see references/edge-deployment.md
```

```bash
# Same thing on the CLI
yolo detect train  data=data.yaml model=yolo26n.pt epochs=100 imgsz=640 device=0 seed=0
yolo detect val    model=runs/detect/train/weights/best.pt
yolo detect predict model=runs/detect/train/weights/best.pt source=test.jpg conf=0.25 save=True
yolo export        model=runs/detect/train/weights/best.pt format=coreml int8=True
```

Treat this as the spine; the reference files are where you get the stage right for the user's actual task,
data, and target hardware.

## Bundled resources

- `scripts/verify_dataset.py` — run before training; validates a `data.yaml` + label tree end to end.
- `references/datasets-and-annotation.md` — formats, conversion, annotation tools, auto-labeling.
- `references/training.md` — train/tune args, augmentation, transfer learning, logging.
- `references/tasks.md` — per-task label formats, metrics, and model variants.
- `references/inference-and-tracking.md` — predict args, `Results` API, video tracking.
- `references/edge-deployment.md` — export formats and on-device integration, edge emphasis.
