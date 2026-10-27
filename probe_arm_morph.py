"""Preview a hand-only optical-flow transition before encoding another video."""

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parent
SIZE = (256, 320)


def load(name):
    src = Image.open(ROOT / name).convert("RGBA")
    sw, _ = src.size
    width = round(sw * 0.82)
    left = (sw - width) // 2
    return np.array(src.crop((left, 0, left + width, width * 5 // 4))
                    .resize(SIZE, Image.Resampling.LANCZOS))


start = load("deepseek_open.png")
end = load("deepseek_mid.png")
bg = np.zeros((SIZE[1], SIZE[0], 3), dtype=np.uint8)
bg[:] = (15, 25, 50)


def grayscale(rgba):
    alpha = rgba[:, :, 3:4].astype(np.float32) / 255
    composite = rgba[:, :, :3] * alpha + bg * (1 - alpha)
    return cv2.cvtColor(composite.astype(np.uint8), cv2.COLOR_RGB2GRAY)


flow_forward = cv2.calcOpticalFlowFarneback(
    grayscale(start), grayscale(end), None, 0.5, 4, 27, 4, 7, 1.5, 0)
yy, xx = np.mgrid[:SIZE[1], :SIZE[0]].astype(np.float32)
mask_image = Image.new("L", SIZE)
draw = ImageDraw.Draw(mask_image)
draw.polygon(((24, 58), (98, 58), (112, 153), (100, 231),
              (26, 225), (18, 125)), fill=255)
mask = np.array(mask_image.filter(ImageFilter.GaussianBlur(9)),
                dtype=np.float32)[:, :, None] / 255


def morph(fraction):
    map_a_x = xx - flow_forward[:, :, 0] * fraction
    map_a_y = yy - flow_forward[:, :, 1] * fraction
    warped_a = cv2.remap(start, map_a_x, map_a_y, cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT)
    combined = start * (1 - mask) + warped_a * mask
    return Image.fromarray(np.uint8(np.clip(combined, 0, 255)), "RGBA")


if __name__ == "__main__":
    sheet = Image.new("RGB", (128 * 5, 160), (15, 25, 50))
    for index, fraction in enumerate((0, 0.25, 0.5, 0.75, 1)):
        frame = morph(fraction).resize((128, 160), Image.Resampling.LANCZOS)
        backing = Image.new("RGBA", frame.size, (15, 25, 50, 255))
        backing.alpha_composite(frame)
        sheet.paste(backing.convert("RGB"), (index * 128, 0))
    sheet.save(ROOT / "arm_morph_probe.png")
    print("arm_morph_probe.png")
