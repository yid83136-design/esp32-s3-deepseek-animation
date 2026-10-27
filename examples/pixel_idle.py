"""Slow 8-frame pixel-art idle animation for 2号 ESP32-S3 and ST7735."""

import time
from machine import Pin, SPI
from ST7735 import TFT


SMALL_WIDTH = 64
SMALL_HEIGHT = 80
SMALL_BYTES = SMALL_WIDTH * SMALL_HEIGHT * 2


def expand2x(raw):
    """Expand one 64x80 RGB565 frame to the native 128x160 TFT size."""
    if len(raw) != SMALL_BYTES:
        raise ValueError("Pixel frame has wrong size")
    wide = bytearray(SMALL_WIDTH * 4 * SMALL_HEIGHT)
    for y in range(SMALL_HEIGHT):
        source = y * SMALL_WIDTH * 2
        dest = y * SMALL_WIDTH * 4
        for x in range(SMALL_WIDTH):
            first = raw[source + 2 * x]
            second = raw[source + 2 * x + 1]
            at = dest + 4 * x
            wide[at] = first
            wide[at + 1] = second
            wide[at + 2] = first
            wide[at + 3] = second
    screen = bytearray(SMALL_WIDTH * 4 * SMALL_HEIGHT * 2)
    row_size = SMALL_WIDTH * 4
    for y in range(SMALL_HEIGHT):
        row = wide[y * row_size:(y + 1) * row_size]
        screen[2 * y * row_size:(2 * y + 1) * row_size] = row
        screen[(2 * y + 1) * row_size:(2 * y + 2) * row_size] = row
    return screen


def setup_screen():
    backlight = Pin(7, Pin.OUT)
    backlight.off()
    spi = SPI(1, baudrate=10_000_000, polarity=0, phase=0,
              sck=Pin(12), mosi=Pin(11))
    screen = TFT(spi, 9, 10, 8)
    screen.initr()
    screen.rgb(True)
    return screen, backlight


def load_frames():
    frames = []
    for number in range(8):
        with open("px_%02d.bin" % number, "rb") as file:
            frames.append(expand2x(file.read()))
    with open("px_blink.bin", "rb") as file:
        blink = expand2x(file.read())
    return frames, blink


def show(screen, frame):
    screen.image(0, 0, 127, 159, frame)


def run():
    frames, blink = load_frames()
    screen, backlight = setup_screen()
    show(screen, frames[0])
    backlight.on()
    print("Pixel idle animation running")
    cycle = 0
    while True:
        for frame in frames:
            show(screen, frame)
            time.sleep_ms(360)
        cycle += 1
        if cycle % 2 == 0:
            show(screen, blink)
            time.sleep_ms(120)
            show(screen, frames[0])


if __name__ == "__main__":
    run()
