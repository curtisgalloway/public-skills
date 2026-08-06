#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0

"""Optional Apollo LED status feedback for Cynthion capture scripts.

Cynthion's Apollo debug microcontroller (VID 0x1d50 / PID 0x615c) drives the
five status LEDs (A…E) and accepts a SET_LED_PATTERN vendor request.  When the
analyzer gateware is running, the FPGA — not Apollo — owns the CONTROL port and
presents the analyzer device (PID 0x615b), so Apollo is usually *not* separately
enumerated during a capture.

This module is therefore best-effort decoration: every method is a silent no-op
when PID 0x615c is not found, and capture behaves identically either way.  It
only lights up on setups where Apollo happens to be reachable alongside the
analyzer.  Do not rely on the LEDs as a capture-status indicator.

LED patterns
------------
  set_ready()      Slow idle pulse (firmware-driven, autonomous — no thread)
  start_capture()  Fill-up animation driven by a background thread:
                     A → A+B → A+B+C → A+B+C+D → all 5 → off → repeat
  stop()           Stop animation thread and turn all LEDs off

Hardware reference
------------------
  Apollo repo:  https://github.com/greatscottgadgets/apollo
  Vendor req:   firmware/src/vendor.c  VENDOR_REQUEST_SET_LED_PATTERN = 0xa1
                (wValue carries the pattern; no data stage)
  Pattern enum: firmware/src/led.h  led_pattern_t — wValue 0…31 is a static
                LED bitmask; larger values select firmware blink patterns
                (LED_IDLE = 500, LED_JTAG_CONNECTED = 150,
                 LED_JTAG_UPLOADING = 50, LED_FLASH_CONNECTED = 130)
"""

import threading
import time

import usb.core

# ---------------------------------------------------------------------------
# Apollo USB identifiers
# ---------------------------------------------------------------------------

_APOLLO_VID = 0x1d50
_APOLLO_PID = 0x615c

# bmRequestType: Host-to-Device | Vendor | Device  (0x00 | 0x40 | 0x00 = 0x40)
_REQUEST_TYPE = 0x40
_SET_LED_PATTERN = 0xa1   # VENDOR_REQUEST_SET_LED_PATTERN

# ---------------------------------------------------------------------------
# Pattern values
# ---------------------------------------------------------------------------

# led_pattern_t LED_IDLE — the MCU blinks autonomously once this value is
# written, so no host thread is needed to sustain it.
LED_IDLE = 500

# Static bitmask frames for the fill-up animation (bit 0 = LED A … bit 4 = LED E).
# Each frame holds LEDs A through N lit, then a dark frame to restart the cycle.
_FILL_FRAMES = [
    0b00001,   # A only
    0b00011,   # A + B
    0b00111,   # A + B + C
    0b01111,   # A + B + C + D
    0b11111,   # all five
    0b00000,   # dark — pause before restarting
]

# Seconds per frame → 6 frames × 0.15 s ≈ 0.9 s per cycle.
_FILL_INTERVAL_S = 0.15


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class ApolloLeds:
    """Controls Cynthion's Apollo debug-controller LEDs during capture.

    Usage::

        leds = ApolloLeds()          # safe even without CONTROL port connected
        leds.set_ready()             # slow pulse while waiting to capture
        ...
        leds.start_capture()         # fill-up animation while capturing
        ...
        leds.stop()                  # all LEDs off when done
    """

    def __init__(self):
        try:
            self._dev = usb.core.find(idVendor=_APOLLO_VID, idProduct=_APOLLO_PID)
        except Exception:
            # No usable libusb backend — degrade to a no-op rather than
            # taking the capture down with us.
            self._dev = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_ready(self):
        """Slow idle pulse — device connected and ready to capture.

        The Apollo firmware drives the blink autonomously; no thread is
        started here.
        """
        self._stop_thread()
        self._set(LED_IDLE)

    def start_capture(self):
        """Fill-up animation — capture is running.

        Starts a daemon thread that cycles through _FILL_FRAMES at
        _FILL_INTERVAL_S seconds per step.  Calls stop() to end it.
        """
        self._stop_thread()
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._fill_loop,
            daemon=True,
            name="apollo-leds",
        )
        self._thread.start()

    def stop(self):
        """Stop the animation thread and turn all LEDs off."""
        self._stop_thread()
        self._set(0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set(self, pattern: int):
        if self._dev is None:
            return
        try:
            self._dev.ctrl_transfer(
                _REQUEST_TYPE, _SET_LED_PATTERN, pattern, 0, None,
            )
        except Exception:
            # CONTROL port disconnected mid-session — degrade gracefully.
            self._dev = None

    def _fill_loop(self):
        while not self._stop_event.is_set():
            for frame in _FILL_FRAMES:
                if self._stop_event.is_set():
                    return
                self._set(frame)
                self._stop_event.wait(_FILL_INTERVAL_S)

    def _stop_thread(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
