#!/usr/bin/env python3
# Copyright 2026 contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""
generate_synthetic.py — create synthetic USB capture JSONs for the worked example.

Simulates two captures of a simple vendor-specific USB device:

  Device: "Example Widget"  VID=0x1234  PID=0xabcd
  Protocol: 4-byte OUT commands on EP1, 4-byte IN responses on EP1
    Byte 0: opcode   (0x01=STATUS_QUERY, 0x02=SET_BRIGHTNESS)
    Byte 1: argument (brightness level for 0x02; 0x00 for 0x01)
    Byte 2: reserved (always 0x00)
    Byte 3: sequence counter (increments per transaction)

  Response format (EP1 IN):
    Byte 0: status   (0x00=OK)
    Byte 1: data     (current brightness for STATUS_QUERY; echo arg for SET_BRIGHTNESS)
    Byte 2: reserved (0x00)
    Byte 3: sequence counter (echoes command seq)

Outputs:
  status_query.json   — 10 STATUS_QUERY transactions (opcode 0x01)
  set_brightness.json — 10 SET_BRIGHTNESS transactions (opcode 0x02, arg=0x80)
"""

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Synthetic device identity (as decode.py Transfer.to_dict() format)
# ---------------------------------------------------------------------------

DEVICE_DESCRIPTOR_XFER = {
    "index": 0,
    "type": "control",
    "addr": 0,
    "endp": 0,
    "direction": "IN",
    "time_s": 0.000002,
    "payload_len": 18,
    "payload_hex": "120100020000004034120cdcab0102030001",
    "setup": {
        "bmRequestType": "0x80",
        "direction": "IN",
        "type": "standard",
        "recipient": "device",
        "bRequest": 6,
        "wValue": "0x0100",
        "wIndex": 0,
        "wLength": 64,
    },
    "decoded": {
        "descriptor_type": 1,
        "descriptor_name": "Device",
        "bLength": 18,
        "bDescriptorType": 1,
        "bcdUSB": "0x0200",
        "bDeviceClass": "0x00",
        "bDeviceSubClass": "0x00",
        "bDeviceProtocol": "0x00",
        "bMaxPacketSize0": 64,
        "idVendor": "0x1234",
        "idProduct": "0xabcd",
        "bcdDevice": "0x0100",
        "iManufacturer": 1,
        "iProduct": 2,
        "iSerialNumber": 3,
        "bNumConfigurations": 1,
    },
}

MANUFACTURER_STRING_XFER = {
    "index": 1,
    "type": "control",
    "addr": 0,
    "endp": 0,
    "direction": "IN",
    "time_s": 0.000010,
    "payload_len": 30,
    "payload_hex": "1e0357006900640067006500740020004c00740064002e00",
    "setup": {
        "bmRequestType": "0x80",
        "direction": "IN",
        "type": "standard",
        "recipient": "device",
        "bRequest": 6,
        "wValue": "0x0301",
        "wIndex": 0x0409,
        "wLength": 255,
    },
    "decoded": {
        "descriptor_type": 3,
        "descriptor_name": "String",
        "bLength": 30,
        "bDescriptorType": 3,
        "string": "Widget Ltd.",
    },
}

PRODUCT_STRING_XFER = {
    "index": 2,
    "type": "control",
    "addr": 0,
    "endp": 0,
    "direction": "IN",
    "time_s": 0.000018,
    "payload_len": 30,
    "payload_hex": "1e0345006d0070006c00650020005700690064006700650074",
    "setup": {
        "bmRequestType": "0x80",
        "direction": "IN",
        "type": "standard",
        "recipient": "device",
        "bRequest": 6,
        "wValue": "0x0302",
        "wIndex": 0x0409,
        "wLength": 255,
    },
    "decoded": {
        "descriptor_type": 3,
        "descriptor_name": "String",
        "bLength": 30,
        "bDescriptorType": 3,
        "string": "Example Widget",
    },
}

ENDPOINT_DESCRIPTOR_XFER = {
    "index": 3,
    "type": "control",
    "addr": 0,
    "endp": 0,
    "direction": "IN",
    "time_s": 0.000025,
    "payload_len": 7,
    "payload_hex": "07058104000000",
    "setup": {
        "bmRequestType": "0x80",
        "direction": "IN",
        "type": "standard",
        "recipient": "device",
        "bRequest": 6,
        "wValue": "0x0200",
        "wIndex": 0,
        "wLength": 255,
    },
    "decoded": {
        "descriptor_type": 5,
        "descriptor_name": "Endpoint",
        "bLength": 7,
        "bDescriptorType": 5,
        "bEndpointAddress": "0x81",
        "direction": "IN",
        "bmAttributes": "0x02",
        "transfer_type": "bulk",
        "wMaxPacketSize": 64,
        "bInterval": 0,
    },
}

SET_CONFIG_XFER = {
    "index": 4,
    "type": "control",
    "addr": 0,
    "endp": 0,
    "direction": "OUT",
    "time_s": 0.000030,
    "payload_len": 0,
    "payload_hex": None,
    "setup": {
        "bmRequestType": "0x00",
        "direction": "OUT",
        "type": "standard",
        "recipient": "device",
        "bRequest": 9,
        "wValue": "0x0001",
        "wIndex": 0,
        "wLength": 0,
    },
    "decoded": {
        "request": "SET_CONFIGURATION",
        "value": 1,
    },
}

ENUMERATION = [
    DEVICE_DESCRIPTOR_XFER,
    MANUFACTURER_STRING_XFER,
    PRODUCT_STRING_XFER,
    ENDPOINT_DESCRIPTOR_XFER,
    SET_CONFIG_XFER,
]

# ---------------------------------------------------------------------------
# Bulk transaction generator
# ---------------------------------------------------------------------------


def make_bulk_out(idx, xfer_idx, opcode, arg0, seq):
    payload = bytes([opcode, arg0, 0x00, seq])
    return {
        "index": xfer_idx,
        "type": "bulk",
        "addr": 0,
        "endp": 1,
        "direction": "OUT",
        "time_s": round(0.001 * (idx + 1), 6),
        "payload_len": 4,
        "payload_hex": payload.hex(),
        "setup": None,
        "decoded": None,
    }


def make_bulk_in(idx, xfer_idx, status, data0, seq):
    payload = bytes([status, data0, 0x00, seq])
    return {
        "index": xfer_idx,
        "type": "bulk",
        "addr": 0,
        "endp": 1,
        "direction": "IN",
        "time_s": round(0.001 * (idx + 1) + 0.0001, 6),
        "payload_len": 4,
        "payload_hex": payload.hex(),
        "setup": None,
        "decoded": None,
    }


def make_capture(opcode, arg0, response_data0, n=10):
    xfers = list(ENUMERATION)
    base = len(xfers)
    for i in range(n):
        seq = i & 0xFF
        xfers.append(make_bulk_out(i, base + i * 2,     opcode, arg0,        seq))
        xfers.append(make_bulk_in (i, base + i * 2 + 1, 0x00,   response_data0, seq))
        # Re-index
        xfers[-2]["index"] = base + i * 2
        xfers[-1]["index"] = base + i * 2 + 1
    return xfers


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    out_dir = Path(__file__).parent

    # Capture A: STATUS_QUERY (opcode 0x01)
    # Response data0 = current brightness = 0x40
    status_query = make_capture(opcode=0x01, arg0=0x00, response_data0=0x40)
    p = out_dir / "status_query.json"
    p.write_text(json.dumps(status_query, indent=2))
    print(f"Written: {p}")

    # Capture B: SET_BRIGHTNESS (opcode 0x02, arg0=0x80)
    # Response echoes arg0
    set_brightness = make_capture(opcode=0x02, arg0=0x80, response_data0=0x80)
    p = out_dir / "set_brightness.json"
    p.write_text(json.dumps(set_brightness, indent=2))
    print(f"Written: {p}")

    print("\nSynthetic captures created. Run the pipeline:")
    print("  cd example/")
    print("  python3 generate_synthetic.py")
    print("  python3 ../scripts/diff_transactions.py \\")
    print("    status_query.json set_brightness.json \\")
    print("    --label status_query set_brightness --format markdown")
    print("  python3 ../scripts/infer_commands.py \\")
    print("    status_query.json set_brightness.json \\")
    print("    --label status_query set_brightness > hypothesis.json")
    print("  python3 ../scripts/gen_replay.py hypothesis.json status_query.json -o replay.py")
    print("  python3 ../scripts/gen_facedancer_clone.py status_query.json -o clone.py")
    print("  python3 ../scripts/gen_protocol_doc.py hypothesis.json \\")
    print("    --capture status_query.json status_query \\")
    print("    --capture set_brightness.json set_brightness \\")
    print("    -o protocol.md")


if __name__ == "__main__":
    main()
