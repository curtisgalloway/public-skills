---
name: claude-session-transcript
description: Reference doc — how to locate the live Claude Code session transcript on disk and extract real user prompts from it (filter rules, slash-command pair collapsing, noise stripping). Other skills (learn, wrapup) Read this file before parsing transcripts. Not a user-invocable skill.
---

# Claude session transcript: location and extraction rules

This skill is a reference for other skills that need to read the user's prompts (or other events) from the current Claude Code session's on-disk transcript. It is not user-invocable. Other skills `Read` this file and apply its rules.

## Where transcripts live

Each session is logged as a JSONL file under:

```
$HOME/.claude/projects/<project-key>/<session-uuid>.jsonl
```

- `<project-key>` is derived from the cwd at session start: slashes replaced with hyphens, prefixed with a leading hyphen. Example: `/home/alice/projects/my-project` → `-home-alice-projects-my-project`.
- `<session-uuid>` is the harness's session UUID.

Each line of the file is one JSON event — user message, assistant message, tool call, tool result, etc.

## Locating the live session

Prefer `${CLAUDE_SESSION_ID}` — the harness substitutes this for the current session's UUID in skill argument contexts. Combine with a glob across all project-key dirs, because the project key is derived from cwd at session start but cwd may have changed mid-session (newly-created repo, `cd` into a subdir):

```bash
ls "$HOME"/.claude/projects/*/"${CLAUDE_SESSION_ID}".jsonl
```

If `${CLAUDE_SESSION_ID}` substitution is not available in the calling context, fall back to the most-recently-modified `.jsonl` anywhere under `$HOME/.claude/projects/`:

```bash
ls -t "$HOME"/.claude/projects/*/*.jsonl | head -1
```

The `*.jsonl` glob (not bare `*`) matters — it excludes the `memory/` subdir and any per-session subdirs.

## Listing sessions for the current project

For skills that need to walk the project's full session history (e.g. `/teach`, `/wrapup`):

```bash
PROJECT_KEY="-$(pwd | tr '/' '-')"
ls -t "$HOME/.claude/projects/$PROJECT_KEY"/*.jsonl
```

`-t` sorts newest first; reverse for chronological order. Same cwd-may-have-changed caveat applies — if the project was created mid-session, the live session's transcript may not be under the cwd-derived project key.

## Extracting real user prompts

A "real user prompt" is what the user actually typed, not a synthetic event. The filter:

- `type == "user"`, AND
- `userType == "external"`, AND
- `message.content` is either:
  - a string, OR
  - an array whose first element has `type: "text"`.

Skip entries whose `message.content` is a `tool_result` array — those are tool-call results being fed back to the model, not user prompts.

### Collapse slash-command pairs

When the user types `/foo`, the transcript records two `user` entries with the same `promptId`:

1. A stub: `<command-message>foo</command-message>`
2. The expanded body that the slash command resolves to.

Treat them as **one** prompt. Keep the expanded body; record the slash-command name as metadata (e.g. `[via /foo]`) if the calling skill cares.

### Strip harness-injected noise

Inside prompt content, strip these wrapper tags and their contents — they are harness injections, not what the user typed:

- `<system-reminder>...</system-reminder>`
- `<ide_selection>...</ide_selection>`
- `<command-stdout>...</command-stdout>`
- `<command-stderr>...</command-stderr>`
- `<command-name>...</command-name>`

What remains after stripping is the user's actual text.

## A jq one-liner for real user prompts

For skills that prefer jq over hand-walking the JSONL:

```bash
jq -c 'select(.type == "user" and .userType == "external")
       | select(
           (.message.content | type) == "string"
           or ((.message.content | type) == "array"
               and (.message.content[0].type == "text"))
         )' "$TRANSCRIPT"
```

This emits one JSON object per real user prompt. Slash-command pair collapsing and noise stripping are not done by the jq — apply those in the calling skill.

## Reading large transcripts

Active sessions can produce JSONL files of hundreds of MB. For large files, prefer:

- `Read` with `offset`/`limit` to page through, OR
- `jq` via `Bash` to extract just the events of interest, OR
- `wc -l` first to gauge size before deciding.

Avoid `Read` without bounds on a multi-MB transcript — it will blow the agent's context.

## What this skill does NOT cover

- **Tool-call event extraction.** `/learn` filters for `type == "assistant"` events with `tool_use` blocks and matches them with subsequent `tool_result` events. Those rules live in `/learn`'s skill body, not here.
- **Per-skill output formats.** What to do with the extracted prompts is each calling skill's concern.
- **Cross-session correlation.** Joining sessions that share state (e.g. a sub-agent session continuing from a parent) is not addressed here.
