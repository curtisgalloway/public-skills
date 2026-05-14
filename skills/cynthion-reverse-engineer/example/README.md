# Worked Example: "Example Widget" Synthetic Protocol

This example demonstrates the full `cynthion-reverse-engineer` pipeline using
synthetic captures of a simple vendor-specific USB device — no hardware required.

## Scenario

The imaginary device (`VID=0x1234`, `PID=0xabcd`, product: "Example Widget") uses a
4-byte command/response protocol on EP1 (bulk bidirectional):

```
OUT (host → device):  [opcode, arg0, reserved, seq]
IN  (device → host):  [status, data0, reserved, seq]

opcodes:
  0x01  STATUS_QUERY   — arg0 ignored; response data0 = current brightness
  0x02  SET_BRIGHTNESS — arg0 = new level;  response data0 = echo of arg0
```

## Step 0 — Generate captures

```bash
python3 generate_synthetic.py
```

Creates `status_query.json` and `set_brightness.json`, each containing 5
enumeration-phase control transfers followed by 10 paired bulk transactions.

## Step 1 — Diff

```bash
python3 ../scripts/diff_transactions.py \
    status_query.json set_brightness.json \
    --label status_query set_brightness --format text
```

Expected output — EP1 OUT:

```
byte[ 0] ^ monotonic   ...   ← opcode (0x01 vs 0x02 differ by 1; diff sees "monotonic")
byte[ 1] ! varying     ...   ← argument (0x00 vs 0x80)
byte[ 2] . constant    ...   ← reserved
byte[ 3] . constant    ...   ← seq counter (same values at each position in both captures)
```

> **Note:** `diff_transactions.py` does pairwise comparison — a byte that
> differs by exactly 1 between the two captures is labelled "monotonic" even
> if it is actually an opcode. `infer_commands.py` resolves this correctly.

## Step 2 — Infer command structure

```bash
python3 ../scripts/infer_commands.py \
    status_query.json set_brightness.json \
    --label status_query set_brightness > hypothesis.json
```

The infer step correctly identifies:
- **EP1 OUT byte[0]** as `opcode` (values 0x01/0x02, one per label)
- **EP1 OUT byte[1]** as `opcode` (values 0x00/0x80, one per label — this is actually the argument; real captures with more labels would separate it)
- **EP1 IN byte[1]** as `opcode` (0x40 = current brightness / 0x80 = echo)

## Step 3 — Generate replay script

```bash
python3 ../scripts/gen_replay.py hypothesis.json status_query.json -o replay.py
python3 replay.py   # requires: pip install libusb1 && device plugged in
```

The replay script opens the device by VID/PID, replays the observed control
transfers, then replays the bulk OUT/IN transactions observed in `status_query.json`.

## Step 4 — Generate Facedancer clone

```bash
python3 ../scripts/gen_facedancer_clone.py status_query.json -o clone.py
```

> **Linux only.** Facedancer 3.x device emulation requires Linux.

```bash
BACKEND=cynthion python3 clone.py
```

The clone exposes the same VID/PID and descriptors as the real device. The
`handle_data_requested` stubs return zeroed bytes — fill them in once you
understand the protocol.

## Step 5 — Generate protocol document

```bash
python3 ../scripts/gen_protocol_doc.py hypothesis.json \
    --capture status_query.json status_query \
    --capture set_brightness.json set_brightness \
    -o protocol.md
```

Produces a structured Markdown reference with device identity, endpoint map,
inferred command table, byte-role breakdown, and open questions.

## What a real session looks like

With real hardware the workflow is identical; replace the `.json` inputs with
`.pcap` files from Packetry and the scripts decode them automatically:

```bash
python3 ../scripts/diff_transactions.py idle.pcap button.pcap \
    --label idle button --format markdown

python3 ../scripts/infer_commands.py idle.pcap button.pcap \
    --label idle button > hypothesis.json

python3 ../scripts/gen_replay.py hypothesis.json idle.pcap -o replay.py
```
