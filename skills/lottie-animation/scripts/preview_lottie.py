#!/usr/bin/env python3
"""
preview_lottie.py — Render a Lottie animation to a static contact sheet of
frames and (optionally) an animated GIF for visual QA.

Pipeline:
  Lottie JSON → python-lottie parse → SVG per frame → cairosvg PNG → PIL composite.

If the rendering pipeline isn't available (python-lottie or cairosvg missing),
falls back to printing a structural summary so you can still spot mistakes.

Usage:
    python preview_lottie.py path/to/animation.json
    python preview_lottie.py path/to/animation.json --frames 12 --gif
    python preview_lottie.py path/to/animation.json --bg "#0a0a14" --width 300

Outputs (next to input file, unless --output-dir is given):
  <stem>_frames.png    Contact sheet of N evenly-spaced frames
  <stem>_preview.gif   Animated preview, played at the animation's fps (if --gif)
"""

from __future__ import annotations
import argparse
import json
import sys
from io import StringIO, BytesIO
from pathlib import Path


def _check_renderer_available() -> tuple[bool, str]:
    """Return (available, missing_packages_message)."""
    missing = []
    try:
        import lottie  # noqa: F401
    except ImportError:
        missing.append("lottie (python-lottie)")
    try:
        import cairosvg  # noqa: F401
    except ImportError:
        missing.append("cairosvg")
    try:
        import PIL  # noqa: F401
    except ImportError:
        missing.append("Pillow")
    if missing:
        return False, ", ".join(missing)
    return True, ""


def structural_summary(data: dict) -> str:
    """Fallback: report on Lottie structure without rendering."""
    lines = []
    lines.append(f"Composition: {data.get('w', '?')} × {data.get('h', '?')} "
                 f"@ {data.get('fr', '?')} fps")
    lines.append(f"Duration: frames {data.get('ip', '?')} → {data.get('op', '?')} "
                 f"({(data.get('op', 0) - data.get('ip', 0)) / max(data.get('fr', 1), 1):.2f}s)")
    layers = data.get("layers", [])
    lines.append(f"Layers: {len(layers)}")
    LAYER_TYPES = {0: "precomp", 1: "solid", 2: "image", 3: "null", 4: "shape", 5: "text"}
    for i, layer in enumerate(layers):
        ty_name = LAYER_TYPES.get(layer.get("ty"), f"unknown({layer.get('ty')})")
        n_shapes = len(layer.get("shapes", []))
        ks = layer.get("ks", {})

        animated = []
        for prop_name, prop in ks.items():
            if isinstance(prop, dict) and prop.get("a") == 1:
                kfs = prop.get("k", [])
                animated.append(f"{prop_name}({len(kfs)}kf)")
        anim_str = f" anim:[{','.join(animated)}]" if animated else ""

        lines.append(
            f"  [{i}] {layer.get('nm', '?')} ({ty_name}) — "
            f"frames {layer.get('ip', '?')}→{layer.get('op', '?')}, "
            f"shapes:{n_shapes}{anim_str}"
        )
    return "\n".join(lines)


def render_frames(data: dict, frame_indices: list[int], width: int) -> list:
    """Render a list of frames to PIL Image objects."""
    from lottie.objects.animation import Animation
    from lottie.exporters.svg import export_svg
    import cairosvg
    from PIL import Image

    anim = Animation.load(data)
    images = []
    for f in frame_indices:
        svg_buf = StringIO()
        export_svg(anim, svg_buf, frame=f)
        svg = svg_buf.getvalue()
        png_bytes = cairosvg.svg2png(
            bytestring=svg.encode("utf-8"),
            output_width=width,
        )
        img = Image.open(BytesIO(png_bytes))
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        images.append(img)
    return images


def build_contact_sheet(images: list, bg_color: tuple, label_frames: list[int] = None):
    """Compose a contact sheet (grid) of rendered frames."""
    from PIL import Image, ImageDraw, ImageFont

    n = len(images)
    if n == 0:
        raise ValueError("No images to compose")
    cols = min(4, n)
    rows = (n + cols - 1) // cols
    cell_w, cell_h = images[0].size
    label_h = 24 if label_frames else 0
    sheet_w = cell_w * cols
    sheet_h = (cell_h + label_h) * rows

    sheet = Image.new("RGBA", (sheet_w, sheet_h), bg_color)
    draw = ImageDraw.Draw(sheet)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for i, img in enumerate(images):
        r, c = divmod(i, cols)
        x = c * cell_w
        y = r * (cell_h + label_h)
        sheet.paste(img, (x, y), img)
        if label_frames and font is not None:
            label = f"frame {label_frames[i]}"
            draw.text((x + 6, y + cell_h + 4), label, fill=(180, 180, 200, 255), font=font)
    return sheet


