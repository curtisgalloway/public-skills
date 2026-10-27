#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Pre-tool-use hook: keep the milestone-implementer agent from landing its own work.

The orchestrator pushes, opens pull requests and merges; the implementer only commits.
A subagent inherits the parent's permission mode, auto mode included, so the agent's
instructions alone do not stop a `git push`. This hook, shipped in the plugin manifest,
reads which agent made the call and denies the implementer `git push` and every `gh`
command. Its tool list already leaves out GitHub connector tools.

This is a tripwire for honest mistakes, not a sandbox: a command built at run time
(`eval`, a script file) gets past it. Calls from any other agent, and input this hook
cannot parse, get no opinion (exit 0, no output), so the guard never breaks the rest
of the session, and never prints an allow that would auto-approve a call.
"""

import json
import re
import shlex
import sys

AGENT = "milestone-implementer"
# Splits a command line into the commands it runs; quotes are not respected here,
# which can only produce extra segments, never hide one.
SEPARATORS = re.compile(r"&&|\|\||[;&|\n(){}`]|\$\(")
# git options that take their value as the next word.
GIT_VALUE_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}


def is_implementer(agent_type):
    return isinstance(agent_type, str) and (
        agent_type == AGENT or agent_type.endswith(":" + AGENT))


def words_of(segment):
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def git_subcommand(words):
    """The subcommand after `git` and its options, or None."""
    i = 0
    while i < len(words):
        word = words[i]
        if word in GIT_VALUE_OPTIONS:
            i += 2
        elif word.startswith("-"):
            i += 1
        else:
            return word
    return None


def segment_problem(segment, depth=0):
    words = words_of(segment)
    for i, word in enumerate(words):
        name = word.rsplit("/", 1)[-1]
        if name == "git" and git_subcommand(words[i + 1:]) == "push":
            return "git push"
        if name == "gh":
            return "gh"
        # A quoted argument may itself be a command (`sh -c 'git push'`).
        if depth < 2 and " " in word and word is not words[0]:
            problem = command_problem(word, depth + 1)
            if problem:
                return problem
    return None


def command_problem(command, depth=0):
    """None when the command neither pushes nor calls gh, else what it tried."""
    if not isinstance(command, str):
        return None
    for segment in SEPARATORS.split(command):
        problem = segment_problem(segment, depth)
        if problem:
            return problem
    return None


def deny(what):
    message = ("milestone-implementer may not run %s: the orchestrator pushes, opens "
               "pull requests and merges. Leave the branch committed and report." % what)
    # Claude Code's JSON and exit-code dialects together; both only withhold.
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "deny",
                                             "permissionDecisionReason": message}}))
    print(message, file=sys.stderr)
    return 2


def main(stdin=sys.stdin):
    try:
        event = json.load(stdin)
    except ValueError:
        return 0
    if not isinstance(event, dict) or not is_implementer(event.get("agent_type")):
        return 0
    if event.get("tool_name") != "Bash":
        return 0
    problem = command_problem((event.get("tool_input") or {}).get("command"))
    return deny(problem) if problem else 0


if __name__ == "__main__":
    sys.exit(main())
