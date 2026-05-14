#!/usr/bin/env python3
# Copyright 2026 contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""
gen_facedancer_clone.py — generate a Facedancer 3.x device emulation scaffold.

Reads decoded transfer JSON (from decode.py) to extract device identity and
endpoint descriptors, then emits a Facedancer 3.x Python script using the
confirmed @use_inner_classes_automatically class syntax.

Syntax verified against:
  https://github.com/greatscottgadgets/facedancer/blob/main/examples/template.py
  https://facedancer.readthedocs.io/

IMPORTANT: Facedancer 3.x requires Linux. macOS and Windows are not supported
for device emulation. Set BACKEND=cynthion before running the output script.

Usage:
    python3 gen_facedancer_clone.py capture.json -o clone_device.py
    python3 gen_facedancer_clone.py capture.json          # stdout
"""

import argparse
import json
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# Extract device + endpoint info from decoded captures
# ---------------------------------------------------------------------------

def _find_device_descriptor(transfers: List[dict]) -> Optional[dict]:
    for xfer in transfers:
        dec = xfer.get("decoded") or {}
        if dec.get("descriptor_type") == 1:
            return dec
    return None


def _find_configuration_descriptor(transfers: List[dict]) -> Optional[dict]:
    for xfer in transfers:
        dec = xfer.get("decoded") or {}
        if dec.get("descriptor_type") == 2:
            return dec
    return None


def _find_endpoint_descriptors(transfers: List[dict]) -> List[dict]:
    endpoints = []
    for xfer in transfers:
        dec = xfer.get("decoded") or {}
        if dec.get("descriptor_type") == 5:
            endpoints.append(dec)
    return endpoints


def _find_interface_descriptor(transfers: List[dict]) -> Optional[dict]:
    for xfer in transfers:
        dec = xfer.get("decoded") or {}
        if dec.get("descriptor_type") == 4:
            return dec
    return None


def _find_string(transfers: List[dict], index: int) -> Optional[str]:
    """Find the nth string descriptor from decoded transfers."""
    found = []
    for xfer in transfers:
        setup = xfer.get("setup") or {}
        dec   = xfer.get("decoded") or {}
        if dec.get("descriptor_type") == 3:
            wval = int(setup.get("wValue", "0x0000"), 16)
            desc_idx = wval & 0xFF
            if desc_idx == index:
                return dec.get("string")
            found.append((desc_idx, dec.get("string")))
    return None


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------

_TRANSFER_TYPE_MAP = {
    "control":     "USBTransferType.CONTROL",
    "bulk":        "USBTransferType.BULK",
    "interrupt":   "USBTransferType.INTERRUPT",
    "isochronous": "USBTransferType.ISOCHRONOUS",
}

_CLASS_MAP = {
    "0x00": "USBDeviceClass.UNSPECIFIED",
    "0x03": "USBDeviceClass.HID",
    "0x08": "USBDeviceClass.MASS_STORAGE",
    "0x0a": "USBDeviceClass.CDC_DATA",
    "0x02": "0x02",  # CDC Control
    "0xe0": "0xe0",  # Wireless
    "0xff": "USBDeviceClass.VENDOR_SPECIFIC",
}


def _hex_to_int(h: str, default: int = 0) -> int:
    try:
        return int(str(h).replace("0x", ""), 16)
    except (ValueError, AttributeError):
        return default


def _endpoint_class_name(ep_addr: str, direction: str, idx: int) -> str:
    dir_name = "In" if direction == "IN" else "Out"
    ep_num = _hex_to_int(ep_addr) & 0x0F
    return f"Endpoint{ep_num}{dir_name}"


def generate_clone(transfers: List[dict]) -> str:
    dev  = _find_device_descriptor(transfers) or {}
    cfg  = _find_configuration_descriptor(transfers) or {}
    intf = _find_interface_descriptor(transfers) or {}
    eps  = _find_endpoint_descriptors(transfers)

    vid = dev.get("idVendor", "0x1209")
    pid = dev.get("idProduct", "0x0001")
    bcd_device = dev.get("bcdDevice", "0x0001")
    bcd_usb    = dev.get("bcdUSB", "0x0200")
    dev_class  = dev.get("bDeviceClass", "0x00")
    dev_sub    = dev.get("bDeviceSubClass", "0x00")
    dev_proto  = dev.get("bDeviceProtocol", "0x00")
    max_pkt_ep0 = dev.get("bMaxPacketSize0", 64)

    mfr_idx     = dev.get("iManufacturer", 0)
    prod_idx    = dev.get("iProduct", 0)
    serial_idx  = dev.get("iSerialNumber", 0)
    mfr_str     = _find_string(transfers, mfr_idx) or "Manufacturer"
    prod_str    = _find_string(transfers, prod_idx) or "Product"
    serial_str  = _find_string(transfers, serial_idx) or "0001"

    max_power   = cfg.get("bMaxPower_mA", 100)
    self_powered = bool(_hex_to_int(str(cfg.get("bmAttributes", "0x80"))) & 0x40)
    remote_wakeup = bool(_hex_to_int(str(cfg.get("bmAttributes", "0x80"))) & 0x20)

    intf_class  = intf.get("bInterfaceClass", "0xff")
    intf_sub    = intf.get("bInterfaceSubClass", "0x00")
    intf_proto  = intf.get("bInterfaceProtocol", "0x00")

    class_const = _CLASS_MAP.get(str(intf_class).lower(), f"0x{_hex_to_int(str(intf_class)):02x}")

    lines = [
        "#!/usr/bin/env python3",
        "# Auto-generated by cynthion-reverse-engineer gen_facedancer_clone.py",
        "# Syntax: Facedancer 3.x (@use_inner_classes_automatically)",
        "#",
        "# REQUIREMENTS:",
        "#   pip install facedancer",
        "#   Linux only — macOS and Windows are not supported for device emulation",
        "#",
        "# USAGE:",
        "#   BACKEND=cynthion python3 clone_device.py",
        "#",
        "# Verified template syntax:",
        "#   https://github.com/greatscottgadgets/facedancer/blob/main/examples/template.py",
        "",
        "import logging",
        "",
        "from facedancer import main",
        "from facedancer import *",
        "from facedancer.classes import USBDeviceClass",
        "",
        "",
        "@use_inner_classes_automatically",
        "class ClonedDevice(USBDevice):",
        f'    """Cloned from {vid}/{pid} — {prod_str}"""',
        "",
        f"    vendor_id                : int = {vid}",
        f"    product_id               : int = {pid}",
        f"    device_revision          : int = {bcd_device}",
        f"    usb_spec_version         : int = {bcd_usb}",
        f"    device_class             : int = {_hex_to_int(str(dev_class))}",
        f"    device_subclass          : int = {_hex_to_int(str(dev_sub))}",
        f"    protocol_revision_number : int = {_hex_to_int(str(dev_proto))}",
        f"    max_packet_size_ep0      : int = {max_pkt_ep0}",
        f'    manufacturer_string      : str = "{mfr_str}"',
        f'    product_string           : str = "{prod_str}"',
        f'    serial_number_string     : str = "{serial_str}"',
        "",
        "    class ClonedConfiguration(USBConfiguration):",
        "        configuration_number   : int  = 1",
        f"        max_power              : int  = {max_power}",
        f"        self_powered           : bool = {self_powered}",
        f"        supports_remote_wakeup : bool = {remote_wakeup}",
        "",
        "        class ClonedInterface(USBInterface):",
        "            number          : int = 0",
        f"            class_number    : int = {class_const}",
        f"            subclass_number : int = {_hex_to_int(str(intf_sub))}",
        f"            protocol_number : int = {_hex_to_int(str(intf_proto))}",
        "",
    ]

    if not eps:
        # No endpoint descriptors found — emit stubs
        lines += [
            "            # TODO: add endpoint classes here.",
            "            # Run decode.py with --phase enumeration to find endpoint descriptors.",
            "            # Example:",
            "            # class BulkInEndpoint(USBEndpoint):",
            "            #     number        : int            = 1",
            "            #     direction     : USBDirection   = USBDirection.IN",
            "            #     transfer_type : USBTransferType = USBTransferType.BULK",
            "            #     max_packet_size : int          = 64",
            "            #     def handle_data_requested(self):",
            "            #         self.send(b'\\x00' * 8)",
            "",
        ]
    else:
        for ep in eps:
            ep_addr = str(ep.get("bEndpointAddress", "0x81"))
            direction = ep.get("direction", "IN")
            ep_num  = _hex_to_int(ep_addr) & 0x0F
            ttype   = ep.get("transfer_type", "bulk")
            mps     = ep.get("wMaxPacketSize", 64)
            interval = ep.get("bInterval", 0)
            dir_const = "USBDirection.IN" if direction == "IN" else "USBDirection.OUT"
            type_const = _TRANSFER_TYPE_MAP.get(ttype, "USBTransferType.BULK")
            cls_name = _endpoint_class_name(ep_addr, direction, ep_num)

            lines.append(f"            class {cls_name}(USBEndpoint):")
            lines.append(f"                number          : int             = {ep_num}")
            lines.append(f"                direction       : USBDirection    = {dir_const}")
            lines.append(f"                transfer_type   : USBTransferType = {type_const}")
            lines.append(f"                max_packet_size : int             = {mps}")
            if interval:
                lines.append(f"                interval        : int             = {interval}")
            lines.append("")

            if direction == "IN":
                lines.append("                def handle_data_requested(self):")
                lines.append(f"                    # TODO: send real data for EP{ep_num} IN")
                lines.append(f"                    self.send(b'\\x00' * {min(mps, 8)})")
            else:
                lines.append("                def handle_data_received(self, data):")
                lines.append(f"                    # TODO: handle data for EP{ep_num} OUT")
                lines.append(f"                    logging.info(f'EP{ep_num} OUT received: {{data.hex()}}')")
            lines.append("")

    # Vendor request handler stub
    lines += [
        "    # --- Vendor request handlers ---",
        "    # Add handlers for class/vendor control requests here.",
        "    # Example:",
        "    # @vendor_request_handler(number=0x01, direction=USBDirection.IN)",
        "    # @to_device",
        "    # def handle_vendor_in(self, request: USBControlRequest):",
        "    #     request.reply(b'\\x00')",
        "",
        "",
        'if __name__ == "__main__":',
        "    main(ClonedDevice)",
        "",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Generate a Facedancer 3.x clone script from a decoded capture."
    )
    p.add_argument("capture", help="JSON from decode.py --format json")
    p.add_argument("-o", "--output", help="Output .py file (default: stdout)")
    args = p.parse_args()

    with open(args.capture) as f:
        transfers = json.load(f)

    script = generate_clone(transfers)

    if args.output:
        Path(args.output).write_text(script)
        print(f"Written to {args.output}")
        print("Run with:  BACKEND=cynthion python3 " + args.output)
        print("Note: Facedancer 3.x device emulation requires Linux.")
    else:
        print(script)


if __name__ == "__main__":
    main()
