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
# BOOT button: press to start cycling through all patterns, press again to stop.
# NeoPixel shows current state/pattern type.
# CDC data port (second serial device) prints pattern names as they run —
# useful for correlating capture timestamps. Nothing needs to read it.
#
# Requires: adafruit_hid library bundle in /lib/
#
# Pin names verified for KB2040 (CircuitPython 9.x):
#   board.NEOPIXEL — onboard NeoPixel
#   board.BUTTON   — BOOT button (pull-up, active-low after boot)
# If either fails at startup, run `import board; print(dir(board))` in the REPL.

import math
import time
import board
import digitalio
import neopixel
import microcontroller
import usb_hid
import usb_cdc
import usb_midi
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
midi_out = usb_midi.ports[1]   # ports[0]=IN (host→device), ports[1]=OUT (device→host)
cdc = usb_cdc.data             # second CDC port; None if host hasn't opened it

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

OFF       = (0,  0,  0)
IDLE      = (0,  0, 12)
KBD       = (0, 28,  0)
MOUSE_C   = (0, 20, 20)
CONSUMER  = (15, 0, 28)
SERIAL    = (28, 18,  0)
MIDI_C    = (24,  0, 24)
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
_btn_ts = 0.0

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

# ---------------------------------------------------------------------------
# Pattern generators
#
# Each function is a generator that yields between small steps so the main
# loop can poll the button and stop early.  Each yields at least once so the
# caller always gets control back immediately after calling next().
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
    # (modifier_list, key, post_delay_s)
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


def pat_cdc_large():
    """64 × 64-byte chunks — fills USB full-speed bulk pipe."""
    px(SERIAL); log("[cdc-large] large bulk transfer")
    if not (cdc and cdc.connected):
        yield; return
    chunk = bytes(range(64))
    for _ in range(64):
        cdc.write(chunk)
        time.sleep(0.01)
        yield


def pat_cdc_small():
    """Packets of 1–65 bytes — exercises short and boundary-size transfers."""
    px(SERIAL); log("[cdc-small] varied small packets")
    if not (cdc and cdc.connected):
        yield; return
    sizes = [1, 2, 3, 7, 8, 9, 15, 16, 17, 31, 32, 33, 63, 64, 65]
    for size in sizes * 3:
        cdc.write(bytes([size & 0xFF] * size))
        time.sleep(0.04)
        yield


def pat_cdc_patterns():
    """Transfers with recognizable data patterns — easy to spot in a hex dump."""
    px(SERIAL); log("[cdc-patterns] data patterns")
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
        time.sleep(0.12)
        yield


def pat_midi_notes():
    """Chromatic scale across two octaves, two channels — note on/off pairs."""
    px(MIDI_C); log("[midi-notes] chromatic scale")
    for octave in range(2):
        for semitone in range(12):
            note = 48 + octave * 12 + semitone
            for ch in range(2):
                midi_out.write(bytes([0x90 | ch, note, 100]))
            time.sleep(0.08)
            for ch in range(2):
                midi_out.write(bytes([0x80 | ch, note, 0]))
            time.sleep(0.04)
            yield


def pat_midi_cc():
    """CC sweeps across all 128 controllers at five values each."""
    px(MIDI_C); log("[midi-cc] control change sweep")
    for cc_num in range(0, 128, 4):
        for val in [0, 32, 64, 96, 127]:
            midi_out.write(bytes([0xB0, cc_num, val]))
            time.sleep(0.02)
        yield


def pat_midi_sysex():
    """SysEx messages of increasing length — tests variable-length bulk parsing."""
    px(MIDI_C); log("[midi-sysex] sysex messages")
    messages = [
        bytes([0xF0, 0x7D, 0x01, 0xF7]),
        bytes([0xF0, 0x7D] + list(range(16))  + [0xF7]),
        bytes([0xF0, 0x7D] + list(range(48))  + [0xF7]),
        bytes([0xF0, 0x7D] + [0x55] * 64      + [0xF7]),
    ]
    for msg in messages:
        midi_out.write(msg)
        time.sleep(0.25)
        yield


def pat_midi_program_pitch():
    """Program change and pitch bend — additional MIDI message types."""
    px(MIDI_C); log("[midi-prog-pitch] program change + pitch bend")
    for prog in range(16):
        midi_out.write(bytes([0xC0, prog]))
        time.sleep(0.05)
        yield
    for raw in range(0, 16384, 512):
        midi_out.write(bytes([0xE0, raw & 0x7F, (raw >> 7) & 0x7F]))
        time.sleep(0.03)
        yield


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
    """All four interface classes active simultaneously."""
    px(MIXED); log("[mixed-all] kbd + mouse + midi + cdc")
    for i in range(20):
        kbd.press([Keycode.A, Keycode.B, Keycode.C][i % 3])
        kbd.release_all()
        mouse.move(3 if i % 2 == 0 else -3, 0)
        note = 60 + (i % 12)
        midi_out.write(bytes([0x90, note, 80]))
        if cdc and cdc.connected:
            cdc.write(bytes([i & 0xFF] * 16))
        time.sleep(0.05)
        midi_out.write(bytes([0x80, note, 0]))
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
    microcontroller.reset()   # board restarts; USB enumerates fresh


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
    pat_midi_notes,
    pat_midi_cc,
    pat_midi_sysex,
    pat_midi_program_pitch,
    pat_mixed_hid,
    pat_mixed_all,
    pat_reconnect,   # always last — resets the board
]


def run_all():
    """Cycle through every pattern.  Returns True on completion, False if stopped."""
    for fn in PATTERNS:
        gen = fn()
        for _ in gen:
            if button_pressed():
                kbd.release_all()
                mouse.release_all()
                return False
        time.sleep(0.30)   # brief pause between patterns
    return True


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

log("KB2040 USB Traffic Generator ready")
log("Press BOOT button to start/stop")

while True:
    t = time.monotonic()
    brightness = (math.sin(t * 1.8) + 1) / 2
    px((0, 0, int(brightness * 12)))
    time.sleep(0.04)

    if button_pressed():
        log("--- start ---")
        px(KBD)
        done = run_all()
        log("--- all patterns complete ---" if done else "--- stopped ---")
        px(IDLE)
        time.sleep(0.5)   # prevent immediate re-trigger
