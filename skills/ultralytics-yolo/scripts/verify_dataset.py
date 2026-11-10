#!/usr/bin/env python3
"""Verify an Ultralytics YOLO dataset before training.

Catches the failure modes that waste GPU time: a data.yaml whose paths don't resolve,
labels that don't mirror images, class indices outside the names range, and coordinates
that aren't normalized to [0, 1]. Run this before every train().

Usage:
    python verify_dataset.py path/to/data.yaml
    python verify_dataset.py path/to/data.yaml --splits train val      # subset of splits
    python verify_dataset.py path/to/data.yaml --max-errors 50         # show more errors

Exit code is non-zero if any hard error is found, so it composes in scripts/CI.

Note: this validates label-file tasks (detect / segment / pose / obb). Classification
datasets use a folder-per-class layout with no label files and are reported as such.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff", ".dng", ".mpo", ".pfm"}
EPS = 1e-3  # tolerance for "normalized to [0, 1]" — coords slightly outside are flagged


def load_yaml(yaml_path: Path) -> dict:
    try:
        import yaml  # PyYAML ships with ultralytics
    except ImportError:
        sys.exit("ERROR: PyYAML not installed. Run `pip install pyyaml` (or it comes with ultralytics).")
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        sys.exit(f"ERROR: {yaml_path} did not parse to a mapping.")
    return data


def resolve_root(yaml_path: Path, path_field) -> Path | None:
    """Resolve the dataset 'path' root the way a human would: try absolute, then relative
    to the yaml's directory, then relative to CWD. Ultralytics itself resolves relative
    'path' against its datasets_dir setting, so prefer an absolute 'path' to avoid ambiguity."""
    if path_field is None:
        # No 'path' key: splits are interpreted relative to the yaml's own directory.
        return yaml_path.parent
    p = Path(str(path_field)).expanduser()
    candidates = [p] if p.is_absolute() else [yaml_path.parent / p, Path.cwd() / p, p]
    for c in candidates:
        if c.exists():
            return c.resolve()
    return None


def names_count(data: dict) -> int:
    names = data.get("names")
    if isinstance(names, dict):
        return len(names)
    if isinstance(names, (list, tuple)):
        return len(names)
    nc = data.get("nc")
    return int(nc) if nc is not None else -1


def image_files(images_dir: Path) -> list[Path]:
    return [p for p in images_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTS]


def label_path_for(img: Path) -> Path:
    """Mirror an image path into the labels tree: .../images/... -> .../labels/....txt
    Only the LAST 'images' segment is swapped, matching Ultralytics' resolver."""
    parts = list(img.parts)
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == "images":
            parts[i] = "labels"
            break
    return Path(*parts).with_suffix(".txt")


def check_label_file(lbl: Path, n_classes: int) -> list[str]:
    """Return a list of error strings for one label file (empty list = clean)."""
    errs: list[str] = []
    try:
        lines = lbl.read_text().strip().splitlines()
    except Exception as e:  # noqa: BLE001
        return [f"{lbl}: unreadable ({e})"]
    for ln, raw in enumerate(lines, 1):
        raw = raw.strip()
        if not raw:
            continue
        toks = raw.split()
        if len(toks) < 5:
            errs.append(f"{lbl}:{ln}: expected 'class + >=4 coords', got {len(toks)} token(s)")
            continue
        try:
            vals = [float(t) for t in toks]
        except ValueError:
            errs.append(f"{lbl}:{ln}: non-numeric token in '{raw}'")
            continue
        cls = vals[0]
        if cls != int(cls):
            errs.append(f"{lbl}:{ln}: class index {cls} is not an integer")
        elif n_classes >= 0 and not (0 <= int(cls) < n_classes):
            errs.append(f"{lbl}:{ln}: class index {int(cls)} out of range [0, {n_classes - 1}]")
        coords = vals[1:]
        if len(coords) % 2 != 0 and len(coords) != 4:
            # detect=4; seg/obb/pose come in xy pairs (+optional visibility handled loosely)
            pass  # arity varies by task; don't false-positive, the normalization check below is the guard
        bad = [f"{v:.4g}" for v in coords if v < -EPS or v > 1 + EPS]
        if bad:
            errs.append(f"{lbl}:{ln}: coords not normalized to [0,1]: {', '.join(bad[:6])}")
    return errs


