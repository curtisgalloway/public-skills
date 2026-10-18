#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Pre-tool-use hook: confine the consult-runner agent to consult.py.

A subagent inherits the parent's permission mode, auto mode included, and a
plugin agent cannot carry its own hooks or permission mode, so the agent's tool
list alone does not stop it from running other commands. This hook, shipped in
the plugin manifest, reads which agent made the call and denies the runner
anything but `python3 <this directory>/consult.py ...`, with the message
optionally passed as a single-quoted heredoc. The runner needs no other tool:
`consult.py --runner` prints its procedure.

Calls from any other agent, and input this hook cannot parse, get no opinion
(exit 0, no output): the guard must never break the rest of the session, and
printing an allow would auto-approve the call in Claude Code.
"""

import json
from pathlib import Path
import re
import shlex
import sys

AGENT = "consult-runner"
HELPER = Path(__file__).resolve().with_name("consult.py")
ALLOWED_TOOLS = {"Bash"}
# A quoted delimiter keeps the shell from expanding anything in the body.
HEREDOC = re.compile(r"\s<<-?\s*'([A-Za-z_][A-Za-z0-9_]*)'\s*$")
# Anything that could start a second command or a substitution on the command line.
SHELL_SYNTAX = re.compile(r"[;&|<>`$()\\\n\r{}*?\[\]~!#]")


def is_runner(agent_type):
    return isinstance(agent_type, str) and (
        agent_type == AGENT or agent_type.endswith(":" + AGENT))


def shell_syntax(line):
    """True when the shell would see an operator, expansion or glob in this line.

    Scans left to right with the shell's own quote state, so a quote character
    inside the other kind of quotes (`"'"`) cannot hide what follows it.
    Single quotes make everything literal; double quotes still expand `$`,
    backticks, `\\` escapes and `!` history, so those stay refused there too.
    """
    quote = None
    for char in line:
        if quote == "'":
            if char == "'":
                quote = None
        elif quote == '"':
            if char == '"':
                quote = None
            elif char in "$`\\!":
                return True
        elif char in "'\"":
            quote = char
        elif SHELL_SYNTAX.match(char):
            return True
    return quote is not None


def command_problem(command):
    """None when the command only runs the helper, else the reason it is refused."""
    if not isinstance(command, str) or not command.strip():
        return "empty command"
    first, _, rest = command.strip().partition("\n")
    heredoc = HEREDOC.search(first)
    if heredoc:
        first = first[:heredoc.start()]
        lines = rest.split("\n")
        if not lines or lines[-1].strip() != heredoc.group(1):
            return "the heredoc must end the command with its delimiter alone on the last line"
        if any(line.strip() == heredoc.group(1) for line in lines[:-1]):
            return "the heredoc delimiter appears inside the message; pick another"
    elif rest.strip():
        return "multi-line commands are allowed only as a single-quoted heredoc"
    if shell_syntax(first):
        return "shell operators, substitutions and globs are not allowed"
    try:
        words = shlex.split(first)
    except ValueError as exc:
        return "unparseable command: %s" % exc
    if len(words) < 2 or not re.fullmatch(r"python3(\.\d+)?", Path(words[0]).name):
        return "the command must start with python3"
    try:
        script = Path(words[1]).expanduser().resolve()
    except (OSError, RuntimeError):
        return "unresolvable script path"
    if script != HELPER:
        return "only %s may run" % HELPER
    return None


def deny(reason):
    message = "consult-runner may only run `python3 %s ...`: %s" % (HELPER, reason)
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
    if not isinstance(event, dict) or not is_runner(event.get("agent_type")):
        return 0
    tool = event.get("tool_name")
    if tool not in ALLOWED_TOOLS:
        return deny("tool %r is not available to the runner" % tool)
    if tool == "Bash":
        problem = command_problem((event.get("tool_input") or {}).get("command"))
        if problem:
            return deny(problem)
    return 0


if __name__ == "__main__":
    sys.exit(main())
