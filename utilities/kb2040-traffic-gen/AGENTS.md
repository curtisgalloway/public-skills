# AGENTS.md — kb2040-traffic-gen

Operational notes for agents running the traffic generator. Read
[README.md](README.md) for the full user-facing reference; this file
focuses on the gotchas an agent is likely to hit.

## When to use this

You're driving an end-to-end USB capture test and need predictable,
labelled traffic on the wire. Typical pairing: this tool on the source
side, [`cynthion-capture`](../../skills/cynthion-capture/) on the
analyzer side.

Don't reach for this for *real* device emulation — it's an exerciser, not
a Facedancer clone.

## Preflight checks

Before invoking `host_exerciser.py`, verify in parallel:

```bash
ls /dev/ttyACM* 2>/dev/null
groups
uv run host_exerciser.py --list  # or: python3 -m serial.tools.list_ports
```

Look for:

- Two `/dev/ttyACM*` devices with VID `0x239a` (the KB2040's CDC console
  + data ports).
- `dialout` in the current process's `groups` output.

If either is missing, jump to [Failure modes](#failure-modes).

## The dialout-group trap

Adding the user to `dialout` only takes effect for *new* login sessions.
A long-running shell (and any agent process spawned from it) keeps the
old group set even after `usermod -aG dialout`. Symptom:

```
Could not open /dev/ttyACM3: Permission denied
```

…even though `getent group dialout` lists the user. Fix without forcing
a logout: spawn a sub-shell with the new group via `sg`:

```bash
sg dialout -c 'uv run host_exerciser.py'
```

This is the recommended invocation when you can't be sure the parent
process picked up the group change.

## The supervisor architecture

Critical fact: `code.py`'s last pattern is `pat_reconnect`, which calls
`microcontroller.reset()`. **Every cycle ends in a hard USB reset.** That
means:

- The host's serial threads exit with `SerialException` at end-of-cycle.
  This is normal, not a bug.
- After re-enumeration, the device's CDC ports may come back with
  **different `/dev/ttyACM*` numbers** (e.g. ACM2/3 → ACM0/1). Don't
  hard-code port paths across runs.
- The default forever-loop in `host_exerciser.py` handles all of this:
  wait → open → drive → detect threads exit → close → loop.

If you bypass the supervisor (e.g. `--once`, or by patching it), expect
to redo the port-detection and reopen yourself between cycles.

## Running it from an agent

Run in the background and watch the log file rather than blocking:

```python
# pseudo-code
task = bash("sg dialout -c 'uv run host_exerciser.py'", run_in_background=True)
# later: read the task's output file and grep for milestones
```

Useful grep targets in the host log:

| Pattern                                                  | Meaning                                                          |
| -------------------------------------------------------- | ---------------------------------------------------------------- |
| `Opening data /dev/ttyACM`                               | New session is opening serial ports                              |
| `host→dev     7B  'start\n'`                             | Supervisor triggered a fresh cycle                               |
| `gate CLOSE '[cdc-large]'`                               | Device started a CDC echo-verifying pattern                      |
| `gate OPEN '[cdc-receive]'`                              | Device is ready for host probe bursts                            |
| `--- session ended; device should be re-enumerating ---` | One full cycle done; supervisor about to loop                    |
| `waiting for KB2040 to enumerate...`                     | Device hasn't reappeared yet — long wait may indicate a real fail|

To prove the loop is healthy, wait for **two** `session ended` lines —
that confirms one full reconnect+restart actually round-tripped.

## Stopping cleanly

- Foreground: Ctrl+C — `main()` catches `KeyboardInterrupt`, sets the
  stop event, joins threads, closes ports.
- Background task: use the harness's task-stop primitive (e.g.
  `TaskStop` in Claude Code). The supervisor will be SIGINT'd and exit
  the same way. The device will finish its current pattern, hit
  `[reconnect]`, reset, and idle (NeoPixel breathing blue) waiting for
  the next `start`.

## Failure modes

| Symptom                                                                 | Likely cause / fix                                                                                                |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `Permission denied` opening ttyACM*                                     | dialout group not active in this process → use `sg dialout -c '...'`                                              |
| `KB2040 data port not found`                                            | Device not enumerated. Check `--list`; confirm cable; if `CIRCUITPY` mounted but no ACM devices, re-copy `boot.py`.|
| Only one ttyACM device shows up with VID 0x239a                         | `boot.py` didn't enable both CDC interfaces — push the file again, then reset the board.                          |
| `dev→host` traffic stops with no `session ended`                        | Echo thread died but supervisor isn't watching (only happens if you bypass the supervisor or use `--once`).       |
| `gate CLOSE` followed by silence forever                                | The next marker arrived after a USB disconnect that killed the console thread. With the supervisor, this resolves at the next `[reconnect]`. |
| NeoPixel breathing blue, no host output                                 | Device is idle. Supervisor not running. Restart `host_exerciser.py`.                                              |
| Host script alive but threads dead (no new output, process still there) | You're running an old version without the supervisor loop. Pull latest `host_exerciser.py` from `main`.           |

## Files in this project

| File                | Where it runs | Role                                                              |
| ------------------- | ------------- | ----------------------------------------------------------------- |
| `boot.py`           | KB2040        | Enables 2× CDC + HID. Must be on `CIRCUITPY/` before `code.py`.   |
| `code.py`           | KB2040        | Pattern generator. `PATTERNS` list controls which patterns run.   |
| `host_exerciser.py` | Host PC       | Supervisor + echo + probe + console-marker reader.                |
| `README.md`         | n/a           | Human-facing reference.                                           |
| `AGENTS.md`         | n/a           | This file.                                                        |

## Don't

- Don't hard-code `/dev/ttyACM2` and `/dev/ttyACM3` across sessions — let
  auto-detect run, or pass `--port` explicitly each time.
- Don't `sudo chmod 666 /dev/ttyACM*` as a permanent fix; the device
  re-enumerates after every cycle and a new device node is created.
- Don't enable the HID patterns in `code.py` while the KB2040 is plugged
  *directly* into your workstation — they will type and click into
  whatever window is focused. Only enable when the device is plumbed
  through Cynthion or a similar HID-isolating fixture.
- Don't `--amend` commits to `code.py` while a host script is connected
  to the device — CIRCUITPY remount races with serial I/O cause flakiness.
