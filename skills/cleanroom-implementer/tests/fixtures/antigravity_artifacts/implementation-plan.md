<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
SYNTHETIC TEST FIXTURE - a clean Antigravity implementation-plan artifact.
It is deliberately dense with target-OS code, which is exactly what a plan
or walkthrough legitimately contains: the driver the agent just wrote. This
file pins the decision that text artifacts are scanned for license markers
only, never for code-shaped-line density.
-->

# Implementation plan: widgetron reset

Source of truth: `docs/widgetron-spec.md` §5 (init sequence, all steps tagged).

## Step 1 - reset the controller

```rust
fn reset(&self) -> Result<(), Error> {
    self.regs.ctl.write(CTL::SFTRST::SET);
    while self.regs.ctl.read(CTL::SFTRST) != 0 {
        self.timer.sleep(Duration::from_micros(10));
    }
    self.regs.phycfg.write(PHYCFG::SUSPEND::CLEAR);
    Ok(())
}
```

## Step 2 - bring up the PHY

```rust
fn phy_init(&self) -> Result<(), Error> {
    self.regs.phycfg.modify(PHYCFG::TURNAROUND.val(9));
    self.regs.gctl.modify(GCTL::PRTCAPDIR.val(2));
    Ok(())
}
```

Spec §5 marks the PHY-write ordering `[source-observed]` — "order not known to
be required" — so a `TODO(spec-gap)` is filed rather than assumed.
