# Training & Fine-Tuning

How to actually train a model well on the user's data. The defaults are good — most of the skill here is
knowing *which* knobs to touch and which to leave alone.

- [The training call](#the-training-call)
- [Arguments that matter most](#arguments-that-matter-most)
- [Transfer learning vs. from scratch](#transfer-learning-vs-from-scratch)
- [Augmentation](#augmentation)
- [Resuming & fine-tuning checkpoints](#resuming--fine-tuning-checkpoints)
- [Multi-GPU](#multi-gpu)
- [Hyperparameter tuning](#hyperparameter-tuning)
- [Experiment logging](#experiment-logging)
- [Reading the results](#reading-the-results)
- [Troubleshooting training](#troubleshooting-training)

## The training call

```python
from ultralytics import YOLO

model = YOLO("yolo26n.pt")          # pretrained weights = transfer learning (almost always what you want)
results = model.train(
    data="data.yaml",
    epochs=100,
    imgsz=640,
    batch=16,                       # or batch=-1 for AutoBatch (≈60% GPU mem), or 0.7 for 70% mem
    device=0,
    seed=0,
    project="runs", name="exp1",    # output -> runs/detect/exp1/
)
```

CLI equivalent:
```bash
yolo detect train data=data.yaml model=yolo26n.pt epochs=100 imgsz=640 batch=16 device=0 seed=0
```

Always run `scripts/verify_dataset.py data.yaml` **before** this. Always confirm `device` with `yolo checks`.

## Arguments that matter most

You rarely need more than these. For the exhaustive list with defaults, run `yolo cfg` rather than guessing.

| Arg | What it does | Guidance |
|-----|--------------|----------|
| `epochs` | training passes | 100 is a sane start; small datasets may want `patience`-based early stop instead of more epochs |
| `imgsz` | input resolution | 640 default. Higher (1280) helps small objects but costs memory/speed quadratically |
| `batch` | images per step | Largest that fits. `-1` = AutoBatch; a float like `0.7` targets that GPU-memory fraction |
| `lr0` / `lrf` | initial / final LR factor | Leave default unless tuning; **not** `learning_rate` |
| `patience` | early-stop patience (epochs w/o val improvement) | Default 100; lower (e.g. 20) to stop dead runs sooner |
| `optimizer` | `auto`/`SGD`/`AdamW`/`MuSGD` | `auto` picks for you; YOLO26 introduces `MuSGD` |
| `cos_lr` | cosine LR schedule | helps longer runs |
| `freeze` | freeze first N layers | freeze backbone for fast fine-tune on small data |
| `device` | compute target | `0`, `"cpu"`, `"mps"`, `[0,1]` |
| `workers` | dataloader workers | lower if you hit shared-memory/`/dev/shm` errors |
| `seed` | RNG seed | set for reproducibility |
| `resume` | continue an interrupted run | see below |

**Don't** invent args. If a user asks for something you can't map to a real key, check `yolo cfg` output
before writing code.

## Transfer learning vs. from scratch

Default to **transfer learning**: load a pretrained `yolo26n.pt` (COCO weights) and `train()` on the user's
data. It converges faster and needs far less data. Only train from scratch (`YOLO("yolo26n.yaml")`, no `.pt`)
when the domain is wildly off-distribution (e.g. medical/satellite with huge labeled sets) and the user
explicitly wants it — and warn them it needs much more data and time.

For small custom datasets, `freeze=10` (freeze the backbone) fine-tunes just the head: fast, resistant to
overfitting, often enough.

## Augmentation

YOLO applies a strong default augmentation pipeline (mosaic, flips, HSV jitter, scale/translate). Usually
leave it alone. Knobs worth knowing:

- `mosaic` (default ~1.0) — combines 4 images; great for detection generalization. YOLO disables it for the
  last `close_mosaic` (default 10) epochs so the model finishes on clean images.
- `mixup`, `copy_paste` — heavier; helpful for segmentation / rare classes.
- `hsv_h/hsv_s/hsv_v`, `degrees`, `translate`, `scale`, `fliplr`/`flipud` — fine-grained controls.
- **Domain caveats:** disable `fliplr` if left/right is semantically meaningful (e.g. reading gauges,
  directional signs). Disable `flipud` unless your imagery is orientation-agnostic (e.g. aerial). For OBB,
  rotation augmentation interacts with the angle target — keep defaults unless you know why.

## Resuming & fine-tuning checkpoints

- **Resume an interrupted run** (same data/config) from `last.pt`:
  ```python
  YOLO("runs/detect/exp1/weights/last.pt").train(resume=True)
  ```
- **Fine-tune `best.pt` on new/more data** — that's a fresh `train()` *without* `resume`, loading the prior
  best as the starting weights:
  ```python
  YOLO("runs/detect/exp1/weights/best.pt").train(data="more_data.yaml", epochs=50)
  ```
  `resume=True` continues the *old* schedule; omit it to start a new schedule from those weights.

## Multi-GPU

`device=[0,1]` triggers DistributedDataParallel automatically. Scale `batch` to total across GPUs. From the
CLI it's identical: `yolo detect train ... device=0,1`. Don't manually wrap in `torchrun` — Ultralytics
handles the spawn.

## Hyperparameter tuning

For systematic search, use the built-in evolutionary tuner rather than a hand-rolled grid:

```python
model.tune(data="data.yaml", epochs=30, iterations=300, optimizer="AdamW", plots=False, save=False)
```

It mutates hyperparameters across `iterations`, scoring each short run, and writes the best set to
`runs/.../tune/`. Expensive — only suggest it once the dataset is solid and a baseline exists. Ray Tune is
also supported (`use_ray=True`) if the user has the infra.

## Experiment logging

Ultralytics auto-integrates with several trackers — installing the package and setting it up is enough; no
code change to the `train()` call:

- **TensorBoard** — local, zero-config (`tensorboard --logdir runs`).
- **Weights & Biases**, **Comet**, **ClearML**, **MLflow**, **DVCLive** — `pip install` the integration and
  it logs metrics/artifacts automatically. Confirm via `yolo settings` which integrations are enabled.

Pick the one the user already uses. Don't bolt on a tracker they didn't ask for.

## Reading the results

After training, `runs/<task>/<name>/` contains:
- `weights/best.pt` (best val mAP) and `weights/last.pt` (final epoch).
- `results.csv` + `results.png` — loss and metric curves. **Curves still descending at the last epoch ⇒
  train longer.** Val loss rising while train loss falls ⇒ overfitting (more data/aug, fewer epochs, freeze).
- `confusion_matrix.png` — which classes get confused; drives targeted data collection.
- `*_curve.png` (PR, F1) — pick an operating `conf` threshold from these for deployment.

Point the user at `best.pt` and these plots; that's the feedback loop.

## Troubleshooting training

- **CUDA out of memory** → lower `batch` (or `batch=-1`), lower `imgsz`, use a smaller model size, or
  `amp=True` (on by default). 
- **`/dev/shm` or "DataLoader worker" errors** → lower `workers`.
- **mAP stuck near 0** → almost always a *data* problem, not a model one. Re-run
  `scripts/verify_dataset.py`, check class indices, and eyeball a few labels in FiftyOne.
- **Loss = NaN** → un-normalized labels or corrupt images; verify the dataset.
- **Trains on CPU unexpectedly** → `yolo checks` showed CUDA `None`; fix the torch/CUDA install.