def looks_like_classification(root: Path, split_val) -> bool:
    """Classification datasets are folder-per-class with no labels/ tree."""
    split_dir = root / str(split_val)
    if not split_dir.is_dir():
        return False
    subdirs = [d for d in split_dir.iterdir() if d.is_dir()]
    has_labels_sibling = (root / "labels").exists()
    return bool(subdirs) and not has_labels_sibling and not (split_dir / "..").joinpath("labels").exists()


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify an Ultralytics YOLO dataset.")
    ap.add_argument("data_yaml", type=Path)
    ap.add_argument("--splits", nargs="*", default=["train", "val", "test"])
    ap.add_argument("--max-errors", type=int, default=20)
    args = ap.parse_args()

    if not args.data_yaml.exists():
        print(f"ERROR: {args.data_yaml} not found.")
        return 2

    data = load_yaml(args.data_yaml)
    root = resolve_root(args.data_yaml, data.get("path"))
    n_classes = names_count(data)

    print(f"data.yaml : {args.data_yaml}")
    print(f"root      : {root if root else 'UNRESOLVED'}")
    print(f"classes   : {n_classes if n_classes >= 0 else 'unknown (no names/nc)'}")
    if data.get("kpt_shape"):
        print(f"kpt_shape : {data['kpt_shape']} (pose dataset)")
    print("-" * 60)

    if root is None:
        print("HARD ERROR: dataset 'path' does not resolve. Use an absolute path or check `yolo settings`.")
        return 1

    hard_errors: list[str] = []
    total_imgs = total_labeled = total_backgrounds = 0

    for split in args.splits:
        split_val = data.get(split)
        if split_val is None:
            if split in ("train", "val"):
                print(f"[{split}] MISSING from data.yaml (required)")
                hard_errors.append(f"{split} split missing")
            continue

        if looks_like_classification(root, split_val):
            print(f"[{split}] looks like a CLASSIFICATION layout (folder-per-class, no labels). Skipping label checks.")
            continue

        images_dir = (root / str(split_val)).resolve()
        if not images_dir.exists():
            print(f"[{split}] images dir not found: {images_dir}")
            hard_errors.append(f"{split} images dir missing: {images_dir}")
            continue

        imgs = image_files(images_dir)
        if not imgs:
            print(f"[{split}] 0 images found in {images_dir}")
            hard_errors.append(f"{split} has 0 images")
            continue

        split_errs: list[str] = []
        labeled = backgrounds = 0
        for img in imgs:
            lbl = label_path_for(img)
            if not lbl.exists():
                backgrounds += 1  # empty/missing label = valid background image
                continue
            if lbl.stat().st_size == 0:
                backgrounds += 1
                continue
            file_errs = check_label_file(lbl, n_classes)
            if file_errs:
                split_errs.extend(file_errs)
            else:
                labeled += 1

        total_imgs += len(imgs)
        total_labeled += labeled
        total_backgrounds += backgrounds
        status = "OK" if not split_errs else f"{len(split_errs)} ERROR(S)"
        print(f"[{split}] {len(imgs)} images | {labeled} labeled | {backgrounds} background | {status}")
        for e in split_errs[: args.max_errors]:
            print(f"    - {e}")
        if len(split_errs) > args.max_errors:
            print(f"    ... and {len(split_errs) - args.max_errors} more (raise --max-errors to see)")
        hard_errors.extend(split_errs)

    print("-" * 60)
    print(f"TOT:  {total_imgs} images | {total_labeled} labeled | {total_backgrounds} background")
    if hard_errors:
        print(f"RESULT: FAIL — {len(hard_errors)} issue(s). Fix these before training.")
        return 1
    print("RESULT: PASS — dataset looks structurally sound. (Still spot-check labels visually, e.g. FiftyOne.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
