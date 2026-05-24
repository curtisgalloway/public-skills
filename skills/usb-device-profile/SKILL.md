---
name: usb-device-profile
description: Generate a USB device profile JSON for a known device by reading its driver source code. The profile encodes the device's endpoint configuration — transfer types, directions, max packet sizes, across all USB configurations — so the Cynthion decode pipeline can correctly type endpoints when enumeration traffic was not captured. Use when the user asks to generate, update, or inspect a device profile, or when preparing a device for analysis with cynthion-anomaly-analysis.
---

<!--
Copyright 2026 Curtis Galloway

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
-->

# Cynthion Device Profile Generator

A **device profile** is a JSON file that records the static structural facts about
a USB device's endpoint configuration. It is consumed by the Cynthion decode
pipeline to pre-seed endpoint types when the capture does not include the
enumeration phase. It is *not* a behavioral contract — do not add expected NAK
rates, latency bounds, or error thresholds. Those belong in a separate
`expectations` section that does not yet exist.

See `docs/cynthion-pipeline-decisions.md` for full design rationale.

---

## Profile format

```json
{
  "device": {
    "vid": 9263,
    "pid": 43981,
    "name": "Codename",
    "speed": "full"
  },
  "configurations": [
    {
      "index": 1,
      "description": "Normal operation",
      "interfaces": [
        {
          "number": 0,
          "class": 255,
          "description": "Vendor bulk data",
          "endpoints": [
            { "address": 1,   "direction": "out", "type": "bulk",      "max_packet_size": 512 },
            { "address": 129, "direction": "in",  "type": "bulk",      "max_packet_size": 512 },
            { "address": 130, "direction": "in",  "type": "interrupt", "max_packet_size": 8   }
          ]
        }
      ]
    }
  ]
}
```

**Field reference:**

| Field | Type | Notes |
|---|---|---|
| `vid`, `pid` | integer | USB Vendor ID and Product ID, decimal |
| `name` | string | Human-readable device codename |
| `speed` | string | `"low"`, `"full"`, or `"high"` |
| `configurations[].index` | integer | Matches USB `bConfigurationValue` (starts at 1) |
| `interfaces[].number` | integer | Matches USB `bInterfaceNumber` |
| `interfaces[].class` | integer | USB interface class code (255 = vendor-specific) |
| `endpoints[].address` | integer | USB endpoint address; bit 7 set (≥ 128) = IN, clear = OUT |
| `endpoints[].direction` | string | `"in"` or `"out"` — redundant with address, kept for clarity |
| `endpoints[].type` | string | `"control"`, `"bulk"`, `"interrupt"`, or `"isochronous"` |
| `endpoints[].max_packet_size` | integer | From USB endpoint descriptor `wMaxPacketSize` |

**Endpoint address encoding:**

| address | direction | endpoint number |
|---|---|---|
| 1–15 | out | 1–15 |
| 129–143 | in | 1–15 (address − 128) |

**Transfer type from `bmAttributes` bits 1:0:**

| bits 1:0 | type |
|---|---|
| 00 | control |
| 01 | isochronous |
| 10 | bulk |
| 11 | interrupt |

**Endpoint numbers are guidance, not authoritative.** Fuchsia allocates endpoint
addresses dynamically across loaded functions; CircuitPython assigns them in
interface registration order. If enumeration is captured in the pcap, the observed
addresses override the profile. If not, the profile values are used as-is.
Include a note in `description` fields when you are uncertain about specific
endpoint addresses.

---

## Generating a profile from Fuchsia driver source

### Step 1 — Identify the function driver(s)

Find the source file(s) that implement the device's USB function(s). Look for:

- Files that call into the `fuchsia.hardware.usb.function` FIDL protocol or the
  C++ `UsbFunction` class
- Files containing `usb_endpoint_descriptor_t`, `usb_interface_descriptor_t`, or
  `usb_configuration_descriptor_t` struct definitions
- `BUILD.gn` entries that depend on `//src/devices/usb/lib/usb` or
  `//sdk/fidl/fuchsia.hardware.usb.function`

