import gc
import sys
import time
import machine

print("Hello from the new ESP32-S3!")
print("MicroPython:", sys.version)
print("Machine:", sys.implementation)
print("Free heap bytes:", gc.mem_free())

while True:
    print("ESP32-S3 running:", time.ticks_ms(), "ms")
    time.sleep(2)
