# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0

"""KB2040 boot.py — runs once at power-on, configures USB interfaces.

Exposes:
  - 2x CDC serial (index 0 = REPL console, index 1 = data port for
    host_exerciser.py)
  - HID: keyboard + mouse + consumer control (media keys)
"""

import usb_hid
import usb_cdc

usb_cdc.enable(console=True, data=True)

usb_hid.enable(
    (
        usb_hid.Device.KEYBOARD,
        usb_hid.Device.MOUSE,
        usb_hid.Device.CONSUMER_CONTROL,
    )
)