A device may have multiple function drivers (e.g., one for each USB interface).
Find all of them.

### Step 2 — Extract USB descriptors

In each function driver, locate the USB descriptor tables. They are typically
defined as `const` byte arrays or C++ struct initializers. Look for patterns like:

```cpp
const usb_endpoint_descriptor_t bulk_in_ep = {
    .bLength          = sizeof(usb_endpoint_descriptor_t),
    .bDescriptorType  = USB_DT_ENDPOINT,
    .bEndpointAddress = USB_ENDPOINT_IN | 1,   // IN, endpoint 1
    .bmAttributes     = USB_ENDPOINT_BULK,
    .wMaxPacketSize   = 512,
    .bInterval        = 0,
};
```

Or as raw byte arrays where the fields appear at fixed offsets per the USB spec:

| Offset | Field | Size |
|---|---|---|
| 0 | bLength | 1 |
| 1 | bDescriptorType (0x05 for endpoint) | 1 |
| 2 | bEndpointAddress | 1 |
| 3 | bmAttributes | 1 |
| 4 | wMaxPacketSize | 2 (little-endian) |
| 6 | bInterval | 1 |

Do the same for interface descriptors (`bDescriptorType = 0x04`):

| Offset | Field |
|---|---|
| 2 | bInterfaceNumber |
| 5 | bInterfaceClass |
| 6 | bInterfaceSubClass |
| 7 | bInterfaceProtocol |

### Step 3 — Identify configurations

Fuchsia's `usb-peripheral` driver assembles functions into configurations. If the
device has multiple configurations, they will be expressed either:

- In separate descriptor tables within the same function driver
- As separately loaded function sets in the device's component manifest (`.cml`)
  or board configuration

Look for multiple `usb_configuration_descriptor_t` structs, or for component
manifest sections that load different function sets. The `bConfigurationValue`
field (or equivalent index) identifies each configuration.

### Step 4 — Find VID and PID

Look in:

- The device's component manifest (`.cml`) for `usb_pid` / `usb_vid` metadata
- The peripheral's bind rules or board configuration file
- Comments in the function driver's header

### Step 5 — Assemble and validate

