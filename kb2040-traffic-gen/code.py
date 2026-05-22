# Copyright 2026 Curtis Galloway
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# code.py — KB2040 USB traffic generator for Cynthion capture sessions
#
# BOOT button (or 'start\n' on CDC data port): start cycling through patterns.
# BOOT button again: stop.
# NeoPixel shows current state/pattern type.
# CDC data port (second serial device) prints pattern names as they run —
# useful for correlating capture timestamps.
#
# CDC bulk patterns use a simple echo protocol with host_exerciser.py:
#   device writes → host echoes back → device reads echo
# pat_cdc_receive inverts this: host sends probe bursts, device reads them.
#
# Requires: adafruit_hid library bundle in /lib/
#
# Pin names for KB2040 (CircuitPython 9.x):
#   board.NEOPIXEL — onboard NeoPixel
#   board.BUTTON   — BOOT button (pull-up, active-low after boot)
# Verify with: import board; print(dir(board))

import math
import time
import board
import digitalio
import neopixel
import microcontroller
import usb_hid
import usb_cdc
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# ---------------------------------------------------------------------------
# Hardware
# ---------------------------------------------------------------------------

pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.25, auto_write=True)

btn = digitalio.DigitalInOut(board.BUTTON)
btn.direction = digitalio.Direction.INPUT
btn.pull = digitalio.Pull.UP  # active-low

# ---------------------------------------------------------------------------
# USB devices (configured in boot.py)
# ---------------------------------------------------------------------------

kbd = Keyboard(usb_hid.devices)
mouse = Mouse(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)
cdc = usb_cdc.data    # second CDC port; None until host opens it

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

OFF       = (0,  0,  0)
IDLE      = (0,  0, 12)
KBD       = (0, 28,  0)
MOUSE_C   = (0, 20, 20)
CONSUMER  = (15, 0, 28)
SERIAL    = (28, 18,  0)
MIXED     = (24, 20,  0)
RECONNECT = (28,  8,  0)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def px(color):
    pixel[0] = color

def log(msg):
    try:
        if cdc and cdc.connected:
            cdc.write((msg + "\r\n").encode("utf-8"))
    except Exception:
        pass

_btn_last = True
_btn_ts   = 0.0

def button_pressed():
    """Edge-detect with 50 ms debounce. Returns True once per physical press."""
    global _btn_last, _btn_ts
    now = time.monotonic()
    val = btn.value
    fell = _btn_last and not val
    _btn_last = val
    if fell and now - _btn_ts > 0.05:
        _btn_ts = now
        return True
    return False

_cmd_buf = b""

def poll_start_cmd():
    """Check CDC data port for a 'start\\n' command from the host. Non-blocking."""
    global _cmd_buf
    try:
        if cdc and cdc.in_waiting:
            _cmd_buf += cdc.read(cdc.in_waiting)
            if b"start" in _cmd_buf:
                _cmd_buf = b""
                return True
            if len(_cmd_buf) > 64:
                _cmd_buf = _cmd_buf[-64:]
    except Exception:
        pass
    return False

def cdc_read_echo(expected_len, wait_ms=50):
    """Read up to expected_len echo bytes after a write.  Returns bytes read."""
    time.sleep(wait_ms / 1000)
    try:
        n = cdc.in_waiting
        if n:
            return cdc.read(min(n, expected_len))
    except Exception:
        pass
    return b""

# ---------------------------------------------------------------------------
# Pattern generators
#
# Each function is a generator yielding between small steps so the main loop
# can poll the stop button without blocking.
# ---------------------------------------------------------------------------

def pat_kbd_burst():
    """30 rapid individual keystrokes — dense interrupt IN traffic."""
    px(KBD); log("[kbd-burst] rapid keystrokes")
    keys = [Keycode.A, Keycode.S, Keycode.D, Keycode.F]
    for i in range(30):
        kbd.press(keys[i % 4])
        kbd.release_all()
        time.sleep(0.06)
        yield


def pat_kbd_typing():
    """Variable-rate typing simulating human input."""
    px(KBD); log("[kbd-typing] simulated typing")
    strokes = [
        ([], Keycode.H,     0.11),
        ([], Keycode.E,     0.09),
        ([], Keycode.L,     0.07),
        ([], Keycode.L,     0.08),
        ([], Keycode.O,     0.16),
        ([], Keycode.SPACE, 0.13),
        ([], Keycode.W,     0.10),
        ([], Keycode.O,     0.09),
        ([], Keycode.R,     0.08),
        ([], Keycode.L,     0.10),
        ([], Keycode.D,     0.08),
        ([], Keycode.ENTER, 0.20),
    ]
    for mods, key, delay in strokes:
        for mod in mods:
            kbd.press(mod)
        kbd.press(key)
        time.sleep(0.05)
        kbd.release_all()
        time.sleep(delay)
        yield


