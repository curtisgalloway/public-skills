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

# boot.py — runs once at power-on, configures USB interfaces before code.py
#
# Exposes:
#   - 2x CDC serial (index 0 = REPL console, index 1 = status/log data port)
#   - HID: keyboard + mouse + consumer control (media keys)
#   - MIDI (bulk endpoints, sysex capable)

import usb_hid
import usb_cdc
import usb_midi

usb_cdc.enable(console=True, data=True)

usb_hid.enable((
    usb_hid.Device.KEYBOARD,
    usb_hid.Device.MOUSE,
    usb_hid.Device.CONSUMER_CONTROL,
))

usb_midi.enable()
