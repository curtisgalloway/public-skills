<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Read the intended session

A **thread** is one saved Codex chat. Its ID identifies the conversation even if another
chat starts in the same project. The **app server** is the interface clients use to read
that history. See the [glossary](../../../../../GLOSSARY.md).

Select the harness that owns the requested session.
For the current session, use the ID supplied by the calling chat, CLI, or hook. If that
ID is unavailable, use the visible conversation for a quick review and identify its
coverage. Ask for the chat if several candidates match and saved history is required.

## Codex

- **Discover.** On desktop, use `list_threads` in history mode with source `codex`.
  Keep the host and project from the request. List active and archived history
  separately for a historical survey and follow each cursor. Match the returned project
  or working directory before reading messages. For a cross-project review use the
  requested date window. Omit worker or subagent chats unless the user included them.
- **Read.** Pass the selected thread ID and host to `read_thread`. Follow the older-turn
  cursors through the requested period, then put turns in chronological order. Listing
  titles is sufficient to select a chat. Quoting a prompt requires its actual message.
- **CLI or another client.** With an initialized Codex app-server connection, use
  `thread/list` for discovery and `thread/read` for metadata. On clients that support
  it, set `currentAccountOnly: true`. Its `cwd` filter matches directories exactly,
  so include known project subdirectories and worktrees or filter the listed metadata
  by project before reading turns. Page
  `thread/turns/list` with the selected `threadId`, `itemsView: "full"` and
  `sortDirection: "asc"`. Pass back `nextCursor` until it is null. Read active
  and archived lists separately when both are in scope. These calls read stored
  history without resuming the session. [App-server protocol](https://learn.chatgpt.com/docs/app-server)
- **Extract.** Take prompt text from user-authored message items. Exclude injected
  instructions, environment records, tool output, and subagent reports. Keep the
  original wording, turn order, and stable thread ID. If a tool returns truncated
  text, request the full item or mark the omission. If history access fails, report
  the missing portion and leave that session eligible for a later summary.

## Claude Code

Use the sibling [Claude transcript reference](../../claude-session-transcript/SKILL.md)
for file selection and real-prompt filtering. For a project survey, verify the recorded
working directory or project for each candidate. If the live ID is ambiguous, ask for
the session. Selecting the newest file across projects can pick an unrelated task.

For another harness, use its own project-scoped history tool or a transcript supplied by
the user. Report the available coverage before drawing conclusions.
