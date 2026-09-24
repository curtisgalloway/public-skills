<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# Lab notebook templates

Replace placeholders with real content and adapt paths to project conventions. Every
timestamp comes from the system clock at the moment of writing.

## Chapter

Create `docs/notebook/<chapter>.md`. Entries are appended below the header, oldest first.

```markdown
# <Chapter ID> — <Title>

Goal: <what this unit of work is for; link the milestone, issue, or request>
Verdict record: <evidence file, PR, or handoff that will record the outcome>

## <timestamp> — opening
Starting revision: <commit or "none">. Pre-existing changes: <none, or list>.
Approach: <the plan, in two or three lines>.

## <timestamp> — attempt: <short title>
<Hypothesis or change, and the outcome. Link logs rather than pasting them.>

## <timestamp> — dead end: <short title>
<What was abandoned and why, so it is not retried.>

## <timestamp> — decision: <short title>
<The choice, the alternatives, and the reason.>

## <timestamp> — surprise: <short title>
<What contradicted an assumption, and what it changes.>

## <timestamp> — direction: <short title>
<The user's instruction and how it changes course.>

## <timestamp> — correction of <timestamp of earlier entry>
<What the earlier entry got wrong and what is true instead.>

## <timestamp> — checkpoint (closing)
State: <complete / in progress / blocked>. <What stands, what remains, the next action.>
```

Entry kinds: `opening`, `attempt`, `dead end`, `decision`, `surprise`, `direction`,
`correction`, `checkpoint`. Mark the final checkpoint of finished work `(closing)`.

## Index

Create `docs/notebook/index.md`.

```markdown
# Notebook index

Updated: <timestamp of the last index refresh>

A row is stale when its chapter has an entry newer than "indexed through".

## Chapters

### [<Chapter ID> — <Title>](<chapter>.md)
Entries: <first entry timestamp> through <indexed-through timestamp>
Outcome: <one line, or "open">
- <key finding or dead end>
- <at most five lines in total>

## Threads
- **<topic>:** [<chapter>](<chapter>.md#<entry anchor>), [<chapter>](<chapter>.md) —
  <one line on how the topic developed>
```

## Process log

Create `docs/process-log.md`. Entries are appended, oldest first.

```markdown
# Process log

Where the agent's process cost time on this project. Input for improving the agent's
instructions and skills; project findings go in the backlog instead.

## <timestamp> — <category>: <short title>
Chapter: [<chapter ID>](notebook/<chapter>.md)
What happened: <observed behavior, with exact error text if short>
Cost: <time, turns, a redone step, a wrong result shipped, or a user correction>
Prevention: <what instruction, check, or tool would have avoided it>
Fix belongs in: <skill name / project instructions / user instructions / tool>
Status: open
```

Categories: `failed command`, `surprise`, `user correction`, `sizing miss`,
`instruction gap`. When an entry is decided, append an entry with the same title and
`Status: fixed in <where>` or `Status: declined: <reason>` rather than editing the
original. An entry with neither is open.
