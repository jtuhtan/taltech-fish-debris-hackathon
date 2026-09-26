#!/usr/bin/env python3
"""Render the "Fish or debris?" promo video and README GIF from training frames.

Needs the released dataset (images/train and annotations/instances_train.json),
Pillow, NumPy, and ffmpeg. Only training-split frames and their released
fish boxes are used.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
W, H = 1920, 1080
FADE = 0.35

NAVY = (3, 44, 68)
BLUE = (7, 91, 131)
CYAN = (8, 168, 211)
CYAN_LIGHT = (99, 223, 243)
GREEN = (105, 220, 98)
AMBER = (255, 184, 77)
WHITE = (255, 255, 255)

# (fish frame, no-fish frame, side of the fish, what is visible in the no-fish frame)
ROUNDS = [
    ("f-218ad4d7cd1d", "f-961b6a879ccc", "right", "dark drifting clumps"),
    ("f-c76e4c313c73", "f-2b06d6762820", "left", "leaf-like material"),
    ("f-a3836e0ae8c1", "f-10e8054729b0", "right", "twig-like debris"),
]
SCHOOL = "f-b8aa32721eb9"
NIGHT = "f-7286ed7a14c7"
FONT_DIRS = [
    Path("/mnt/c/Windows/Fonts"),
    Path("C:/Windows/Fonts"),
    Path("/Library/Fonts"),
    Path("/usr/share/fonts/truetype/msttcorefonts"),
    Path("/usr/share/fonts/truetype/dejavu"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", required=True, type=Path, help="Folder with images/ and annotations/")
    parser.add_argument("--mp4", type=Path, default=REPO_ROOT / "docs" / "promo" / "fish-or-debris.mp4")
    parser.add_argument("--gif", type=Path, default=REPO_ROOT / "docs" / "promo" / "fish-or-debris.gif")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--gif-width", type=int, default=800)
    parser.add_argument("--gif-fps", type=int, default=12)
    parser.add_argument("--preview", type=float, nargs="*", help="Only save PNG stills at these times (s)")
    return parser.parse_args()


@lru_cache(maxsize=None)
def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    names = ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"] if bold else ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"]
    for directory in FONT_DIRS:
        for name in names:
            if (directory / name).exists():
                return ImageFont.truetype(str(directory / name), size)
    return ImageFont.load_default(size)


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def phase(t: float, start: float, duration: float) -> float:
    return clamp((t - start) / duration)


def ease(x: float) -> float:
    return 1 - (1 - clamp(x)) ** 3


def ease_back(x: float) -> float:
    x = clamp(x)
    return 1 + 2.7 * (x - 1) ** 3 + 1.7 * (x - 1) ** 2


def rgba(color: tuple[int, int, int], alpha: float) -> tuple[int, int, int, int]:
    return (*color, round(255 * clamp(alpha)))


def background() -> Image.Image:
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    g = (x / W + y / H) / 2
    rgb = np.zeros((H, W, 3), np.float32)
    for (p0, c0), (p1, c1) in [((0.0, NAVY), (0.55, BLUE)), ((0.55, BLUE), (1.0, CYAN))]:
        mask = (g >= p0) & (g <= p1)
        f = ((g - p0) / (p1 - p0))[..., None]
        rgb[mask] = (np.array(c0) * (1 - f) + np.array(c1) * f)[mask]
    rgb = rgb * 0.62 + np.array(NAVY) * 0.38
    distance = np.hypot(x - 0.75 * W, y - 0.2 * H) / (0.75 * math.hypot(W, H))
    glow = np.clip(1 - distance, 0, 1)[..., None] * 0.22
    rgb = rgb * (1 - glow) + np.array((53, 212, 242)) * glow
    return Image.fromarray(rgb.clip(0, 255).astype(np.uint8), "RGB").convert("RGBA")


def text(draw: ImageDraw.ImageDraw, xy: tuple[float, float], value: str, size: int,
         fill: tuple[int, int, int] = WHITE, alpha: float = 1.0, bold: bool = True,
         anchor: str = "la", tracking: float = 0) -> float:
    face = font(size, bold)
    if not tracking:
        draw.text(xy, value, font=face, fill=rgba(fill, alpha), anchor=anchor)
        return face.getlength(value)
    widths = [face.getlength(char) for char in value]
    total = sum(widths) + tracking * (len(value) - 1)
    x = xy[0] - (total / 2 if anchor[0] == "m" else total if anchor[0] == "r" else 0)
    for char, width in zip(value, widths):
        draw.text((x, xy[1]), char, font=face, fill=rgba(fill, alpha), anchor="l" + anchor[1])
        x += width + tracking
    return total


def pill(draw: ImageDraw.ImageDraw, center: tuple[float, float], label: str, size: int,
         color: tuple[int, int, int], alpha: float, icon: str | None = None) -> None:
    face = font(size)
    icon_w = size * 1.1 if icon else 0
    width = face.getlength(label) + icon_w + size * 1.4
    height = size * 1.9
    x0, y0 = center[0] - width / 2, center[1] - height / 2
    draw.rounded_rectangle([x0, y0, x0 + width, y0 + height], radius=height / 2, fill=rgba(color, alpha))
    tx = x0 + size * 0.7
    if icon:
        cx, cy, r = tx + size * 0.4, center[1], size * 0.36
        stroke = max(3, size // 7)
        if icon == "check":
            draw.line([(cx - r, cy), (cx - r * 0.25, cy + r * 0.75), (cx + r, cy - r * 0.8)], fill=rgba(NAVY, alpha), width=stroke, joint="curve")
        else:
            draw.line([(cx - r, cy - r), (cx + r, cy + r)], fill=rgba(NAVY, alpha), width=stroke)
            draw.line([(cx - r, cy + r), (cx + r, cy - r)], fill=rgba(NAVY, alpha), width=stroke)
        tx += icon_w
    draw.text((tx, center[1]), label, font=face, fill=rgba(NAVY, alpha), anchor="lm")


@dataclass
class Panel:
    image: Image.Image
    shadow: Image.Image
    x: int
    y: int
    scale: float
    boxes: list[list[float]]

    @property
    def bottom(self) -> int:
        return self.y + self.image.height

    def box_rect(self, box: list[float], grow: float = 1.0, dy: float = 0, pad: float = 5) -> list[float]:
        x, y, w, h = box
        cx = self.x + (x + w / 2) * self.scale
        cy = self.y + dy + (y + h / 2) * self.scale
        hw, hh = w * self.scale / 2 * grow + pad, h * self.scale / 2 * grow + pad
        return [cx - hw, cy - hh, cx + hw, cy + hh]


def make_panel(image: Image.Image, boxes: list[list[float]], cx: float, cy: float, max_w: float, max_h: float) -> Panel:
    scale = min(max_w / image.width, max_h / image.height)
    size = (round(image.width * scale), round(image.height * scale))
    resized = image.resize(size, Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=18, fill=255)
    resized.putalpha(mask)
    shadow = Image.new("RGBA", (size[0] + 80, size[1] + 80), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([40, 52, size[0] + 40, size[1] + 52], radius=22, fill=(0, 10, 20, 140))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    return Panel(resized, shadow, round(cx - size[0] / 2), round(cy - size[1] / 2), scale, boxes)


def paste(canvas: Image.Image, panel: Panel, alpha: float = 1.0, dy: float = 0, dim: float = 0.0) -> None:
    if alpha <= 0:
        return
    image = panel.image
    if dim > 0:
        shade = Image.new("RGBA", image.size, (2, 20, 32, round(255 * dim * 0.6)))
        image = Image.alpha_composite(image, shade)
        image.putalpha(panel.image.getchannel("A"))
    if alpha < 1:
        image = image.copy()
        image.putalpha(image.getchannel("A").point(lambda v: round(v * alpha)))
        shadow = panel.shadow.copy()
        shadow.putalpha(shadow.getchannel("A").point(lambda v: round(v * alpha)))
    else:
        shadow = panel.shadow
    canvas.alpha_composite(shadow, (panel.x - 40, round(panel.y + dy) - 40))
    canvas.alpha_composite(image, (panel.x, round(panel.y + dy)))


def draw_boxes(canvas: Image.Image, panel: Panel, progress: list[float], dy: float = 0, label: bool = False) -> None:
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    crisp = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    glow_draw, crisp_draw = ImageDraw.Draw(glow), ImageDraw.Draw(crisp)
    for box, p in zip(panel.boxes, progress):
        if p <= 0:
            continue
        rect = panel.box_rect(box, ease_back(p), dy)
        glow_draw.rounded_rectangle(rect, radius=8, outline=rgba(GREEN, 0.75 * clamp(p * 2)), width=12)
        crisp_draw.rounded_rectangle(rect, radius=8, outline=rgba(GREEN, clamp(p * 2)), width=4)
        if label and p > 0.5:
            alpha = clamp((p - 0.5) * 2)
            face = font(24)
            width = face.getlength("fish") + 24
            lx, ly = rect[0], rect[1] - 38 if rect[1] - 38 > panel.y + dy else rect[3] + 6
            crisp_draw.rounded_rectangle([lx, ly, lx + width, ly + 32], radius=10, fill=rgba(GREEN, alpha))
            crisp_draw.text((lx + 12, ly + 16), "fish", font=face, fill=rgba(NAVY, alpha), anchor="lm")
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(7)))
    canvas.alpha_composite(crisp)


def header(draw: ImageDraw.ImageDraw, eyebrow: str, title: str, t: float) -> None:
    a = ease(phase(t, 0.0, 0.4))
    text(draw, (W / 2, 78 - 12 * (1 - a)), eyebrow, 26, CYAN_LIGHT, a, anchor="ms", tracking=5)
    text(draw, (W / 2, 146 - 12 * (1 - a)), title, 60, WHITE, a, anchor="ms")


def footer(draw: ImageDraw.ImageDraw, alpha: float = 1.0) -> None:
    text(draw, (60, H - 40), "Training-split frames · human-annotated fish boxes", 24, CYAN_LIGHT, 0.85 * alpha, bold=False, anchor="ls")
    text(draw, (W - 60, H - 40), "EIT WATER HACKATHON · MUNICH 2026", 22, CYAN_LIGHT, 0.85 * alpha, anchor="rs", tracking=3)


def countdown(draw: ImageDraw.ImageDraw, t: float, start: float, step: float, alpha: float) -> None:
    cx, cy, r = W - 170, 112, 46
    elapsed = (t - start) / (3 * step)
    if alpha <= 0 or elapsed < 0:
        return
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=rgba(WHITE, 0.25 * alpha), width=6)
    remaining = 1 - clamp(elapsed)
    if remaining > 0:
        draw.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * remaining, fill=rgba(CYAN_LIGHT, alpha), width=6)
    number = 3 - min(2, int((t - start) / step))
    text(draw, (cx, cy), str(number), 44, WHITE, alpha, anchor="mm")


class Video:
    def __init__(self, dataset: Path) -> None:
        coco = json.loads((dataset / "annotations" / "instances_train.json").read_text(encoding="utf-8"))
        boxes: dict[int, list[list[float]]] = {}
        for annotation in coco["annotations"]:
            boxes.setdefault(annotation["image_id"], []).append(annotation["bbox"])
        self.frames: dict[str, tuple[Image.Image, list[list[float]]]] = {}
        wanted = {frame for pair in ROUNDS for frame in pair[:2]} | {SCHOOL, NIGHT}
        for image in coco["images"]:
            frame_id = Path(image["file_name"]).stem
            if frame_id in wanted:
                pixels = Image.open(dataset / "images" / "train" / image["file_name"]).convert("RGB")
                self.frames[frame_id] = (pixels, boxes.get(image["id"], []))
        missing = wanted - set(self.frames)
        if missing:
            raise SystemExit(f"Training frames not found: {', '.join(sorted(missing))}")
        self.background = background()
        self.logos = []
        for name, height in (("iamhydro.png", 92), ("taltech.png", 130)):
            logo = Image.open(REPO_ROOT / "docs" / "brand" / name).convert("RGBA")
            logo = logo.crop(logo.getchannel("A").getbbox())
            self.logos.append(logo.resize((round(logo.width * height / logo.height), height), Image.LANCZOS))
        self.round_panels = [self.layout_round(*spec) for spec in ROUNDS]
        self.school = make_panel(*self.frames[SCHOOL], W / 2, 585, 1560, 760)
        self.night = make_panel(*self.frames[NIGHT], W / 2, 585, 1200, 760)
        self.scenes = [
            (3.0, self.intro),
            (4.8, lambda t: self.quiz(t, 0, 0.6)),
            (4.3, lambda t: self.quiz(t, 1, 0.5)),
            (4.3, lambda t: self.quiz(t, 2, 0.5)),
            (4.0, lambda t: self.showcase(t, self.school, "ONE FRAME", "Sometimes it's a whole school")),
            (3.4, lambda t: self.showcase(t, self.night, "DAWN · DAY · DUSK · NIGHT", "Fish don't stop at sunset")),
            (5.8, self.outro),
        ]
        self.duration = sum(duration for duration, _ in self.scenes)

    def layout_round(self, fish: str, empty: str, side: str, _: str) -> tuple[Panel, Panel]:
        image = self.frames[fish][0]
        gap, max_w, max_h, cy = 64, 860, 690, 560
        scale = min(max_w / image.width, max_h / image.height)
        half = image.width * scale / 2 + gap / 2
        left, right = W / 2 - half, W / 2 + half
        fish_x, empty_x = (right, left) if side == "right" else (left, right)
        return (make_panel(*self.frames[fish], fish_x, cy, max_w, max_h),
                make_panel(*self.frames[empty], empty_x, cy, max_w, max_h))

    def canvas(self) -> tuple[Image.Image, Image.Image, ImageDraw.ImageDraw]:
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        return self.background.copy(), overlay, ImageDraw.Draw(overlay)

    def intro(self, t: float) -> Image.Image:
        image, overlay, draw = self.canvas()
        a1, a2, a3 = (ease(phase(t, start, 0.6)) for start in (0.1, 0.35, 0.8))
        text(draw, (W / 2, 360 - 20 * (1 - a1)), "EIT WATER HACKATHON · MUNICH 2026", 30, CYAN_LIGHT, a1, anchor="ms", tracking=6)
        text(draw, (W / 2, 520 - 20 * (1 - a2)), "Fish or debris?", 150, WHITE, a2, anchor="ms")
        wave = ease(phase(t, 0.6, 1.2))
        points = [(W / 2 - 420 + i * 8, 590 + 14 * math.sin(i / 7)) for i in range(int(106 * wave))]
        if len(points) > 1:
            draw.line(points, fill=rgba(GREEN, 0.9), width=7, joint="curve")
        text(draw, (W / 2, 700 - 16 * (1 - a3)), "Leaves, twigs, and sediment can trigger thousands of", 40, WHITE, 0.92 * a3, bold=False, anchor="ms")
        text(draw, (W / 2, 756 - 16 * (1 - a3)), "false alarms per camera station, per day.", 40, WHITE, 0.92 * a3, bold=False, anchor="ms")
        image.alpha_composite(overlay)
        return image

    def quiz(self, t: float, number: int, step: float) -> Image.Image:
        image, overlay, draw = self.canvas()
        fish, empty = self.round_panels[number]
        visible = ROUNDS[number][3]
        start, reveal = 0.5, 0.5 + 3 * step
        header(draw, f"ROUND {number + 1} OF 3", "Which frame has a fish?", t)
        slide = ease(phase(t, 0.05, 0.5))
        dy = 50 * (1 - slide)
        dim = ease(phase(t, reveal, 0.4))
        paste(image, fish, slide, dy)
        paste(image, empty, slide, dy, dim)
        for index, panel in enumerate(sorted((fish, empty), key=lambda p: p.x)):
            letter_alpha = slide * (1 - ease(phase(t, reveal, 0.3)))
            pill(draw, (panel.x + 44, panel.y + dy + 40), "AB"[index], 30, CYAN_LIGHT, letter_alpha)
        countdown(draw, t, start, step, slide * (1 - ease(phase(t, reveal, 0.25))))
        draw_boxes(image, fish, [phase(t, reveal, 0.45)] * len(fish.boxes), dy, label=True)
        verdict = ease(phase(t, reveal + 0.15, 0.4))
        pill(draw, (fish.x + fish.image.width / 2, fish.bottom + 52 + 20 * (1 - verdict)), "FISH", 34, GREEN, verdict, "check")
        pill(draw, (empty.x + empty.image.width / 2, empty.bottom + 52 + 20 * (1 - verdict)), f"NO FISH · {visible}", 34, AMBER, verdict, "cross")
        footer(draw, slide)
        image.alpha_composite(overlay)
        return image

    def showcase(self, t: float, panel: Panel, eyebrow: str, title: str) -> Image.Image:
        image, overlay, draw = self.canvas()
        header(draw, eyebrow, title, t)
        slide = ease(phase(t, 0.05, 0.5))
        dy = 40 * (1 - slide)
        paste(image, panel, slide, dy)
        order = sorted(range(len(panel.boxes)), key=lambda i: panel.boxes[i][0] + panel.boxes[i][1] * 0.3)
        spacing = min(0.14, 1.6 / max(1, len(order)))
        progress = [0.0] * len(order)
        for rank, index in enumerate(order):
            progress[index] = phase(t, 0.6 + rank * spacing, 0.35)
        draw_boxes(image, panel, progress, dy)
        count = sum(1 for p in progress if p > 0.3)
        if count:
            pill(draw, (W - 190, 112), f"{count} fish", 34, GREEN, ease(phase(t, 0.6, 0.3)), "check")
        footer(draw, slide)
        image.alpha_composite(overlay)
        return image

    def outro(self, t: float) -> Image.Image:
        image, overlay, draw = self.canvas()
        a = [ease(phase(t, 0.1 + i * 0.12, 0.5)) for i in range(10)]
        text(draw, (W / 2, 150), "I AM HYDRO × TALTECH CHALLENGE", 28, CYAN_LIGHT, a[0], anchor="ms", tracking=6)
        text(draw, (W / 2, 246 - 14 * (1 - a[1])), "Can your AI find the fish", 76, WHITE, a[1], anchor="ms")
        text(draw, (W / 2, 336 - 14 * (1 - a[2])), "without chasing every leaf?", 76, CYAN_LIGHT, a[2], anchor="ms")
        stats = [("1,200", "images"), ("1,291", "fish boxes"), ("300", "hard negatives"), ("4", "light conditions")]
        card_w, gap = 330, 30
        x0 = W / 2 - (len(stats) * card_w + (len(stats) - 1) * gap) / 2
        for i, (value, label) in enumerate(stats):
            alpha, x = a[3 + i], x0 + i * (card_w + gap)
            y = 420 + 20 * (1 - alpha)
            draw.rounded_rectangle([x, y, x + card_w, y + 150], radius=22, fill=(255, 255, 255, round(34 * alpha)), outline=rgba(CYAN_LIGHT, 0.5 * alpha), width=2)
            text(draw, (x + card_w / 2, y + 82), value, 64, WHITE, alpha, anchor="ms")
            text(draw, (x + card_w / 2, y + 124), label, 28, CYAN_LIGHT, alpha, bold=False, anchor="ms")
        cta = a[7]
        pill(draw, (W / 2, 668 + 16 * (1 - cta)), "Join the fish-vs-debris challenge", 40, GREEN, cta)
        text(draw, (W / 2, 772), "github.com/jtuhtan/taltech-fish-debris-hackathon", 32, WHITE, a[8], bold=False, anchor="ms")
        logo_alpha, logo_gap, padding = a[9], 80, 64
        card_w = sum(logo.width for logo in self.logos) + logo_gap + 2 * padding
        card = [W / 2 - card_w / 2, 830, W / 2 + card_w / 2, 990]
        if logo_alpha > 0:
            draw.rounded_rectangle(card, radius=26, fill=(255, 255, 255, round(245 * logo_alpha)))
        image.alpha_composite(overlay)
        x = card[0] + padding
        for logo in self.logos:
            if logo_alpha > 0:
                faded = logo.copy()
                faded.putalpha(logo.getchannel("A").point(lambda v: round(v * logo_alpha)))
                image.alpha_composite(faded, (round(x), round((card[1] + card[3] - logo.height) / 2)))
            x += logo.width + logo_gap
        return image

    def frame(self, t: float) -> Image.Image:
        start = 0.0
        for index, (duration, scene) in enumerate(self.scenes):
            if t < start + duration or index == len(self.scenes) - 1:
                image = scene(t - start)
                if index + 1 < len(self.scenes) and t > start + duration - FADE:
                    mix = (t - (start + duration - FADE)) / FADE
                    image = Image.blend(image, self.scenes[index + 1][1](0.0), ease(mix))
                elif index == len(self.scenes) - 1 and t > start + duration - FADE:
                    mix = (t - (start + duration - FADE)) / FADE
                    image = Image.blend(image, self.scenes[0][1](0.0), ease(mix))
                return image.convert("RGB")
            start += duration
        raise AssertionError("unreachable")


def main() -> None:
    args = parse_args()
    video = Video(args.dataset)
    if args.preview:
        for t in args.preview:
            path = args.mp4.with_name(f"preview-{t:05.2f}s.png")
            path.parent.mkdir(parents=True, exist_ok=True)
            video.frame(t).save(path)
            print(path)
        return

    args.mp4.parent.mkdir(parents=True, exist_ok=True)
    frames = round(video.duration * args.fps)
    encoder = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(args.fps), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(args.mp4)],
        stdin=subprocess.PIPE,
    )
    assert encoder.stdin is not None
    for index in range(frames):
        encoder.stdin.write(video.frame(index / args.fps).tobytes())
        if index % args.fps == 0:
            print(f"\rRendering {index / args.fps:4.1f}/{video.duration:.1f} s", end="", flush=True)
    encoder.stdin.close()
    if encoder.wait() != 0:
        raise SystemExit("ffmpeg failed while encoding the MP4.")
    print(f"\nWrote {args.mp4}")

    palette_filter = (
        f"fps={args.gif_fps},scale={args.gif_width}:-1:flags=lanczos,split[a][b];"
        "[a]palettegen=stats_mode=diff:max_colors=192[p];"
        "[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle"
    )
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(args.mp4), "-vf", palette_filter,
                    "-loop", "0", str(args.gif)], check=True)
    print(f"Wrote {args.gif}")


if __name__ == "__main__":
    main()
