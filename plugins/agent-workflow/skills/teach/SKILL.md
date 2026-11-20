---
name: teach
description: Summarize past coding-agent sessions into teaching-oriented markdown files. Reads project-scoped Claude Code or Codex session history, finds sessions that haven't been summarized yet (keyed on session_id in existing summary frontmatter), and writes one summary per unsummarized session. Use when the user invokes /teach or asks to "summarize previous sessions" / "catch up on session summaries".
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Teach: summarize past sessions for teaching

The user produces teaching material that shows students how they used agentic coding tools to build a project. Each summary file is a **teaching artifact** — the goal is to make the user's prompting technique legible to a student reading later, not to recap the work in a developer-changelog tone.

## Where things live

- **Session history (input):** use the shared [session history reference](../learn/references/session-history.md)
  for Codex thread selection and pagination or Claude Code transcript selection and filtering.
- **Summaries (output):** `sessions/YYYY-MM-DD-<slug>.md` relative to the selected repository root. Create the `sessions/` dir if it does not exist.

## Procedure

1. **List candidate sessions** for the current project and harness using the shared reference.
   Keep the stable session ID, project, and timestamp with each candidate.

2. **Include the live session** when its identity and project are confirmed. Summarize through
   the last available user turn and identify that cutoff for a live chat. Later runs keep
   existing summaries unless the user asks to refresh one.

3. **Find what's already summarized.** Grep `sessions/*.md` for `session_id:` frontmatter values. Build the set of already-covered session IDs. If `sessions/` is empty or missing, the set is empty. Sessions whose ID is already in this set are skipped, including the live one.

4. **For each unsummarized session,** in chronological order (oldest first, so the teaching narrative reads forward):
   - Read the selected session's messages in order. Follow the reference for its harness to
     extract real user prompts and distinguish them from tool output or injected instructions.
   - If only summaries or truncated messages are available, report the missing evidence
     and skip that session so a later run can finish it.
   - Take the date from the first event or thread creation timestamp, in the user's local
     time when known.
   - Pick a short slug (3-6 words, kebab-case) describing the session's topic.

5. **Write the summary** at `sessions/YYYY-MM-DD-<slug>.md` using the template below. Do not overwrite an existing file with the same path — if a collision occurs, append `-2`, `-3`, etc.

6. **Report** to the user: how many sessions were already summarized, how many you just wrote, and the path of each new file. If there were zero unsummarized sessions, say so plainly.

## Summary file template

```markdown
---
session_id: <stable-session-or-thread-id>
date: <YYYY-MM-DD>
title: <human-readable title>
---

# <title>

## What got built
<2-4 sentences: what concrete artifacts or decisions came out of this session. Link to files in the repo with markdown links where relevant.>

## Prompts, in order

### 1. <short label for the prompt>
> <verbatim user prompt, or a faithful condensation if it's very long — quote the key phrasing>

**What the agent did:** <one or two sentences>

**Teaching note:** <one or two sentences on the technique — what made this prompt effective, or what the student should notice about how it was framed. Examples: "asks for a tradeoff rather than an answer, which keeps the agent in advisory mode", "names the file path explicitly so the agent doesn't have to guess", "corrects course mid-task rather than restarting — cheaper than re-prompting from scratch".>

### 2. ...

## Takeaways for students
- <bullet — 2 to 5 of these, focused on prompting/agentic-tool technique, not on the project's domain>
```

## Style guidance for the summaries

- **Quote prompts faithfully.** Students need to see the actual phrasing the user used, not a paraphrase. Trim only for length, and mark elisions with `[…]`.
- **Teaching notes are the point.** A summary without teaching notes is just a transcript dump. For each prompt, ask: *what would a student miss if they only saw the prompt and the result?* That gap is the teaching note.
- **Surface course corrections.** When the user pushed back, redirected, or rejected a tool call, that is high-value teaching content — flag it explicitly (e.g. "user rejected the first attempt and clarified the requirement, which is a normal part of working with agents").
- **Be honest about dead ends.** If a prompt led to the wrong place and the user redirected, say so. The teaching value is in the recovery, not in pretending the path was straight.
- **Brand-neutral language.** Refer to "the agent" rather than naming a specific tool in the body of the summary. The frontmatter and tooling references can stay literal.

## Things to avoid

- Do not invent prompts the user did not send.
- Do not include tool-call output verbatim — it bloats the file and isn't teaching material. Describe what the tool did in one phrase instead.
- Do not write a generic "Summary of changes" section that duplicates `git log` — focus on the prompting, which `git log` cannot capture.