def render_gif(data: dict, output_path: Path, width: int, max_frames: int = 60) -> None:
    """Render an animated GIF preview. Samples up to max_frames evenly from
    the animation, with delay matching the animation's fps."""
    from lottie.objects.animation import Animation
    from lottie.exporters.svg import export_svg
    import cairosvg
    from PIL import Image

    anim = Animation.load(data)
    duration = int(anim.out_point - anim.in_point)
    fps = float(anim.frame_rate)

    step = max(1, duration // max_frames)
    frame_indices = list(range(int(anim.in_point), int(anim.out_point) + 1, step))[:max_frames]

    frames = []
    for f in frame_indices:
        svg_buf = StringIO()
        export_svg(anim, svg_buf, frame=f)
        png_bytes = cairosvg.svg2png(
            bytestring=svg_buf.getvalue().encode("utf-8"),
            output_width=width,
        )
        img = Image.open(BytesIO(png_bytes))
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        frames.append(img)

    if not frames:
        raise ValueError("No frames to encode")

    # GIF frame duration in ms — accounts for the step subsampling
    frame_duration_ms = max(20, int(1000 * step / fps))
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=frame_duration_ms,
        loop=0,
        disposal=2,
        optimize=False,
    )


def parse_color(s: str) -> tuple:
    """Parse a hex color string to an RGBA tuple."""
    s = s.lstrip("#")
    if len(s) == 6:
        r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
        return (r, g, b, 255)
    if len(s) == 8:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), int(s[6:8], 16))
    raise ValueError(f"Invalid hex color: {s}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Lottie animation preview.")
    parser.add_argument("file", help="Path to Lottie JSON file")
    parser.add_argument("--frames", type=int, default=8, help="Number of contact-sheet frames (default 8)")
    parser.add_argument("--width", type=int, default=200, help="Per-frame render width in pixels (default 200)")
    parser.add_argument("--bg", default="#101018", help="Contact sheet background color (default dark)")
    parser.add_argument("--gif", action="store_true", help="Also render an animated GIF preview")
    parser.add_argument("--gif-max-frames", type=int, default=60, help="Maximum frames in GIF (default 60)")
    parser.add_argument("--output-dir", help="Output directory (default: same dir as input)")
    parser.add_argument("--structure-only", action="store_true", help="Skip rendering, only print structure")
    args = parser.parse_args()

    input_path = Path(args.file)
    if not input_path.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1

    try:
        with open(input_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON: {e}", file=sys.stderr)
        return 1

    # Always print the structural summary at the top — useful even when rendering works
    print(f"=== {input_path.name} ===")
    print(structural_summary(data))
    print()

    if args.structure_only:
        return 0

    available, missing_msg = _check_renderer_available()
    if not available:
        print(f"Renderer unavailable — missing packages: {missing_msg}")
        print("Install with: pip install lottie cairosvg Pillow")
        print("(Structure summary above is the available output.)")
        return 0

    output_dir = Path(args.output_dir) if args.output_dir else input_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem
    bg = parse_color(args.bg)

    # Compute evenly-spaced frame indices across the composition
    ip = int(data.get("ip", 0))
    op = int(data.get("op", 60))
    n = max(2, args.frames)
    if n == 1:
        frame_indices = [ip]
    else:
        frame_indices = [ip + i * (op - ip) // (n - 1) for i in range(n)]

    try:
        images = render_frames(data, frame_indices, args.width)
    except Exception as e:
        print(f"Render error: {type(e).__name__}: {e}", file=sys.stderr)
        print("(Structure summary above is the available output.)")
        return 1

    sheet = build_contact_sheet(images, bg, label_frames=frame_indices)
    sheet_path = output_dir / f"{stem}_frames.png"
    sheet.save(sheet_path)
    print(f"Contact sheet: {sheet_path} ({sheet.size[0]}×{sheet.size[1]}, {len(images)} frames)")

    if args.gif:
        gif_path = output_dir / f"{stem}_preview.gif"
        try:
            render_gif(data, gif_path, args.width, max_frames=args.gif_max_frames)
            print(f"Animated preview: {gif_path}")
        except Exception as e:
            print(f"GIF render error: {type(e).__name__}: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
