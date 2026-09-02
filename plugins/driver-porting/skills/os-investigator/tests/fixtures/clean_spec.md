# Widgetron spec (SYNTHETIC FIXTURE - clean)

This fixture is what a good spec looks like: the same hardware facts as the
leaky fixture, expressed as hardware facts, grouped the way a databook would
group them, with per-fact provenance tags and the required caveats.

## Register map (grouped per the databook)

| Offset | Name | Notes |
| --- | --- | --- |
| 0x00 | CTRL | soft-reset, enable, and interrupt-unmask bits [databook 3.1] |
| 0x04 | STATUS | reset-busy indication [databook 3.2] |

## Ordered init sequence

1. Assert the controller soft reset through the control register. [databook 4.2]
2. Poll the status register until the reset-busy indication clears, bounding
   the wait with a timeout. The retry count is an implementation choice, not a
   silicon requirement - re-derive on hardware. [source-observed]
3. Enable the controller and unmask its interrupt. Order not known to be
   required. [source-observed]

No source code reproduced; facts and mechanism only.
