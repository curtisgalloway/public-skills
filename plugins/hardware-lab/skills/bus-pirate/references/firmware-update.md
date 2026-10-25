<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Updating Bus Pirate 5/6 firmware to the latest main build

Companion to `SKILL.md`. Takes about five minutes; the flash itself is under a
minute.

**Terms**
- **UF2**: the firmware image format the RP2040/RP2350 boot ROM accepts.
- **Bootloader / BOOTSEL**: the boot ROM's update mode. It shows up as a USB
  drive (`RPI-RP2` on BP5) plus a vendor interface that `picotool` talks to.
- **picotool**: Raspberry Pi's CLI for that vendor interface
  (`brew install picotool`, or your distro's package).

## Where "latest" comes from

Upstream (`DangerousPrototypes/BusPirate5-firmware`) has **no tags or GitHub
Releases** for firmware. GitHub Actions artifacts expire after 7 days and need a
login. The source to use is the official forum thread
<https://forum.buspirate.com/t/bus-pirate-5-auto-build-main-branch/20>: the
upstream bot posts `ci-buspirate-main-<sha>.zip` there for every commit to
`main`, and the firmware download page sends users to it. The `main_staging`
branch is stale, and the other branches are unmerged work. Do not flash them.

## Steps

1. **Check what is running now.** Run `i` at the terminal and note the
   `Firmware` line and the board (`Bus Pirate 5 REV10`, `Bus Pirate 6`, …). Very
   old builds print `Firmware v0.1.0 (commit unknown)`. Current ones print
   `Firmware main branch @ <sha> (<build date>)`.
2. **Fetch the newest build** into an empty directory:

   ```bash
   python3 scripts/bp_firmware.py latest                  # just look: sha, date, URL
   python3 scripts/bp_firmware.py fetch --board rev10 <empty-dir>
   ```

   Boards: `rev10` (Bus Pirate 5, current), `bp6`, `xl` (5XL), `rev8` (early
   5). The JSON output gives the extracted `.uf2` path and the sha to expect.
   If `i` already shows that sha, stop: the board is up to date.
3. **Make sure nothing else is using the Bus Pirate.** It drops off USB for the
   flash, and a running capture or script loses its port. If it is wired into
   a test rig, check with whoever owns the rig.
4. **Enter the bootloader.** Type `$` at the terminal prompt. The serial ports
   vanish at once (an open terminal reports "Device not configured", which is
   expected). The fallback is to hold the underside button while plugging in.
5. **Flash it.** Prefer `picotool`, which writes, verifies and reboots in one
   step and does not depend on the drive mounting:

   ```bash
   picotool info -a                         # confirms the bootloader is present; shows the old build
   picotool load -v -x <empty-dir>/bus_pirate5_rev10.uf2
   ```

   It should print `OK` after `Verifying Flash` and then `The device was
   rebooted`. Without `picotool`, copy the `.uf2` to the bootloader drive
   (`RPI-RP2` on BP5; `RP2350` or `BP__BOOT` on BP6). On macOS, `cp` to that
   FAT drive exits 1 with "could not copy extended attributes". The copy itself
   succeeded, so don't retry it.
6. **Confirm.** Reattach the terminal and run `i`. The `Firmware` line must
   show `main branch @ <sha>` with the sha from step 2.

## Things that differ after the update

- **The serial port names can change.** Old builds report a placeholder USB
  serial number, so macOS names the ports `/dev/cu.usbmodem1234567890121` /
  `…123`. Current builds report `5buspirate`, which gives
  `/dev/cu.usbmodem5buspirate1` (terminal) and `…3` (binary). Run
  `ls /dev/cu.usbmodem*` again and update any script that hard-codes the old
  name.
- **More modes.** A Feb 2024 build listed 6 (HiZ, 1-WIRE, UART, I2C, SPI, LED).
  `322c452` lists 14 (adds HDUART, 2WIRE, 3WIRE, DIO, INFRARED, JTAG, PS2, USB).
  Some mode names also changed (`1-WIRE` → `1WIRE`).
- **The VT100 prompt comes back** (`VT100 compatible color mode? (Y/n)>`).
  From a script, plain `\r` and `n\r` only re-printed the prompt. Sending `n\n`
  and then `n\r\n` got to `HiZ>`. Read until you see a mode prompt rather than
  assuming one write is enough.
- The default binmode on the second port may now be `SUMP logic analyzer`. Check
  `i` → `Active binmode` and change it with `binmode` if your tooling expects
  another.

## Troubleshooting

- **`RPI-RP2` never mounts after `$`.** This was seen on macOS 27: the USB
  device `RP2 Boot` (2e8a:0003) enumerated and the mass-storage driver attached,
  but no volume appeared. `picotool` still works because it uses a separate
  interface. Check with `ioreg -p IOUSB -l -w0 | grep -i 'RP2 Boot'`.
- **Red blinking after a flash** means the wrong board's `.uf2`. Enter the
  bootloader with the button and load the right file.
- **`picotool` finds no device**: the board is not in the bootloader (run `$`
  again), or on Linux it needs a udev rule or `sudo`.