def pat_kbd_modifiers():
    """Modifier-key combos — generates multi-byte HID reports."""
    px(KBD); log("[kbd-modifiers] modifier combos")
    combos = [
        ([Keycode.LEFT_CONTROL], Keycode.Z),
        ([Keycode.LEFT_CONTROL], Keycode.Y),
        ([Keycode.LEFT_CONTROL], Keycode.C),
        ([Keycode.LEFT_SHIFT, Keycode.LEFT_CONTROL], Keycode.Z),
        ([Keycode.LEFT_SHIFT], Keycode.F5),
        ([Keycode.LEFT_SHIFT], Keycode.F6),
        ([], Keycode.F5),
        ([], Keycode.ESCAPE),
    ]
    for mods, key in combos:
        for mod in mods:
            kbd.press(mod)
        kbd.press(key)
        time.sleep(0.08)
        kbd.release_all()
        time.sleep(0.30)
        yield


def pat_kbd_fkeys():
    """F1–F12 function keys."""
    px(KBD); log("[kbd-fkeys] function keys")
    fkeys = [
        Keycode.F1,  Keycode.F2,  Keycode.F3,  Keycode.F4,
        Keycode.F5,  Keycode.F6,  Keycode.F7,  Keycode.F8,
        Keycode.F9,  Keycode.F10, Keycode.F11, Keycode.F12,
    ]
    for key in fkeys:
        kbd.press(key)
        time.sleep(0.06)
        kbd.release_all()
        time.sleep(0.12)
        yield


def pat_mouse_circles():
    """Smooth circular mouse movement — sustained interrupt endpoint traffic."""
    px(MOUSE_C); log("[mouse-circles] circular movement")
    steps = 60
    radius = 25
    prev_x, prev_y = radius, 0
    for _ in range(2):
        for i in range(steps):
            angle = 2 * math.pi * i / steps
            x = int(radius * math.cos(angle))
            y = int(radius * math.sin(angle))
            mouse.move(x - prev_x, y - prev_y)
            prev_x, prev_y = x, y
            time.sleep(0.025)
            yield


def pat_mouse_clicks():
    """Left, right, middle button clicks plus scroll wheel."""
    px(MOUSE_C); log("[mouse-clicks] buttons + scroll")
    for _ in range(4):
        mouse.click(Mouse.LEFT_BUTTON)
        time.sleep(0.15)
        mouse.click(Mouse.RIGHT_BUTTON)
        time.sleep(0.15)
        mouse.click(Mouse.MIDDLE_BUTTON)
        time.sleep(0.15)
        mouse.move(wheel=5)
        time.sleep(0.10)
        mouse.move(wheel=-5)
        time.sleep(0.20)
        yield


def pat_mouse_drag():
    """Button held during movement — drag reports."""
    px(MOUSE_C); log("[mouse-drag] click-hold-move")
    mouse.press(Mouse.LEFT_BUTTON)
    for _ in range(40):
        mouse.move(3, 0)
        time.sleep(0.03)
        yield
    for _ in range(40):
        mouse.move(-3, 0)
        time.sleep(0.03)
        yield
    mouse.release(Mouse.LEFT_BUTTON)
    yield


def pat_consumer_ctrl():
    """Consumer control / media keys — single-value HID reports."""
    px(CONSUMER); log("[consumer-ctrl] media keys")
    codes = [
        ConsumerControlCode.VOLUME_INCREMENT,
        ConsumerControlCode.VOLUME_INCREMENT,
        ConsumerControlCode.VOLUME_DECREMENT,
        ConsumerControlCode.MUTE,
        ConsumerControlCode.PLAY_PAUSE,
        ConsumerControlCode.SCAN_NEXT_TRACK,
        ConsumerControlCode.SCAN_PREVIOUS_TRACK,
        ConsumerControlCode.MUTE,
        ConsumerControlCode.BRIGHTNESS_INCREMENT,
        ConsumerControlCode.BRIGHTNESS_DECREMENT,
    ]
    for code in codes:
        cc.send(code)
        time.sleep(0.25)
        yield


# --- CDC bulk patterns (require host_exerciser.py running) ---
#
# Echo protocol: device writes → host echoes → device reads echo.
# Each cdc.write() is followed by cdc_read_echo() on the same step.

def pat_cdc_large():
    """64 × 64-byte writes with host echo — fills bulk pipe both directions."""
    px(SERIAL); log("[cdc-large] bulk write+echo")
    if not (cdc and cdc.connected):
        yield; return
    for seq in range(64):
        payload = bytes([seq & 0xFF] * 64)
        cdc.write(payload)
        echo = cdc_read_echo(len(payload))
        if echo and echo != payload[:len(echo)]:
            log(f"[cdc-large] echo mismatch seq={seq}")
        yield