Write the profile JSON. For each endpoint address you are uncertain about (because
Fuchsia's dynamic allocator may assign it differently at runtime), note the
uncertainty in the parent interface's `description` field. Example:

```
"description": "Vendor data interface — endpoint addresses derived from source; verify against enumeration capture"
```

---

## Generating a profile from CircuitPython (boot.py)

CircuitPython's `boot.py` completely specifies the USB interface configuration.
Read it and apply the following mapping rules.

### CDC interfaces (`usb_cdc.enable`)

`usb_cdc.enable(console=True, data=True)` creates one CDC interface per `True`
argument, in order. Each CDC interface consists of two USB interfaces:

1. **CDC Communication Interface** — one Interrupt IN endpoint for notifications
   (typically 8 bytes, 16 ms interval)
2. **CDC Data Interface** — one Bulk IN and one Bulk OUT endpoint (typically 64
   bytes for full-speed)

Emit both sub-interfaces for each CDC device. Label `console` as "CDC console
(REPL/log)" and `data` as "CDC data port".

### HID interfaces (`usb_hid.enable`)

`usb_hid.enable((device1, device2, ...))` creates one HID interface containing
all listed devices, each distinguished by a report ID. The interface has a single
Interrupt IN endpoint (typically 8–64 bytes, 8 ms interval) and sometimes an
Interrupt OUT endpoint for LED reports (keyboard only, 1 byte).

| Device constant | Notes |
|---|---|
| `usb_hid.Device.KEYBOARD` | Interrupt IN (8 bytes); Interrupt OUT for LED (1 byte, optional) |
| `usb_hid.Device.MOUSE` | Interrupt IN (4–7 bytes typical) |
| `usb_hid.Device.CONSUMER_CONTROL` | Interrupt IN (2–4 bytes typical) |

### Endpoint address assignment

CircuitPython assigns endpoint addresses in interface registration order, starting
from 1. The exact numbers are not deterministic from `boot.py` alone — they depend
on the CircuitPython firmware version and the order in which interfaces are
registered internally.

**Mark all endpoint addresses as uncertain in the profile description** when
generating from `boot.py` alone. To get authoritative numbers, capture a baseline
USB enumeration (plug in the device, capture the full descriptor exchange with
Cynthion or Wireshark/usbmon) and read the `bEndpointAddress` fields from the
Configuration Descriptor response.

### VID and PID

The KB2040 uses Adafruit's VID `0x239a` (decimal 9114). The PID depends on the
specific HID + CDC combination enabled in `boot.py`. Capture the enumeration or
look up the PID in the CircuitPython USB descriptor source for the specific
configuration.

---

## Example profiles

### KB2040 USB Frobnicator

The KB2040 traffic generator (`utilities/kb2040-traffic-gen/`) exposes two CDC
interfaces and a composite HID interface (keyboard, mouse, consumer control) as
configured in `boot.py`.

Endpoint addresses below are derived from CircuitPython's typical assignment order
for this configuration and should be verified against a baseline enumeration
capture before relying on them for enumeration-free decoding.

```json
{
  "device": {
    "vid": 9114,
    "pid": 32815,
    "name": "KB2040 USB Frobnicator",
    "speed": "full"
  },
  "configurations": [
    {
      "index": 1,
      "description": "Normal operation — CDC console + CDC data + composite HID",
      "interfaces": [
        {
          "number": 0,
          "class": 2,
          "description": "CDC console communication interface (REPL/log notifications)",
          "endpoints": [
            { "address": 129, "direction": "in", "type": "interrupt", "max_packet_size": 8 }
          ]
        },
        {
          "number": 1,
          "class": 10,
          "description": "CDC console data interface (REPL/log bulk pipe) — endpoint addresses guidance only",
          "endpoints": [
            { "address": 2,   "direction": "out", "type": "bulk", "max_packet_size": 64 },
            { "address": 130, "direction": "in",  "type": "bulk", "max_packet_size": 64 }
          ]
        },
        {
          "number": 2,
          "class": 2,
          "description": "CDC data communication interface (host_exerciser.py echo protocol notifications)",
          "endpoints": [
            { "address": 131, "direction": "in", "type": "interrupt", "max_packet_size": 8 }
          ]
        },
        {
          "number": 3,
          "class": 10,
          "description": "CDC data interface (host_exerciser.py echo bulk pipe) — endpoint addresses guidance only",
          "endpoints": [
            { "address": 3,   "direction": "out", "type": "bulk", "max_packet_size": 64 },
            { "address": 132, "direction": "in",  "type": "bulk", "max_packet_size": 64 }
          ]
        },
        {
          "number": 4,
          "class": 3,
          "description": "Composite HID (keyboard + mouse + consumer control) — endpoint addresses guidance only",
          "endpoints": [
            { "address": 133, "direction": "in",  "type": "interrupt", "max_packet_size": 8 },
            { "address": 4,   "direction": "out", "type": "interrupt", "max_packet_size": 8 }
          ]
        }
      ]
    }
  ]
}
```

**Notes on the KB2040 profile:**

- PID `32815` (0x802F) is a placeholder — verify the actual PID from a baseline
  enumeration capture or from the CircuitPython USB descriptor source for the
  keyboard+mouse+consumer+2×CDC combination.
- The HID Interrupt OUT endpoint (address 4) carries keyboard LED state from the
  host. It may not be present in all CircuitPython builds; verify before relying on it.
- The CDC notification endpoints (class 2, Interrupt IN) carry USB CDC control
  state changes. They typically carry minimal traffic and may generate NAKs during
  idle — this is normal behavior for CDC notification endpoints.
- To verify and correct endpoint addresses: plug the KB2040 into a Linux host and
  run `lsusb -v -d 239a:` to read the full descriptor, or capture a Cynthion
  enumeration session and extract addresses from the Configuration Descriptor
  response.
