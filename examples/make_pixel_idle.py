"""Build a consistent, low-resolution pixel-art idle animation for ST7735."""

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
W, H = 64, 80
SOURCE = ROOT / "deepseek_pixel_source.png"


def sprite():
    source = Image.open(SOURCE).convert("RGBA")
    sw, _ = source.size
    crop_width = round(sw * 0.82)
    crop_height = round(crop_width * H / W)
    left = (sw - crop_width) // 2
    source = source.crop((left, 0, left + crop_width, crop_height))
    source = source.resize((W, H), Image.Resampling.BOX)
    alpha = source.getchannel("A").point(lambda value: 255 if value >= 96 else 0)
    rgb = source.convert("RGB").quantize(
        colors=24, method=Image.Quantize.FASTOCTREE,
        dither=Image.Dither.NONE).convert("RGB")
    rgb.putalpha(alpha)
    return rgb


base = sprite()
base.save(ROOT / "pixel_sprite_64x80.png")
base.resize((W * 4, H * 4), Image.Resampling.NEAREST).save(
    ROOT / "pixel_sprite_zoom.png")


def closed_eyes(image):
    """Replace only the tiny eye interiors; the rest of the sprite stays fixed."""
    image = image.copy()
    draw = ImageDraw.Draw(image)
    skin = (239, 191, 179, 255)
    ink = (25, 30, 77, 255)
    for x0, x1 in ((24, 30), (38, 44)):
        draw.rectangle((x0, 32, x1, 36), fill=skin)
        draw.line((x0, 33, x1, 33), fill=ink, width=1)
    return image


def scene(phase, blink=False):
    # One display pixel is a 2x2 physical block. All motions happen on this
    # shared pixel grid, so there is no resampling shimmer between frames.
    image = Image.new("RGB", (W, H), (9, 18, 43))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 56, W, H), fill=(11, 25, 54))
    draw.rectangle((0, 72, W, H), fill=(14, 31, 63))
    stars = ((5, 8), (54, 10), (8, 29), (60, 35), (4, 59), (57, 67))
    for index, (x, y) in enumerate(stars):
        drift = (phase // 3 + index) % 3 - 1
        shade = (68, 125, 179) if (phase + index) % 4 else (109, 184, 228)
        draw.point((x + drift, y), fill=shade)
        if (phase + index) % 5 == 0:
            draw.point((x + drift + 1, y), fill=shade)

    poses = ((0, 0), (0, 0), (0, -1), (0, -1),
             (1, -1), (1, 0), (0, 1), (0, 1))
    dx, dy = poses[phase]
    actor = closed_eyes(base) if blink else base
    image.paste(actor, (dx, dy), actor)
    return image


def raw565(image):
    raw = bytearray(W * H * 2)
    for i, (r, g, b) in enumerate(image.get_flattened_data()):
        value = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        raw[2 * i] = value >> 8
        raw[2 * i + 1] = value & 255
    return raw


frames = []
for phase in range(8):
    frame = scene(phase)
    (ROOT / ("px_%02d.bin" % phase)).write_bytes(raw565(frame))
    frame.resize((W * 2, H * 2), Image.Resampling.NEAREST).save(
        ROOT / ("px_%02d_preview.png" % phase))
    frames.append(frame)

blink = scene(0, blink=True)
(ROOT / "px_blink.bin").write_bytes(raw565(blink))
blink.resize((W * 2, H * 2), Image.Resampling.NEAREST).save(
    ROOT / "px_blink_preview.png")

sheet = Image.new("RGB", (W * 2 * 4, H * 2 * 2))
for index, frame in enumerate(frames):
    sheet.paste(frame.resize((W * 2, H * 2), Image.Resampling.NEAREST),
                ((index % 4) * W * 2, (index // 4) * H * 2))
sheet.save(ROOT / "pixel_idle_contact_sheet.png")
print("Generated", len(frames) + 1, "pixel frames")
