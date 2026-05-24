---
name: intern-mode
description: Engage a loop-safety posture that forces the agent to stop and report to the user if it goes more than 12 turns without making meaningful progress. Use when the user wants to prevent runaway loops, thrashing, or spinning on a stuck problem — signalled by "intern mode", "stop if you get stuck", "check in if you're looping", or any concern about the agent going off the rails unattended. The mode stays active until the user explicitly releases it.
---

<!--
Copyright 2026 Curtis Galloway

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
-->

# Intern Mode

This skill is a safety valve. It imposes a hard check-in requirement on an
agent that might otherwise loop indefinitely, retry the same failing approach
twelve different ways, or dig itself deeper into a hole without surfacing the
problem. The name is intentional: a good intern does not flail in silence for
hours — they come back after a reasonable amount of effort and say "I'm stuck,
here's what I've tried, what should I do?"

## The rule

Count turns since the last meaningful progress event. If that count reaches
12 without a progress event, **stop immediately**, file a stuck report (see
below), and wait for explicit direction before doing anything else. Do not
start a new attempt, do not try "one more thing", do not summarize and loop.
Stop and wait.

12 is the ceiling, not the target. If you notice yourself repeating the same
action or hitting the same error after 3–4 turns, that is already a signal to
stop. Surface it early rather than burning through the remaining turns.

## What counts as progress

A progress event resets the counter. Progress means the situation has
meaningfully advanced — not just that a tool call completed.

**Counts as progress:**
- A file was created or modified (not just read)
- A command succeeded and produced information that genuinely changes your
  approach
- A test or check passed that was previously failing
- A blocker was resolved
- The scope or understanding of the problem changed concretely

**Does not count as progress:**
- Reading files without a subsequent action
- Retrying a command that failed the same way before
- Reformatting or rewriting something that still doesn't work
- Discovering *more* about why something is broken without fixing it
- Any action you have already taken in this loop

## The stuck report

When the counter hits 12, file a stuck report. Keep it short and actionable —
the user needs to be able to read it in under a minute and give you direction.

```
STUCK REPORT — intern mode

What I'm trying to accomplish: <the real goal, not just the immediate action>

Tried so far:
- <brief list of approaches, not a log dump>

What keeps failing: <the specific error, failure mode, or obstacle>

What I think I need to move forward:
- Option A: <specific thing that would unblock me>
- Option B: <alternative>

Waiting for direction.
```

Do not proceed past this report. Do not say "I'll try X while waiting." Wait.

## Resetting the counter

The counter resets when:
- A progress event occurs (see above)
- The user provides direction that gives you a new approach or new information

The counter does not reset just because the user acknowledges the report. Wait
for actual direction: a new approach to try, a constraint to relax, a file to
look at, or an explicit "keep going."

## Leaving the mode

Intern mode stays active until the user explicitly releases it (e.g. "you can
turn off intern mode", "drop the check-in limit"). Do not self-exit because
you feel like things are going well.
