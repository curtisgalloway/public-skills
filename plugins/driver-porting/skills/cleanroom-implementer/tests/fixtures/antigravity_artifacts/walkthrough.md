<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
SYNTHETIC TEST FIXTURE - a contaminated Antigravity walkthrough artifact.
It carries license MARKERS only (no real source): a marker in an artifact is
the signal that encumbered text reached a surface the hook never sees, since
the Antigravity IDE does not run hooks.
-->

# Walkthrough: widgetron reset

I compared the reset path against the reference implementation. The upstream
file opens with:

    SPDX-License-Identifier: GPL-2.0
    #include <linux/module.h>
    MODULE_LICENSE("GPL");

and exports its probe entry point with EXPORT_SYMBOL_GPL, which is where the
ordering constraint came from.
