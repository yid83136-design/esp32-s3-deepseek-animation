"""Play the pre-rendered high-detail animation stream on the 2号 TFT."""

import deflate
import io
import micropython
import struct
import time

from machine import Pin, SPI
from ST7735 import TFT


VIDEO = "hd_idle.dsv"
FRAME_BYTES = 128 * 160 * 2


@micropython.viper
def apply_delta(target, change, length: int):
    current = ptr8(target)
    update = ptr8(change)
    for offset in range(length):
        current[offset] = current[offset] ^ update[offset]


def load_video():
    with open(VIDEO, "rb") as source:
        header = source.read(12)
        if len(header) != 12 or header[:4] != b"DSV2":
            raise ValueError("Bad video header")
        width, height, count, fps = struct.unpack("<HHHH", header[4:])
        if (width, height) != (128, 160) or count < 2 or fps < 1:
            raise ValueError("Unsupported video")
        frames = []
        current = bytearray(FRAME_BYTES)
        for _ in range(count):
            size_bytes = source.read(4)
            if len(size_bytes) != 4:
                raise ValueError("Truncated frame header")
            size = struct.unpack("<I", size_bytes)[0]
            compressed = source.read(size)
            if len(compressed) != size:
                raise ValueError("Truncated frame")
            with deflate.DeflateIO(io.BytesIO(compressed), deflate.ZLIB) as stream:
                frame = stream.read()
            if len(frame) != FRAME_BYTES:
                raise ValueError("Invalid frame size")
            apply_delta(current, frame, FRAME_BYTES)
            frames.append(bytes(current))
    return frames, fps


def run():
    frames, fps = load_video()
    backlight = Pin(7, Pin.OUT)
    backlight.off()
    spi = SPI(1, baudrate=10_000_000, polarity=0, phase=0,
              sck=Pin(12), mosi=Pin(11))
    screen = TFT(spi, 9, 10, 8)
    screen.initr()
    screen.rgb(True)
    screen.image(0, 0, 127, 159, frames[0])
    backlight.on()
    print("HD video running", len(frames), "frames", fps, "fps")
    period = 1000 // fps
    next_at = time.ticks_ms()
    while True:
        for frame in frames:
            screen.image(0, 0, 127, 159, frame)
            next_at = time.ticks_add(next_at, period)
            remaining = time.ticks_diff(next_at, time.ticks_ms())
            if remaining > 0:
                time.sleep_ms(remaining)
            elif remaining < -period:
                next_at = time.ticks_ms()


if __name__ == "__main__":
    run()
