# Export & Edge Deployment

Getting a trained model off the GPU and onto a phone, embedded board, or production server. This is where
"it works in Python" and "it works on the device" diverge — pick the format for the *target*, quantize
deliberately, and respect YOLO26's NMS-free design.

- [The export call](#the-export-call)
- [Format selection by target](#format-selection-by-target)
- [YOLO26 is NMS-free — what changes](#yolo26-is-nms-free--what-changes)
- [Quantization](#quantization)
- [CoreML (iOS / macOS)](#coreml-ios--macos)
- [TFLite (Android / embedded)](#tflite-android--embedded)
- [ONNX & ONNX Runtime (cross-platform / mobile)](#onnx--onnx-runtime-crossplatform--mobile)
- [Server / high-throughput](#server--highthroughput)
- [On-device post-processing](#on-device-post-processing)
- [Known edge gotchas](#known-edge-gotchas)

## The export call

```python
from ultralytics import YOLO
model = YOLO("runs/detect/exp1/weights/best.pt")
model.export(format="coreml", imgsz=640, int8=True, nms=False)
```
```bash
yolo export model=best.pt format=coreml imgsz=640 int8=True
```

Export writes the converted artifact next to the `.pt`. Some formats need extra deps — install the matching
pip extra (e.g. `pip install "ultralytics[export-coreml]"`, `[export-tensorflow]`, `[export-executorch]`).
**Lock `imgsz` at export** to the resolution you'll feed on-device; a mismatch silently degrades accuracy.

## Format selection by target

Choose by where the model will run, not by familiarity:

| Target | Format | Notes |
|--------|--------|-------|
| **iOS / macOS** | `coreml` → `.mlpackage` | Neural Engine / GPU acceleration; native Swift integration |
| **Android** | `tflite` | NNAPI/GPU delegate; `int8` for size/speed |
| **Cross-platform mobile / many runtimes** | `onnx` | ONNX Runtime (incl. mobile builds), broad ecosystem |
| **Google Coral Edge TPU** | `edgetpu` | requires `int8`; compile for the TPU |
| **NVIDIA Jetson / server GPU** | `engine` (TensorRT) | fastest on NVIDIA; build on the *target* GPU |
| **Intel CPU / iGPU / VPU** | `openvino` | strong CPU/edge perf on Intel hardware |
| **Raspberry Pi / ARM CPU** | `onnx` or `tflite` | NCNN historically best but see gotchas |
| **React Native app** | `onnx` (onnxruntime-react-native) or platform-native (`coreml`+`tflite`) | one ONNX vs. two native artifacts — pick per perf needs |

Other supported formats include `torchscript`, `saved_model`/`pb` (TensorFlow), `tfjs`, `paddle`, `mnn`,
`ncnn`, `executorch` (PyTorch Edge), and `imx`/`rknn` for specific SoCs. When unsure, ask the user the exact
device/OS and runtime before exporting — the wrong format is a silent time sink.

## YOLO26 is NMS-free — what changes

YOLO26 detection is **end-to-end**: the model emits final, deduplicated boxes directly, with **no
non-max-suppression** stage. This is the headline reason it's edge-friendly — there's no NMS to reimplement
in Swift/Kotlin/C++, and the exported graph is simpler and faster.

Practical consequences:
- **Don't add NMS on-device for YOLO26.** Feed the raw model outputs straight through; an extra NMS pass
  will *delete valid boxes* or do nothing useful.
- The `iou` (NMS IoU) argument has **no effect** on YOLO26 inference. `conf` thresholding still applies.
- For **older generations** (YOLO11/v8/etc.), the model *does* need NMS. When the runtime can't easily run
  NMS itself, export with `nms=True` to embed it in the CoreML/TFLite/ONNX graph. If you set `nms=True` on a
  YOLO26 model it's redundant — leave it `False`.

When you hand off a YOLO26 export, tell the integrating engineer explicitly: "outputs are final detections,
no NMS required."

## Quantization

Trades a little accuracy for big size/latency wins — usually worth it on edge.

- `half=True` → FP16. ~2× smaller, near-lossless, GPU/Neural-Engine friendly. Safe default for mobile.
- `int8=True` → INT8. ~4× smaller, fastest, but **needs calibration data** to stay accurate. Provide a
  representative sample via `data=` (the dataset yaml or a folder); Ultralytics runs calibration over it.
  Required for `edgetpu`. Always re-run `model.val()` on the exported INT8 model — expect a small mAP drop
  and confirm it's acceptable before shipping.
- Don't INT8 blindly on tasks sensitive to fine detail (small-object detection, precise segmentation)
  without checking the validation delta.

## CoreML (iOS / macOS)

```python
model.export(format="coreml", imgsz=640, half=True, nms=False)  # -> best.mlpackage
```
- Needs `coremltools` (`ultralytics[export-coreml]`); conversion is most reliable **on macOS**.
- Drop the `.mlpackage` into Xcode; it runs on the Neural Engine/GPU via the Vision/CoreML APIs.
- `int8=True` for max compression; validate the accuracy hit.
- For YOLO26, leave `nms=False` and consume outputs directly in Swift (see [post-processing](#on-device-post-processing)).

## TFLite (Android / embedded)

```python
model.export(format="tflite", imgsz=640, int8=True, data="data.yaml")  # int8 needs calibration data
```
- Use the GPU or NNAPI delegate in the Android app for acceleration.
- `format="edgetpu"` (requires `int8`) for Coral; compile the resulting model for the Edge TPU.
- Verify input tensor layout/normalization in your Android preprocessing matches what YOLO expects
  (RGB, 0–1, letterboxed to `imgsz`).

## ONNX & ONNX Runtime (cross-platform / mobile)

```python
model.export(format="onnx", imgsz=640, opset=12, dynamic=False, simplify=True)
```
- The most portable option: runs via ONNX Runtime on server, desktop, Android, iOS, and **React Native**
  (`onnxruntime-react-native`).
- `dynamic=True` allows variable input sizes (more flexible, sometimes slower); keep `False` + fixed `imgsz`
  for the fastest, most predictable mobile path.
- `simplify=True` folds constants for a leaner graph.
- Great default when you want **one artifact** across both mobile platforms instead of maintaining separate
  CoreML + TFLite builds.

## Server / high-throughput

- **TensorRT** (`format="engine"`): fastest on NVIDIA. **Build the engine on the same GPU arch** it will run
  on — engines aren't portable across GPU generations. `half=True`/`int8=True` supported.
- **OpenVINO**: best on Intel CPUs/iGPUs/VPUs.
- For serving at scale, export to ONNX/TensorRT and front it with **Triton Inference Server** (Ultralytics
  documents a Triton path) rather than running the Python `predict` loop in production.

## On-device post-processing

Whatever the format, the model outputs **tensors**, not drawn boxes. Native code must:
1. **Preprocess** identically to training: resize+letterbox to `imgsz`, BGR→RGB if needed, scale to 0–1
   (or the quantized input scale), CHW layout.
2. **Run** the model.
3. **Postprocess**: parse output tensor → boxes/scores/classes; **scale coordinates back** from `imgsz`
   space to the original image (undo the letterbox padding). For YOLO26: take outputs as-is (no NMS). For
   older gens without embedded NMS: run NMS here.

Coordinate scaling and letterbox-undo are the most common source of "boxes are offset/wrong size" bugs in
mobile integrations — get the preprocessing and the inverse transform exactly symmetric.

## Known edge gotchas

- **NCNN disabled on ARM64.** Although NCNN historically gave the best Raspberry Pi performance, it is
  currently disabled for ARM64 in Ultralytics (`AutoBackend` raises `NotImplementedError`). On Pi 5 / ARM64,
  **export to ONNX or TFLite instead.** Don't promise NCNN on those boards without checking the installed
  version first (`yolo checks`, `python -c "import ultralytics; print(ultralytics.__version__)"`).
- **TensorRT engines aren't portable** — rebuild per target GPU.
- **CoreML conversion off-macOS** can be flaky — prefer a Mac (or CI mac runner) for `.mlpackage` builds.
- **INT8 without calibration data** produces a model with badly degraded accuracy — always pass `data=`.
- **`imgsz` mismatch** between export and on-device input quietly tanks accuracy.
- **Forgetting YOLO26 is NMS-free** → duplicate or dropped boxes after someone bolts on an NMS step.