def pat_cdc_small():
    """Varied-size writes (1–65 B) with echo — exercises packet-boundary handling."""
    px(SERIAL); log("[cdc-small] varied small packets + echo")
    if not (cdc and cdc.connected):
        yield; return
    sizes = [1, 2, 3, 7, 8, 9, 15, 16, 17, 31, 32, 33, 63, 64, 65]
    for size in sizes * 3:
        payload = bytes([size & 0xFF] * size)
        cdc.write(payload)
        cdc_read_echo(len(payload))
        time.sleep(0.02)
        yield


def pat_cdc_patterns():
    """Named data patterns with echo — easy to identify in a capture hex dump."""
    px(SERIAL); log("[cdc-patterns] data patterns + echo")
    if not (cdc and cdc.connected):
        yield; return
    payloads = [
        bytes([0x00] * 64),
        bytes([0xFF] * 64),
        bytes([0xAA, 0x55] * 32),
        bytes(range(64)),
        bytes(range(63, -1, -1)),
        bytes([0xDE, 0xAD, 0xBE, 0xEF] * 16),
        bytes([i ^ 0xA5 for i in range(64)]),
    ]
    for p in payloads:
        cdc.write(p)
        cdc_read_echo(len(p))
        yield


def pat_cdc_receive():
    """Device reads only — exercises host-initiated bulk OUT (probe bursts from host)."""
    px(SERIAL); log("[cdc-receive] reading host probe bursts")
    if not (cdc and cdc.connected):
        yield; return
    total = 0
    for _ in range(30):
        try:
            n = cdc.in_waiting
            if n:
                total += len(cdc.read(n))
        except Exception:
            pass
        time.sleep(0.1)
        yield
    log(f"[cdc-receive] {total} bytes received from host")


def pat_mixed_hid():
    """Keyboard and mouse interleaved — two interrupt endpoints simultaneously."""
    px(MIXED); log("[mixed-hid] kbd + mouse")
    keys = [Keycode.A, Keycode.S, Keycode.D, Keycode.F]
    for i in range(24):
        kbd.press(keys[i % 4])
        kbd.release_all()
        mouse.move(4 if i % 2 == 0 else -4, 2 if i % 3 == 0 else -2)
        if i % 6 == 0:
            mouse.click(Mouse.LEFT_BUTTON)
        time.sleep(0.08)
        yield


def pat_mixed_all():
    """HID keyboard, mouse, and CDC simultaneously."""
    px(MIXED); log("[mixed-all] kbd + mouse + cdc")
    for i in range(20):
        kbd.press([Keycode.A, Keycode.B, Keycode.C][i % 3])
        kbd.release_all()
        mouse.move(3 if i % 2 == 0 else -3, 0)
        if cdc and cdc.connected:
            payload = bytes([i & 0xFF] * 16)
            cdc.write(payload)
            cdc_read_echo(len(payload), wait_ms=30)
        time.sleep(0.08)
        yield


def pat_reconnect():
    """Hardware reset — triggers a full USB re-enumeration sequence."""
    px(RECONNECT); log("[reconnect] triggering re-enumeration in 500 ms")
    kbd.release_all()
    mouse.release_all()
    for _ in range(4):
        px(RECONNECT); time.sleep(0.12)
        px(OFF);        time.sleep(0.12)
        yield
    microcontroller.reset()


# ---------------------------------------------------------------------------
# Pattern registry — order determines capture sequence
# ---------------------------------------------------------------------------

PATTERNS = [
    pat_kbd_burst,
    pat_kbd_typing,
    pat_kbd_modifiers,
    pat_kbd_fkeys,
    pat_mouse_circles,
    pat_mouse_clicks,
    pat_mouse_drag,
    pat_consumer_ctrl,
    pat_cdc_large,
    pat_cdc_small,
    pat_cdc_patterns,
    pat_cdc_receive,
    pat_mixed_hid,
    pat_mixed_all,
    pat_reconnect,     # always last — resets the board
]


def run_all():
    """Cycle through every pattern. Returns True on completion, False if stopped."""
    for fn in PATTERNS:
        gen = fn()
        for _ in gen:
            if button_pressed():
                kbd.release_all()
                mouse.release_all()
                return False
        # drain any buffered CDC input before moving to the next pattern
        try:
            if cdc and cdc.in_waiting:
                cdc.read(cdc.in_waiting)
        except Exception:
            pass
        time.sleep(0.30)
    return True


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

log("KB2040 USB Traffic Generator ready")
log("Press BOOT button or send 'start\\n' to begin")

while True:
    t = time.monotonic()
    brightness = (math.sin(t * 1.8) + 1) / 2
    px((0, 0, int(brightness * 12)))
    time.sleep(0.04)

    if button_pressed() or poll_start_cmd():
        log("--- start ---")
        px(KBD)
        done = run_all()
        log("--- all patterns complete ---" if done else "--- stopped ---")
        px(IDLE)
        time.sleep(0.5)   # prevent immediate re-trigger
