# Widgetron spec (SYNTHETIC FIXTURE - deliberately leaky)

This fixture is what a bad spec looks like: the init sequence transcribed
statement-by-statement from the reference implementation, carrying the
source's own invented identifier names.

widgetron_write(wp, WIDGETRON_CTRL, CTRL_SOFT_RESET);
while (widgetron_read(wp, WIDGETRON_STATUS) & STATUS_RESET_BUSY) {
	if (!--purple_latch_timeout)
		return -ETIMEDOUT;
}

The driver names its state machine `widgetron_bringup_sequence` and counts
down a `purple_latch_timeout`.
