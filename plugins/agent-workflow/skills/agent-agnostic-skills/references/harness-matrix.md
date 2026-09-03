# Harness matrix

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
portability-scan: intentional - this file's job is to name each harness's
surfaces side by side, so per-harness paths are the content, not a smell.
-->

**Verified 2026-08-11** against vendor documentation and, where the docs were unreachable, the
vendors' public repositories. Every row below is a claim about a moving target. Antigravity has
relocated hooks, settings and skills between releases; treat this as a starting point and confirm
with the slash commands in the last section, which report what your build actually reads.

## Contents

- [Status](#status)
- [Config locations](#config-locations)
- [Context and rules files](#context-and-rules-files)
- [Skills](#skills)
- [Subagents](#subagents)
- [Hooks](#hooks)
- [Tool names](#tool-names)
- [Argument names](#argument-names)
- [Capability denial](#capability-denial)
- [Session records](#session-records)
- [Ground truth commands](#ground-truth-commands)

## Status

| Harness | Binary | Status |
|---|---|---|
| Google Antigravity | `agy` CLI + IDE | Current. Go, closed source. Shares the agent engine with the IDE. |
| Gemini CLI | `gemini` | **Retired 2026-06-18** for free/Pro/Ultra and individual Code Assist. Enterprise Code Assist Standard/Enterprise retain access. Succeeded by Antigravity CLI. |
| Claude Code | `claude` | Current. |

Announced 2026-05-19, roughly a 30-day migration window. Keep Gemini CLI paths as labeled legacy
rungs in search ladders; drop them from install instructions.

## Config locations

| | Antigravity | Claude Code |
|---|---|---|
| user settings | `~/.gemini/antigravity-cli/settings.json` (newer builds also `~/.gemini/config/`) | `~/.claude/settings.json` |
| project settings | project-scoped settings dir your build reads (`~/.gemini/config/projects/`) | `<project>/.claude/settings.json` |
| workspace config dir | `<workspace>/.agents/` | `<project>/.claude/` |
| project-dir variable | **none** — read `workspacePaths[0]` from the event | `$CLAUDE_PROJECT_DIR` |

Gemini CLI, for reference: `~/.gemini/settings.json`, `<project>/.gemini/settings.json`,
`$GEMINI_PROJECT_DIR`.

## Context and rules files

| | Antigravity |
|---|---|
| cross-tool | `AGENTS.md` at the workspace root |
| harness-specific | `GEMINI.md` — **outranks** `AGENTS.md` |
| workspace rules | `.agent/rules/*.md` (both `.agent/` and `.agents/` have shipped — confirm) |
| precedence | system rules > `GEMINI.md` > `AGENTS.md` > workspace rules |

Claude Code reads `CLAUDE.md`, and `AGENTS.md` where configured. Keep one real copy; a duplicated
override drifts from the file you actually edit.

## Skills

Plain directories containing `SKILL.md` (exact filename; capitalization matters on case-sensitive
filesystems). Discovered at:

- Antigravity, user: `~/.gemini/antigravity/skills/`
- Antigravity, plugins: `~/.gemini/antigravity-cli/plugins/<plugin>/skills/`
- Antigravity, workspace: `<workspace>/.agents/skills/`
- `~/.agents/skills/` — reads as the tool-agnostic location and is worth keeping as a search rung,
  but **Antigravity does not read it** (Gemini CLI did). Do not install here and expect `agy` to
  find it.
- Claude Code: `~/.claude/skills/`, `<project>/.claude/skills/`
- Legacy Gemini CLI: `~/.gemini/skills/`, `<project>/.gemini/skills/`

`SKILL.md` is found at the root of a skills directory or one level deep
(`skills/<skill-name>/SKILL.md`); the subdirectory layout is what lets a skill bundle scripts.

## Subagents

| | Antigravity | Claude Code |
|---|---|---|
| location | `<workspace>/.agents/agents/<name>.md` or `.agents/agents/<name>/agent.md` | `<project>/.claude/agents/<name>.md` |
| format | Markdown, YAML frontmatter | Markdown, YAML frontmatter |
| tool restriction | `tools:` list (allowlist) | `tools:` list (allowlist) |
| invocation | `invoke_subagent` | `Task` |
| notable fields | `subagent`, `mainAgent`, `hidden`, `inheritMcp`, `commandExecutionPolicy`, `model` | `tools`, `model` |

Antigravity's `commandExecutionPolicy: sandbox` and `inheritMcp: false` are the two fields that
actually remove capability rather than merely narrowing a list.

**An unmapped or misspelled tool name in `tools:` is dropped silently.** Confirm the vocabulary
against your build; a silently dropped entry is either a tool you thought you'd removed or one you
thought you had.

## Hooks

| | Antigravity | Claude Code |
|---|---|---|
| config | `<workspace>/.agents/hooks.json`, `~/.gemini/config/hooks.json` (older: `~/.gemini/antigravity-cli/hooks.json`) | `settings.json` → `hooks` |
| pre-tool event | `PreToolUse` | `PreToolUse` |
| other events | `PostToolUse`, `PostInvocation`, `Stop` | `PostToolUse`, `SessionStart`, `Stop`, … |
| matcher | regex over tool name | string/regex over tool name |
| structure | named hook sets: `{"<name>": {"enabled": true, "PreToolUse": [{"matcher": …, "hooks": [{"command": …}]}]}}` | `{"PreToolUse": [{"matcher": …, "hooks": [{"type": "command", "command": …}]}]}` |

Gemini CLI, for reference, used `BeforeTool`/`AfterTool` and exported `$GEMINI_PROJECT_DIR` to hook
commands.

### Antigravity `PreToolUse` payload (stdin)

```json
{
  "toolCall": {"name": "run_command",
               "args": {"CommandLine": "…", "Cwd": "…", "WaitMsBeforeAsync": 0}},
  "stepIdx": 4,
  "conversationId": "…",
  "workspacePaths": ["/path/to/workspace"],
  "transcriptPath": "/path/to/session/log",
  "artifactDirectoryPath": "/path/to/artifacts",
  "modelName": "…"
}
```

Note the nesting under `toolCall` and the camelCase envelope with PascalCase tool arguments. Claude
Code sends `tool_name` and `tool_input` flat at the top level.

### Deciding

| | Antigravity | Claude Code |
|---|---|---|
| deny | `{"decision":"deny","reason":…}`; non-zero exit also denies | exit 2 + stderr, or `hookSpecificOutput.permissionDecision: "deny"` |
| allow | `{"decision":"allow"}` — **an empty object or empty stdout is not accepted** | exit 0; silence is fine |
| other | `"ask"` requests confirmation | `"ask"` via `permissionDecision` |

The fields are additive across harnesses, so one response can satisfy all of them. See
`plugins/driver-porting/skills/cleanroom-implementer/scripts/cleanroom_hook.py` for the combined emitter.

### Caveats

- Workspace-local hooks load **only in a trusted workspace**; an untrusted one fails open silently.
- The **Antigravity IDE has not reliably run CLI hooks**. Hooks are the `agy` mechanism. Verify in
  the surface you actually work in.
- `agy -p` / `--print` is the non-interactive form, with `--output-format` for scripting, but has
  open bugs hanging in non-TTY environments — piping or subprocess-spawning it may produce silence.

## Tool names

| Operation | Antigravity | Claude Code | Gemini CLI (retired) |
|---|---|---|---|
| read file | `view_file`, `read_file` | `Read` | `read_file` |
| write file | `write_file` | `Write` | `write_file` |
| edit file | `edit_file` | `Edit` | `replace` |
| list dir | `list_dir` | — (Bash/Glob) | `list_directory` |
| grep | `grep_search`, `codebase_search` | `Grep` | `grep_search`, `search_file_content` |
| glob | — | `Glob` | `glob` |
| shell | `run_command` | `Bash` | `run_shell_command` |
| fetch URL | `read_url_content` | `WebFetch` | `web_fetch` (URL inside `prompt`) |
| web search | `search_web` | `WebSearch` | `google_web_search` |
| delegate | `invoke_subagent` | `Task` | (subagent invocation) |
| MCP tools | vendor-prefixed | `mcp__<server>__<tool>` | `mcp_<server>_<tool>` |

## Argument names

Case-fold before comparing; that single step collapses most of this table.

| Kind | Names seen |
|---|---|
| file path | `TargetFile`, `AbsolutePath`, `file_path`, `absolute_path`, `path`, `paths`, `notebook_path` |
| directory | `Cwd`, `SearchDirectory`, `dir_path`, `directory`, `path` |
| shell command | `CommandLine`, `command`, `cmd` |
| URL | `Url`, `url`; **or embedded in a prose `prompt`** (Gemini's `web_fetch` took no `url` field) |
| query | `Query`, `query`, `pattern` |
| authored content | `CodeEdit`, `content`, `new_string`, `old_string`, `patch`, `instruction` |

The last row is the one to exempt from scanning, deliberately and with a comment.

## Capability denial

**Antigravity** — allow/ask/deny lists in settings, precedence `deny > ask > allow`, recursive path
matching, `tool(arg)` rule syntax, `regex:` prefix for regex rules:

```json
{"permissions": {"deny": ["search_web", "read_file(~/src/linux)"]}}
```

Permission modes: `request-review` (default), `accept-edits`, `plan`, `always-proceed`,
`proceed-in-sandbox`, `strict`. **`strict` denies all non-read operations** — wrong for any agent
whose job is writing code. `proceed-in-sandbox` is the unattended-with-guardrails choice.

**Claude Code** — `permissions.deny` in settings, with `Tool(pattern)` entries.

**Gemini CLI** (retired) had a TOML policy engine (`~/.gemini/policies/*.toml`, `[[rule]]` tables,
`toolName`/`argsPattern`/`commandRegex`/`decision`/`priority`, `--policy` replacing rather than
merging the user directory). It is the most expressive of the three and is gone, which is the
argument for keeping policy *data* in a file you own and treating the harness layer as wiring.

None of these have an environment-variable escape. If one role must be exempt (an investigator that
may read what an implementer may not), scope it by **launch** — a separate process with different
settings — not by a variable the permission layer never reads.

## Session records

| | Antigravity | Claude Code |
|---|---|---|
| transcript | path given per event as `transcriptPath` | `~/.claude/projects/<slug>/<session>.jsonl` |
| artifacts | `artifactDirectoryPath` per event; `~/.gemini/antigravity/brain/<GUID>/` | — |
| conversation store | SQLite `.db` | — |
| artifact types | task, implementation plan, walkthrough, other | — |

Record shapes to recognize in one pass: nested `toolCall` objects with the result *beside* the call,
`toolCalls[]` arrays with the result *inside*, `functionCall`/`functionResponse` parts,
`tool_use`/`tool_result` blocks. Sniff the container format (SQLite magic bytes, JSONL, JSON, text)
rather than trusting the extension.

Antigravity's artifacts matter for auditing: plans and walkthroughs are written from whatever was in
context, so they carry the same evidence a transcript does — and in the IDE, where hooks may not
fire, they may be the only record you get.

## Ground truth commands

When a path here is wrong, these report what the build actually reads:

- Antigravity: `/hooks`, `/permissions`, `/permissions list`, `/agents`, `/skills`, `/config`
- Claude Code: `/hooks`, `/permissions`, `/agents`, `/config`

And the check no command replaces: deliberately trigger the behavior your tool exists to catch, and
confirm it appears in your log.
