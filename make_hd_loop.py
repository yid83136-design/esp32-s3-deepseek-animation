"""Render a seamless HD idle loop and encode it for the ST7735.

The MP4 is for desktop preview. The ESP32 reads hd_idle.dsv instead of trying
to decode MP4 on the microcontroller.
"""

from pathlib import Path
import math
import struct
import subprocess
import zlib

from PIL import Image, ImageDraw

from probe_arm_morph import morph


ROOT = Path(__file__).resolve().parent
FRAMES_DIR = ROOT / "hd_frames"
FRAMES_DIR.mkdir(exist_ok=True)
WIDTH, HEIGHT = 128, 160
SCALE = 4
COUNT = 32
FPS = 10


def rgb565(image):
    out = bytearray(WIDTH * HEIGHT * 2)
    for i, (r, g, b) in enumerate(image.get_flattened_data()):
        value = ((r & 248) << 8) | ((g & 252) << 3) | (b >> 3)
        out[2 * i] = value >> 8
        out[2 * i + 1] = value & 255
    return bytes(out)


def background(phase):
    canvas = Image.new("RGBA", (WIDTH * SCALE, HEIGHT * SCALE))
    draw = ImageDraw.Draw(canvas)
    for y in range(HEIGHT * SCALE):
        shade = y // (20 * SCALE)
        draw.line((0, y, WIDTH * SCALE, y),
                  fill=(8 + shade, 20 + shade, 47 + shade * 2, 255))
    for index, (x, y) in enumerate(((10, 12), (116, 22), (7, 75),
                                     (119, 108), (17, 141), (109, 148))):
        drift = 2 * math.sin(phase + index * 1.8)
        glow = 140 + int(50 * (1 + math.sin(phase * 2 + index)))
        sx = int((x + drift) * SCALE)
        sy = y * SCALE
        color = (90, min(220, glow), 244, 255)
        draw.line((sx - 5, sy, sx + 5, sy), fill=color, width=2)
        draw.line((sx, sy - 5, sx, sy + 5), fill=color, width=2)
    return canvas


encoded = bytearray(b"DSV2")
encoded += struct.pack("<HHHH", WIDTH, HEIGHT, COUNT, FPS)
sizes = []
previous = None
for index in range(COUNT):
    phase = index * 2 * math.pi / COUNT
    hand_position = (1 - math.cos(phase)) / 2
    sprite = morph(hand_position).resize(
        (WIDTH * SCALE, HEIGHT * SCALE), Image.Resampling.LANCZOS)
    dx = 2.2 * math.sin(phase + 0.3)
    dy = 3.3 * math.sin(phase)
    angle = 1.5 * math.sin(phase - 0.4)
    breathing = 1.0 + 0.010 * math.sin(phase)
    scaled_size = (round(sprite.width * breathing),
                   round(sprite.height * breathing))
    moved = sprite.resize(scaled_size, Image.Resampling.BICUBIC)
    layer = Image.new("RGBA", sprite.size)
    layer.alpha_composite(moved, ((sprite.width - moved.width) // 2,
                                  (sprite.height - moved.height) // 2))
    layer = layer.rotate(angle, Image.Resampling.BICUBIC,
                         center=(sprite.width // 2, sprite.height * 3 // 4),
                         translate=(round(dx * SCALE), round(dy * SCALE)))
    frame = Image.alpha_composite(background(phase), layer)
    frame = frame.convert("RGB").resize((WIDTH, HEIGHT),
                                        Image.Resampling.LANCZOS)
    frame.save(FRAMES_DIR / ("frame_%02d.png" % index))
    raw = rgb565(frame)
    change = raw if previous is None else bytes(
        current ^ old for current, old in zip(raw, previous))
    packed = zlib.compress(change, level=9)
    encoded += struct.pack("<I", len(packed))
    encoded += packed
    sizes.append(len(packed))
    previous = raw

(ROOT / "hd_idle.dsv").write_bytes(encoded)
print("frames", COUNT, "stream_bytes", len(encoded),
      "average_frame_bytes", round(sum(sizes) / COUNT))

subprocess.run([
    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
    "-framerate", str(FPS), "-i", str(FRAMES_DIR / "frame_%02d.png"),
    "-vf", "scale=512:640:flags=lanczos,format=yuv420p",
    "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p",
    str(ROOT / "hd_idle_preview.mp4"),
], check=True)
