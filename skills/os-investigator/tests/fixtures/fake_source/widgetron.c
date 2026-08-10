/*
 * SYNTHETIC TEST FIXTURE - not real source from any project.
 *
 * A wholly fictional "Widgetron" peripheral, written from scratch as scanner
 * bait. It stands in for encumbered source in leak_scan tests. Never replace
 * this with real kernel/firmware code: the test suite would itself become the
 * leak it exists to detect.
 */
#include <fictional/widgetron.h>

#define WIDGETRON_CTRL   0x00
#define WIDGETRON_STATUS 0x04

static int widgetron_bringup_sequence(struct widgetron_priv *wp)
{
	unsigned int purple_latch_timeout = 4200;

	widgetron_write(wp, WIDGETRON_CTRL, CTRL_SOFT_RESET);
	while (widgetron_read(wp, WIDGETRON_STATUS) & STATUS_RESET_BUSY) {
		if (!--purple_latch_timeout)
			return -ETIMEDOUT;
	}
	widgetron_write(wp, WIDGETRON_CTRL, CTRL_ENABLE | CTRL_IRQ_UNMASK);
	return 0;
}
