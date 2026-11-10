# Inference & Tracking

Running a trained (or pretrained) model on images/video and parsing what comes back, plus multi-object
tracking across video frames.

- [Running prediction](#running-prediction)
- [Sources](#sources)
- [The Results object](#the-results-object)
- [Prediction arguments that matter](#prediction-arguments-that-matter)
- [Streaming & large jobs](#streaming--large-jobs)
- [Tracking](#tracking)
- [Video pipelines](#video-pipelines)

## Running prediction

```python
from ultralytics import YOLO
model = YOLO("runs/detect/exp1/weights/best.pt")   # or a pretrained yolo26n.pt

results = model.predict(source="image.jpg", conf=0.25, save=True)
# shorthand: model("image.jpg")
```

`predict` returns a **list of `Results`** — one per image (or per frame). CLI:
```bash
yolo detect predict model=best.pt source=image.jpg conf=0.25 save=True
```

## Sources

`source=` is flexible — match it to the input:

| Source | Example |
|--------|---------|
| Single image | `"img.jpg"` |
| Folder / glob | `"images/"`, `"images/*.jpg"` |
| Video file | `"clip.mp4"` |
| Image array | a NumPy `HWC BGR` array or PIL image |
| Webcam | `0` (device index) |
| RTSP/HTTP stream | `"rtsp://…"`, `"https://…/stream.m3u8"` |
| YouTube | `"https://youtu.be/…"` |
| List | `["a.jpg", "b.jpg"]` |

## The Results object

Each `Results` carries only the fields relevant to its task (see [tasks.md](tasks.md)):

```python
r = results[0]
r.boxes        # detection/seg/obb boxes: .xyxy .xywhn .conf .cls
r.masks        # segmentation: .xy (polygons), .data (binary masks)
r.keypoints    # pose: .xy .xyn .conf
r.obb          # obb: .xyxyxyxy .xywhr
r.probs        # classification: .top1 .top5 .top1conf
r.names        # index -> class name
r.plot()       # -> annotated BGR ndarray (for cv2.imshow / saving)
r.save(filename="out.jpg")
r.to_json()    # serialize detections (also .to_df() for a DataFrame)
```

Iterate detections explicitly when you need the data, not just an annotated image:

```python
for r in results:
    for box in r.boxes:
        cls_name = r.names[int(box.cls)]
        conf = float(box.conf)
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        ...
```

## Prediction arguments that matter

| Arg | Effect |
|-----|--------|
| `conf` | confidence threshold (default 0.25). Raise to cut false positives |
| `iou` | NMS IoU threshold (default 0.7). **No effect on YOLO26 end-to-end models** — they're NMS-free |
| `imgsz` | inference resolution; match training for best accuracy |
| `device` | `0` / `"cpu"` / `"mps"` |
| `half` | FP16 inference on GPU — faster, lower memory |
| `classes` | filter to a subset, e.g. `classes=[0, 2]` |
| `save`, `save_txt`, `save_conf`, `save_crop` | persist annotated images / YOLO-format predictions / crops |
| `stream` | return a generator instead of a list (see next) |
| `max_det` | cap detections per image |
| `vid_stride` | process every Nth video frame |

## Streaming & large jobs

For videos, folders, or live streams, **`stream=True`** returns a generator that yields one `Results` at a
time instead of building a giant in-memory list — essential to avoid OOM on long inputs:

```python
for r in model.predict(source="long_video.mp4", stream=True):
    process(r)        # handle each frame as it arrives
```

Without `stream=True` a long video tries to materialize every frame's results at once.

## Tracking

Tracking assigns persistent IDs to detections across frames. Use `model.track` (not `predict`) — it adds an
ID to each box:

```python
for r in model.track(source="clip.mp4", tracker="bytetrack.yaml", persist=True, stream=True):
    for box in r.boxes:
        track_id = int(box.id) if box.id is not None else None
        ...
```

- **Trackers:** `bytetrack.yaml` (fast, robust default) or `botsort.yaml` (adds appearance/ReID and camera-
  motion compensation — better through occlusions, heavier). Start with ByteTrack; switch to BoT-SORT if IDs
  swap too often.
- `persist=True` keeps tracks alive across successive calls when you feed frames yourself.
- Tracking works for detect / segment / pose / obb models. To customize tracker thresholds, copy the yaml,
  edit it, and pass your path.

## Video pipelines

For end-to-end video apps (counting, dwell time, zone intrusion), the cleanest path is **Ultralytics
Solutions** rather than re-implementing logic on raw `Results`:

```python
from ultralytics import solutions
counter = solutions.ObjectCounter(model="yolo26n.pt", region=[(x1,y1),(x2,y2),...], show=True)
# feed frames (e.g. via cv2.VideoCapture) -> counter(frame)
```

Solutions cover object counting, heatmaps, speed estimation, region/line crossing, and more — they wrap
tracking + the geometry so you don't hand-roll it. For fully custom logic, drive `model.track(stream=True)`
yourself and read `box.id` / `box.xyxy` per frame. Decode/encode video with OpenCV (`cv2.VideoCapture` /
`cv2.VideoWriter`); use `vid_stride` to skip frames when real-time isn't required.
