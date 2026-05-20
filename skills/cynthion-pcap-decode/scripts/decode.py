#!/usr/bin/env python3
# Copyright 2026 contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""
decode.py — USB pcap decoder for Packetry/Cynthion captures (LINKTYPE_USB_2_0 = 288).

Primary path:  tshark (Wireshark usbll dissector) — streams packets via -T ek
Fallback path: native Python pcap reader (no tshark required)

Usage:
    python3 decode.py capture.pcap
    python3 decode.py capture.pcap --format transcript
    python3 decode.py capture.pcap --format markdown
    python3 decode.py capture.pcap --filter address=2
    python3 decode.py capture.pcap --filter endpoint=1 --filter transfer-type=interrupt
    python3 decode.py capture.pcap --phase enumeration
    python3 decode.py capture.pcap --time-range 0.0,1.5
    python3 decode.py capture.pcap --native   # force fallback decoder
"""

import argparse
import json
import struct
import subprocess
from dataclasses import dataclass, field
from typing import Iterator, List, Optional, Tuple

# ---------------------------------------------------------------------------
# PID constants (the raw 8-bit USB PID byte)
# ---------------------------------------------------------------------------

class PID:
    SOF   = 165  # 0xa5
    SETUP = 45   # 0x2d
    OUT   = 225  # 0xe1
    IN    = 105  # 0x69
    DATA0 = 195  # 0xc3
    DATA1 = 75   # 0x4b
    DATA2 = 135  # 0x87
    MDATA = 15   # 0x0f
    ACK   = 210  # 0xd2
    NAK   = 90   # 0x5a
    STALL = 30   # 0x1e
    NYET  = 150  # 0x96
    PRE   = 60   # 0x3c
    SPLIT = 120  # 0x78
    PING  = 180  # 0xb4

PID_NAMES      = {v: k for k, v in vars(PID).items() if not k.startswith("_")}
TOKEN_PIDS     = {PID.SETUP, PID.OUT, PID.IN, PID.SOF}
DATA_PIDS      = {PID.DATA0, PID.DATA1, PID.DATA2, PID.MDATA}
HANDSHAKE_PIDS = {PID.ACK, PID.NAK, PID.STALL, PID.NYET}

LINKTYPE_USB_2_0 = 288
PCAP_MAGIC_LE    = 0xa1b2c3d4
PCAP_MAGIC_NS    = 0xa1b23c4d  # nanosecond variant — Packetry uses this

# Standard descriptor types
DESC = {
    0x01: "Device",       0x02: "Configuration", 0x03: "String",
    0x04: "Interface",    0x05: "Endpoint",       0x06: "DeviceQualifier",
    0x21: "HID",          0x22: "HIDReport",      0x23: "HIDPhysical",
}

# Standard requests (bRequest)
REQ_GET_DESCRIPTOR   = 0x06
REQ_SET_ADDRESS      = 0x05
REQ_SET_CONFIGURATION = 0x09
REQ_GET_CONFIGURATION = 0x08

# MSC signatures
CBW_SIG = 0x43425355
CSW_SIG = 0x53425355

# CDC-ACM request names
CDC_REQUESTS = {
    0x00: "SEND_ENCAPSULATED_COMMAND", 0x01: "GET_ENCAPSULATED_RESPONSE",
    0x20: "SET_LINE_CODING",           0x21: "GET_LINE_CODING",
    0x22: "SET_CONTROL_LINE_STATE",    0x23: "SEND_BREAK",
}

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Packet:
    frame_no: int
    time_s: float          # seconds relative to first packet
    time_abs: str          # ISO timestamp string
    pid: int
    pid_name: str
    addr: Optional[int]    # device address (token packets)
    endp: Optional[int]    # endpoint number (token packets)
    data: Optional[bytes]  # payload bytes, CRC stripped (data packets)
    src: str               # "host" or "addr.endp"
    dst: str


@dataclass
class Transaction:
    index: int
    time_s: float
    token: Packet
    data_pkt: Optional[Packet]
    handshake: Optional[Packet]
    addr: int
    endp: int

    @property
    def direction(self) -> str:
        return {PID.IN: "IN", PID.OUT: "OUT", PID.SETUP: "SETUP"}.get(self.token.pid, "?")

    @property
    def successful(self) -> bool:
        return self.handshake is not None and self.handshake.pid == PID.ACK

    @property
    def payload(self) -> Optional[bytes]:
        return self.data_pkt.data if self.data_pkt else None


@dataclass
class Transfer:
    index: int
    type: str            # control / bulk / interrupt / iso
    addr: int
    endp: int
    direction: str       # IN / OUT
    time_s: float
    transactions: List[Transaction] = field(default_factory=list)
    payload: Optional[bytes] = None   # reassembled data payload
    setup: Optional[dict] = None      # decoded SETUP packet (control only)
    decoded: Optional[dict] = None    # descriptor or class decode

    def to_dict(self) -> dict:
        d = {
            "index": self.index, "type": self.type,
            "addr": self.addr, "endp": self.endp,
            "direction": self.direction, "time_s": round(self.time_s, 9),
            "payload_len": len(self.payload) if self.payload else 0,
            "payload_hex": self.payload.hex() if self.payload else None,
        }
        if self.setup:
            d["setup"] = self.setup
        if self.decoded:
            d["decoded"] = self.decoded
        return d


# ---------------------------------------------------------------------------
# Layer 1 — Packet streaming
# ---------------------------------------------------------------------------

def _ek_int(s: str) -> int:
    """Parse a tshark -T ek integer field. tshark emits some fields as decimal
    (e.g. "12") and others as 0x-prefixed hex (e.g. usbll.pid as "0xa5" in
    tshark 4.2). Accept either form."""
    return int(s, 16) if s.lower().startswith("0x") else int(s)


def _ek_packet(doc: dict) -> Optional[Packet]:
    """Parse one tshark -T ek document line into a Packet."""
    layers = doc.get("layers", {})
    usbll = layers.get("usbll")
    frame = layers.get("frame", {})
    if usbll is None:
        return None

    pid_str = usbll.get("usbll_usbll_pid")
    if pid_str is None:
        return None
    pid = _ek_int(pid_str)

    addr_s = usbll.get("usbll_usbll_device_addr")
    endp_s = usbll.get("usbll_usbll_endp")
    addr = _ek_int(addr_s) if addr_s is not None else None
    endp = _ek_int(endp_s) if endp_s is not None else None

    raw_data = usbll.get("usbll_usbll_data")
    data = bytes(int(b, 16) for b in raw_data.split(":")) if raw_data else None

    src = usbll.get("usbll_usbll_src") or ""
    dst = usbll.get("usbll_usbll_dst") or ""
    # In -T ek, usbll_usbll_addr may be a list ["host","addr.ep"]; ignore it.

    frame_no  = int(frame.get("frame_frame_number", 0))
    time_abs  = frame.get("frame_frame_time_epoch", "")
    time_s    = float(frame.get("frame_frame_time_relative", 0))

    return Packet(
        frame_no=frame_no, time_s=time_s, time_abs=time_abs,
        pid=pid, pid_name=PID_NAMES.get(pid, f"UNK({pid:#04x})"),
        addr=addr, endp=endp, data=data, src=src, dst=dst,
    )


def stream_packets_tshark(pcap_path: str) -> Iterator[Packet]:
    """Stream Packets from tshark -T ek output (one JSON document per packet)."""
    cmd = ["tshark", "-r", pcap_path, "-T", "ek"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    try:
        while True:
            # -T ek alternates: index line, then document line
            idx = proc.stdout.readline()
            if not idx:
                break
            doc_line = proc.stdout.readline()
            if not doc_line:
                break
            try:
                doc = json.loads(doc_line)
            except json.JSONDecodeError:
                continue
            pkt = _ek_packet(doc)
            if pkt is not None:
                yield pkt
    finally:
        proc.stdout.close()
        proc.wait()


def _token_addr_endp(raw: bytes) -> Tuple[int, int]:
    """Decode the addr[6:0]+endp[3:0] fields from a token packet (bits after PID)."""
    if len(raw) < 3:
        return 0, 0
    word = raw[1] | (raw[2] << 8)
    return word & 0x7F, (word >> 7) & 0x0F


def stream_packets_native(pcap_path: str) -> Iterator[Packet]:
    """Stream Packets by reading the pcap file directly — no tshark required."""
    with open(pcap_path, "rb") as f:
        magic = struct.unpack("<I", f.read(4))[0]
        if magic not in (PCAP_MAGIC_LE, PCAP_MAGIC_NS):
            raise ValueError(f"Unrecognised pcap magic: {magic:#010x}")
        ns = (magic == PCAP_MAGIC_NS)
        _, _, _, _, _, linktype = struct.unpack("<HHiIII", f.read(20))
        if linktype != LINKTYPE_USB_2_0:
            raise ValueError(f"Expected LINKTYPE_USB_2_0 (288), got {linktype}")

        t0: Optional[float] = None
        frame_no = 0
        last_token_pid = PID.OUT  # tracks direction for native data-packet src/dst

        while True:
            hdr = f.read(16)
            if len(hdr) < 16:
                break
            ts_sec, ts_frac, incl_len, _ = struct.unpack("<IIII", hdr)
            raw = f.read(incl_len)
            if not raw:
                continue

            frame_no += 1
            abs_s = ts_sec + ts_frac / (1e9 if ns else 1e6)
            if t0 is None:
                t0 = abs_s
            time_s = abs_s - t0

            pid = raw[0]
            pid_name = PID_NAMES.get(pid, f"UNK({pid:#04x})")
            addr = endp = None
            data = None
            src = dst = ""

            if pid in TOKEN_PIDS and len(raw) >= 3:
                addr, endp = _token_addr_endp(raw)
                src, dst = "host", f"{addr}.{endp}"
                last_token_pid = pid
            elif pid in DATA_PIDS and len(raw) >= 3:
                data = raw[1:-2]  # strip 2-byte CRC16
                if last_token_pid == PID.IN:
                    src, dst = "device", "host"
                else:
                    src, dst = "host", "device"

            yield Packet(
                frame_no=frame_no, time_s=time_s,
                time_abs=f"{abs_s:.9f}", pid=pid, pid_name=pid_name,
                addr=addr, endp=endp, data=data, src=src, dst=dst,
            )


def stream_packets(pcap_path: str, force_native: bool = False) -> Iterator[Packet]:
    if not force_native:
        try:
            subprocess.run(["tshark", "--version"], capture_output=True, check=True)
            yield from stream_packets_tshark(pcap_path)
            return
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
    yield from stream_packets_native(pcap_path)


# ---------------------------------------------------------------------------
# Layer 2 — Transaction grouping
# ---------------------------------------------------------------------------

def stream_transactions(packets: Iterator[Packet]) -> Iterator[Transaction]:
    """Group packet stream into transactions: token [+ data] [+ handshake]."""
    idx = 0
    pending_token: Optional[Packet] = None
    pending_data:  Optional[Packet] = None

    def emit(token, data, hs):
        nonlocal idx
        yield Transaction(
            index=idx, time_s=token.time_s, token=token, data_pkt=data,
            handshake=hs, addr=token.addr or 0, endp=token.endp or 0,
        )
        idx += 1

    for pkt in packets:
        if pkt.pid == PID.SOF:
            continue  # SOF = frame delimiter, not a transaction component

        if pkt.pid in TOKEN_PIDS:
            if pending_token is not None:
                yield from emit(pending_token, pending_data, None)
            pending_token = pkt
            pending_data  = None

        elif pkt.pid in DATA_PIDS:
            if pending_token is not None:
                pending_data = pkt

        elif pkt.pid in HANDSHAKE_PIDS:
            if pending_token is not None:
                yield from emit(pending_token, pending_data, pkt)
                pending_token = None
                pending_data  = None

    if pending_token is not None:
        yield from emit(pending_token, pending_data, None)


# ---------------------------------------------------------------------------
# Layer 3 — Transfer reassembly
# ---------------------------------------------------------------------------

def _reassemble(txns: List[Transaction]) -> Optional[bytes]:
    """Concatenate data payloads from successful data-stage transactions."""
    chunks = [tx.payload for tx in txns if tx.successful and tx.payload]
    return b"".join(chunks) if chunks else None


def stream_transfers(transactions: Iterator[Transaction]) -> Iterator[Transfer]:
    """Reassemble transactions into transfers.

    Control transfers: SETUP → optional data stage → status (ZLP).
    Bulk/interrupt:    each successful transaction is its own transfer.
    """
    xfer_idx = 0
    pending: dict = {}  # (addr, endp) -> list[Transaction] for in-progress control xfers

    for tx in transactions:
        key = (tx.addr, tx.endp)

        if tx.token.pid == PID.SETUP:
            pending[key] = [tx]
            continue

        if key in pending:
            pending[key].append(tx)
            xfer_txns = pending[key]
            # Status stage: a ZLP IN or OUT that ACKs, following the data stage.
            last = xfer_txns[-1]
            if (last.token.pid != PID.SETUP and last.successful
                    and (last.payload is None or len(last.payload) == 0)):
                txns = pending.pop(key)
                setup_data = txns[0].payload
                data_stage = txns[1:-1]
                payload = _reassemble(data_stage)
                # Direction: if setup bmRequestType bit7=1 the device sends data (IN)
                direction = "IN"
                if setup_data and len(setup_data) >= 1:
                    direction = "IN" if (setup_data[0] & 0x80) else "OUT"
                xfer = Transfer(
                    index=xfer_idx, type="control",
                    addr=tx.addr, endp=tx.endp, direction=direction,
                    time_s=txns[0].time_s, transactions=txns,
                    payload=payload,
                    setup=_decode_setup(setup_data),
                )
                xfer.decoded = decode_content(xfer.setup, xfer.payload)
                yield xfer
                xfer_idx += 1
            continue

        # Bulk / interrupt: one transfer per successful data-bearing transaction
        if tx.successful and tx.payload:
            yield Transfer(
                index=xfer_idx,
                type="bulk",       # heuristic; interrupt requires endpoint descriptor
                addr=tx.addr, endp=tx.endp, direction=tx.direction,
                time_s=tx.time_s, transactions=[tx], payload=tx.payload,
            )
            xfer_idx += 1


# ---------------------------------------------------------------------------
# Layer 4 — Descriptor and class decoding
# ---------------------------------------------------------------------------

def _decode_setup(data: Optional[bytes]) -> Optional[dict]:
    if not data or len(data) < 8:
        return None
    bm, req, v_lo, v_hi, i_lo, i_hi, l_lo, l_hi = data[:8]
    wValue = v_lo | (v_hi << 8)
    wIndex = i_lo | (i_hi << 8)
    wLength = l_lo | (l_hi << 8)
    return {
        "bmRequestType": f"{bm:#04x}",
        "direction":  "IN" if (bm & 0x80) else "OUT",
        "type":       ["standard", "class", "vendor", "reserved"][(bm >> 5) & 0x03],
        "recipient":  ["device", "interface", "endpoint", "other"][min(bm & 0x1F, 3)],
        "bRequest":   req,
        "wValue":     f"{wValue:#06x}",
        "wIndex":     wIndex,
        "wLength":    wLength,
    }


def _decode_device_descriptor(d: bytes) -> dict:
    if len(d) < 18:
        return {"error": "truncated", "raw": d.hex()}
    f = struct.unpack_from("<BBHBBBBHHHBBBB", d)
    return {
        "bLength": f[0], "bDescriptorType": f[1], "bcdUSB": f"{f[2]:#06x}",
        "bDeviceClass": f"{f[3]:#04x}", "bDeviceSubClass": f"{f[4]:#04x}",
        "bDeviceProtocol": f"{f[5]:#04x}", "bMaxPacketSize0": f[6],
        "idVendor": f"{f[7]:#06x}", "idProduct": f"{f[8]:#06x}",
        "bcdDevice": f"{f[9]:#06x}",
        "iManufacturer": f[10], "iProduct": f[11],
        "iSerialNumber": f[12], "bNumConfigurations": f[13],
    }


def _decode_config_descriptor(d: bytes) -> dict:
    if len(d) < 9:
        return {"error": "truncated", "raw": d.hex()}
    bL, bT, wT, bNI, bCV, iC, bmA, bMP = struct.unpack_from("<BBHBBBBB", d)
    return {
        "bLength": bL, "bDescriptorType": bT, "wTotalLength": wT,
        "bNumInterfaces": bNI, "bConfigurationValue": bCV,
        "iConfiguration": iC, "bmAttributes": f"{bmA:#04x}",
        "bMaxPower_mA": bMP * 2,
    }


def _decode_interface_descriptor(d: bytes) -> dict:
    if len(d) < 9:
        return {"error": "truncated", "raw": d.hex()}
    f = struct.unpack_from("<BBBBBBBBB", d)
    return {
        "bLength": f[0], "bDescriptorType": f[1], "bInterfaceNumber": f[2],
        "bAlternateSetting": f[3], "bNumEndpoints": f[4],
        "bInterfaceClass": f"{f[5]:#04x}", "bInterfaceSubClass": f"{f[6]:#04x}",
        "bInterfaceProtocol": f"{f[7]:#04x}", "iInterface": f[8],
    }


def _decode_endpoint_descriptor(d: bytes) -> dict:
    if len(d) < 7:
        return {"error": "truncated", "raw": d.hex()}
    bL, bT, bA, bmA, mL, mH, bI = struct.unpack_from("<BBBBBBB", d)
    return {
        "bLength": bL, "bDescriptorType": bT,
        "bEndpointAddress": f"{bA:#04x}",
        "direction": "IN" if (bA & 0x80) else "OUT",
        "bmAttributes": f"{bmA:#04x}",
        "transfer_type": ["control", "isochronous", "bulk", "interrupt"][bmA & 0x03],
        "wMaxPacketSize": mL | (mH << 8), "bInterval": bI,
    }


def _decode_string_descriptor(d: bytes) -> dict:
    if len(d) < 2:
        return {"error": "truncated"}
    bL, bT = d[0], d[1]
    payload = d[2:]
    if not payload:
        return {"bLength": bL, "bDescriptorType": bT}
    try:
        return {"bLength": bL, "bDescriptorType": bT, "string": payload.decode("utf-16-le")}
    except UnicodeDecodeError:
        n = len(payload) // 2
        langs = list(struct.unpack_from(f"<{n}H", payload))
        return {"bLength": bL, "bDescriptorType": bT,
                "language_ids": [f"{l:#06x}" for l in langs]}


_DESCRIPTOR_DECODERS = {
    0x01: _decode_device_descriptor,
    0x02: _decode_config_descriptor,
    0x04: _decode_interface_descriptor,
    0x05: _decode_endpoint_descriptor,
    0x03: _decode_string_descriptor,
}


def _decode_msc(d: bytes) -> dict:
    if len(d) >= 31:
        sig = struct.unpack_from("<I", d)[0]
        if sig == CBW_SIG:
            _, tag, xlen, flags, lun, cblen = struct.unpack_from("<IIIBBB", d)
            return {"class": "MSC CBW", "tag": f"{tag:#010x}",
                    "transfer_length": xlen,
                    "direction": "IN" if flags & 0x80 else "OUT",
                    "lun": lun, "cb": d[15:15 + cblen].hex()}
    if len(d) >= 13:
        sig = struct.unpack_from("<I", d)[0]
        if sig == CSW_SIG:
            _, tag, residue, status = struct.unpack_from("<IIIB", d)
            return {"class": "MSC CSW", "tag": f"{tag:#010x}",
                    "data_residue": residue,
                    "status": ["passed", "failed", "phase_error"][min(status, 2)]}
    return {"class": "MSC data", "raw": d.hex()}


def _decode_cdc_acm(setup: dict, payload: Optional[bytes]) -> dict:
    req = setup.get("bRequest", 0)
    result: dict = {"class": "CDC-ACM", "request": CDC_REQUESTS.get(req, f"req({req:#04x})")}
    if req == 0x20 and payload and len(payload) >= 7:
        rate, stop, parity, bits = struct.unpack_from("<IBBB", payload)
        result["line_coding"] = {"baud_rate": rate, "stop_bits": stop,
                                  "parity": parity, "data_bits": bits}
    elif req == 0x22:
        wval = int(setup.get("wValue", "0x0"), 16)
        result["dtr"] = bool(wval & 0x01)
        result["rts"] = bool(wval & 0x02)
    return result


def _decode_midi(d: bytes) -> dict:
    events = []
    for i in range(0, len(d) - 3, 4):
        h = d[i]
        events.append({"cable": (h >> 4) & 0x0F, "cin": h & 0x0F,
                        "bytes": d[i + 1:i + 4].hex()})
    return {"class": "MIDI", "events": events}


def decode_content(setup: Optional[dict], payload: Optional[bytes]) -> Optional[dict]:
    """Decode the data payload of a control transfer given its SETUP fields."""
    if not setup or not payload:
        return None

    req  = setup.get("bRequest", 0)
    kind = setup.get("type", "standard")

    if kind == "standard":
        if req == REQ_GET_DESCRIPTOR:
            wval  = int(setup.get("wValue", "0x0000"), 16)
            dtype = (wval >> 8) & 0xFF
            dec   = _DESCRIPTOR_DECODERS.get(dtype)
            base  = {"descriptor_type": dtype, "descriptor_name": DESC.get(dtype, f"{dtype:#04x}")}
            return {**base, **(dec(payload) if dec else {"raw": payload.hex()})}
        if req == REQ_SET_ADDRESS:
            return {"request": "SET_ADDRESS", "new_address": int(setup.get("wValue", "0x0"), 16)}
        if req in (REQ_SET_CONFIGURATION, REQ_GET_CONFIGURATION):
            return {"request": "SET_CONFIGURATION" if req == REQ_SET_CONFIGURATION else "GET_CONFIGURATION",
                    "value": int(setup.get("wValue", "0x0"), 16)}

    elif kind == "class":
        if len(payload) in (31, 13):
            sig = struct.unpack_from("<I", payload)[0] if len(payload) >= 4 else 0
            if sig in (CBW_SIG, CSW_SIG):
                return _decode_msc(payload)
        req_name = CDC_REQUESTS.get(req)
        if req_name:
            return _decode_cdc_acm(setup, payload)
        if len(payload) % 4 == 0 and len(payload) >= 4:
            return _decode_midi(payload)
        return {"class": "class-specific", "raw": payload[:64].hex()}

    elif kind == "vendor":
        return {"class": "vendor-specific", "raw": payload[:64].hex()}

    return None


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

class Filters:
    def __init__(self, args):
        self.addr: Optional[int] = None
        self.endp: Optional[int] = None
        self.transfer_type: Optional[str] = None
        self.time_start: Optional[float] = None
        self.time_end:   Optional[float] = None
        self.phase_enum: bool = getattr(args, "phase", None) == "enumeration"

        for spec in getattr(args, "filter", []) or []:
            k, _, v = spec.partition("=")
            if k == "address":
                self.addr = int(v)
            elif k == "endpoint":
                self.endp = int(v)
            elif k == "transfer-type":
                self.transfer_type = v

        tr = getattr(args, "time_range", None)
        if tr:
            parts = tr.split(",")
            self.time_start = float(parts[0]) if parts[0] else None
            self.time_end   = float(parts[1]) if len(parts) > 1 and parts[1] else None

    def match(self, xfer: Transfer) -> bool:
        if self.addr is not None and xfer.addr != self.addr:
            return False
        if self.endp is not None and xfer.endp != self.endp:
            return False
        if self.transfer_type and xfer.type != self.transfer_type:
            return False
        if self.time_start is not None and xfer.time_s < self.time_start:
            return False
        if self.time_end is not None and xfer.time_s > self.time_end:
            return False
        if self.phase_enum:
            if xfer.type != "control" or xfer.endp != 0:
                return False
            req = (xfer.setup or {}).get("bRequest", -1)
            if req not in (REQ_GET_DESCRIPTOR, REQ_SET_ADDRESS, REQ_SET_CONFIGURATION):
                return False
        return True


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def _hex_dump(data: bytes, indent: int = 4) -> str:
    pad = " " * indent
    lines = []
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        hex_part  = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{pad}{i:04x}  {hex_part:<48}  {ascii_part}")
    return "\n".join(lines)


def format_json(transfers: List[Transfer]) -> str:
    return json.dumps([x.to_dict() for x in transfers], indent=2)


def format_transcript(transfers: List[Transfer]) -> str:
    lines = []
    for xfer in transfers:
        hdr = (f"[{xfer.index:4d}] t={xfer.time_s:.6f}s  "
               f"{xfer.type.upper():9s} addr={xfer.addr} ep={xfer.endp} "
               f"{xfer.direction}")
        lines.append(hdr)
        if xfer.setup:
            s = xfer.setup
            lines.append(f"       SETUP  req={s['bRequest']:#04x} "
                         f"type={s['type']} wValue={s['wValue']} wLength={s['wLength']}")
        if xfer.decoded:
            lines.append(f"       -> {xfer.decoded}")
        if xfer.payload and not xfer.decoded:
            lines.append(f"       {len(xfer.payload)} bytes:")
            lines.append(_hex_dump(xfer.payload))
    return "\n".join(lines)


def format_markdown(transfers: List[Transfer]) -> str:
    control = [x for x in transfers if x.type == "control"]
    other   = [x for x in transfers if x.type != "control"]

    lines = ["# USB Capture Summary", ""]
    lines.append(f"**Total transfers:** {len(transfers)} "
                 f"({len(control)} control, {len(other)} bulk/interrupt/iso)")
    lines.append("")

    if control:
        lines += ["## Control Transfers (EP0)", ""]
        lines.append("| # | Time (s) | addr | Req | Direction | Descriptor / Result |")
        lines.append("|---|----------|------|-----|-----------|---------------------|")
        for x in control:
            s = x.setup or {}
            req = s.get("bRequest", "?")
            desc = ""
            if x.decoded:
                dn = x.decoded.get("descriptor_name") or x.decoded.get("request") or x.decoded.get("class", "")
                desc = dn
            lines.append(f"| {x.index} | {x.time_s:.4f} | {x.addr} | "
                         f"{req:#04x} | {x.direction} | {desc} |")
        lines.append("")

    if other:
        lines += ["## Data Transfers", ""]
        lines.append("| # | Time (s) | addr | ep | type | dir | bytes |")
        lines.append("|---|----------|------|----|------|-----|-------|")
        for x in other:
            lines.append(f"| {x.index} | {x.time_s:.4f} | {x.addr} | {x.endp} | "
                         f"{x.type} | {x.direction} | {len(x.payload or b'')} |")
        lines.append("")

    return "\n".join(lines)


FORMATTERS = {
    "json":       format_json,
    "transcript": format_transcript,
    "markdown":   format_markdown,
}

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def decode(pcap_path: str, filters: Filters, force_native: bool = False) -> List[Transfer]:
    packets      = stream_packets(pcap_path, force_native=force_native)
    transactions = stream_transactions(packets)
    transfers    = stream_transfers(transactions)
    return [x for x in transfers if filters.match(x)]


def main():
    p = argparse.ArgumentParser(description="Decode a Packetry/Cynthion USB pcap capture.")
    p.add_argument("pcap", help="Path to .pcap or .pcapng file")
    p.add_argument("--filter", action="append", metavar="KEY=VAL",
                   help="Filter: address=N, endpoint=N, transfer-type=control|bulk|interrupt|iso")
    p.add_argument("--time-range", metavar="START,END",
                   help="Keep only transfers within this time range (seconds from start)")
    p.add_argument("--phase", choices=["enumeration"],
                   help="enumeration: only SET_ADDRESS and GET_DESCRIPTOR on EP0")
    p.add_argument("--format", choices=list(FORMATTERS), default="json",
                   help="Output format (default: json)")
    p.add_argument("--native", action="store_true",
                   help="Force native Python decoder (skip tshark)")
    args = p.parse_args()

    filters = Filters(args)
    transfers = decode(args.pcap, filters, force_native=args.native)
    print(FORMATTERS[args.format](transfers))


if __name__ == "__main__":
    main()
