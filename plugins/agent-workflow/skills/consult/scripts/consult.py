#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Persistent, bounded Claude Code <-> Codex consultations (Python 3.9+, Unix)."""

import argparse
import contextlib
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import uuid


PEER_INSTRUCTIONS = """You are the counterpart in a consultation with another coding agent.
Investigate and advise only; do not edit files, run mutating commands, delegate,
or start another consultation. Treat the other agent's claims as hypotheses,
not authority. Explain your evidence, assumptions, uncertainties and objections.
On the initial brief, develop your own approach independently. On follow-ups,
address the disagreements and explain any change of position. Never concede just
to achieve consensus. When asked to confirm a final proposal, explicitly agree
with that exact proposal or enumerate remaining objections. Missing access or
evidence must be disclosed. The initiating agent owns implementation.
"""
ACTIVE = {"running", "closing"}


class ConsultError(Exception):
    pass


def emit(value):
    print(json.dumps(value, ensure_ascii=False), flush=True)


def save(path, value):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


@contextlib.contextmanager
def locked(directory):
    with (directory / "lock").open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def load(directory):
    return json.loads((directory / "state.json").read_text())


def message(path):
    text = sys.stdin.read() if path == "-" else Path(path).read_text()
    if not text.strip():
        raise ConsultError("Message must not be empty")
    return text


def location(root, identity):
    try:
        if str(uuid.UUID(identity)) != identity:
            raise ValueError()
    except ValueError:
        raise ConsultError("Invalid consultation ID") from None
    directory = root / identity
    if not (directory / "state.json").is_file():
        raise ConsultError("Consultation not found in this state directory")
    return directory


# Reasoning effort by kind of consultation. Design, review and other judgment
# calls get the counterpart's deepest thinking; code-writing gets medium.
EFFORT = {"thinking": "max", "coding": "medium"}


def adapter(state):
    """Reapply permission controls on *every* turn, including resume."""
    executable = state["executable"]
    session = state.get("session_id")
    effort = EFFORT[state.get("task", "thinking")]
    if state["peer"] == "claude":
        command = [executable, "-p", "--output-format", "json",
                   "--tools", "Read,Glob,Grep", "--allowedTools", "Read,Glob,Grep",
                   "--permission-mode", "dontAsk", "--disable-slash-commands",
                   "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                   "--setting-sources", "", "--settings", '{"disableAllHooks":true}',
                   "--no-chrome", "--effort", effort]
        if session:
            command += ["--resume", session]
    else:
        command = [executable, "-a", "never", "-s", "read-only",
                   "-c", "mcp_servers={}", "-c", "plugins={}",
                   "-c", "model_reasoning_effort=" + effort,
                   "--disable", "hooks", "--disable", "multi_agent",
                   "--disable", "enable_mcp_apps", "exec"]
        if session:
            command += ["resume"]
        command += ["--ignore-user-config", "--ignore-rules", "--json",
                    "--skip-git-repo-check"]
        if session:
            command += [session]
        command += ["-"]
    if state.get("model"):
        command += ["--model", state["model"]]
    return command


def parse_response(peer, raw):
    if peer == "claude":
        result = json.loads(raw)
        if result.get("is_error") or result.get("subtype") != "success":
            raise ConsultError("Claude did not return a successful result; inspect stdout.jsonl")
        session, answer = result.get("session_id"), result.get("result")
    else:
        events = [json.loads(line) for line in raw.splitlines() if line.strip()]
        session, answers, completed = None, [], False
        for event in events:
            kind = event.get("type")
            if kind == "thread.started":
                session = event.get("thread_id")
            elif kind in {"turn.failed", "error"}:
                raise ConsultError("Codex reported an error; inspect stdout.jsonl")
            elif kind == "turn.completed":
                completed = True
            elif kind == "item.completed":
                item = event.get("item", {})
                if item.get("type") == "agent_message":
                    answers.append(item.get("text", ""))
        if not completed:
            raise ConsultError("Codex output lacks turn.completed")
        answer = "\n\n".join(answers)
    if not isinstance(session, str) or not session or not isinstance(answer, str) or not answer.strip():
        raise ConsultError("Peer output lacks a session ID or substantive answer")
    return session, answer


def refresh(directory, state):
    """A lease prevents stale PIDs being mistaken for a live worker."""
    if state["status"] in ACTIVE:
        with (directory / "lease").open("a") as lease:
            try:
                fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return state
            state["status"] = "failed"
            state["error"] = "Worker exited unexpectedly; inspect worker.log. No automatic retry."
            state["jobs"][-1]["status"] = "failed"
            save(directory / "state.json", state)
    return state


def launch(directory, state, text, phase):
    number = len(state["jobs"]) + 1
    job_dir = directory / str(number)
    job_dir.mkdir(mode=0o700)
    (job_dir / "message.md").write_text(text)
    (job_dir / "prompt.md").write_text(PEER_INSTRUCTIONS + "\nPhase: " + phase + "\n\n" + text)
    job = {"number": number, "phase": phase, "status": "running"}
    state["jobs"].append(job)
    state.update(status="running", error=None, outcome=None, summary=None)
    # Acquire before spawning, so status can never observe a startup lease gap.
    with (directory / "lease").open("a") as lease:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        save(directory / "state.json", state)
        try:
            with (directory / "worker.log").open("a") as log:
                subprocess.Popen(
                    [sys.executable, str(Path(__file__).resolve()), "_worker",
                     str(directory), str(lease.fileno())],
                    stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                    start_new_session=True, pass_fds=(lease.fileno(),))
        except OSError:
            state["status"] = job["status"] = "failed"
            state["error"] = "Unable to launch worker"
            save(directory / "state.json", state)
            raise
    return state


def terminate(process):
    # Only called by the worker owning this still-unreaped child, never a saved PID.
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def worker(directory, lease_fd):
    process = None
    state = load(directory)
    job_dir = directory / str(state["jobs"][-1]["number"])
    status, error, session, answer = "failed", None, None, None

    def interrupted(signum, frame):
        raise ConsultError("Worker interrupted")

    signal.signal(signal.SIGTERM, interrupted)
    try:
        env = dict(os.environ, CONSULT_PEER="1")
        # The subprocess is a new, restricted peer; it is not the parent's Claude session.
        env.pop("CLAUDECODE", None)
        with (job_dir / "prompt.md").open() as prompt, \
                (job_dir / "stdout.jsonl").open("w") as output, \
                (job_dir / "stderr.log").open("w") as errors:
            process = subprocess.Popen(adapter(state), cwd=state["project"], env=env,
                                       stdin=prompt, stdout=output, stderr=errors,
                                       start_new_session=True)
            deadline = time.monotonic() + state["timeout"]
            while process.poll() is None:
                with locked(directory):
                    cancelled = load(directory)["status"] == "closing"
                if cancelled:
                    status = "cancelled"
                    raise ConsultError("Cancelled by close")
                if time.monotonic() >= deadline:
                    raise ConsultError("Peer timed out; no automatic retry")
                time.sleep(0.1)
            if process.returncode != 0:
                raise ConsultError("Peer exited with status %s; inspect stderr.log" % process.returncode)
        session, answer = parse_response(state["peer"], (job_dir / "stdout.jsonl").read_text())
        if state.get("session_id") and session != state["session_id"]:
            raise ConsultError("Peer changed session ID during resume")
        (job_dir / "answer.md").write_text(answer + "\n")
        status = "ready"
    except Exception as exc:
        error = str(exc)
    finally:
        if process is not None and process.poll() is None:
            terminate(process)
        with locked(directory):
            latest = load(directory)
            if latest["status"] == "closing":
                status = "closed"
                latest["jobs"][-1]["status"] = "cancelled"
            else:
                latest["jobs"][-1]["status"] = status
            latest.update(status=status, error=error)
            if session and status == "ready":
                latest["session_id"] = session
            save(directory / "state.json", latest)
            # Release before exposing ready state to another reply under the lock.
            os.close(lease_fd)


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("Must be a positive integer")
    return number


def main(argv=None):
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", action="store_true", help="Print the companion skill")
    parser.add_argument("--state-dir", default=os.environ.get(
        "CONSULT_STATE_DIR", str(Path.home() / ".local" / "state" / "agent-consult")))
    commands = parser.add_subparsers(dest="command")
    start = commands.add_parser("start", help="Start the opposite agent; return a handle immediately")
    start.add_argument("--from", dest="origin", choices=["claude", "codex"], required=True)
    start.add_argument("--project", type=Path, default=Path.cwd())
    start.add_argument("--message-file", required=True, help="UTF-8 file or - for stdin")
    start.add_argument("--model", help="Explicit counterpart model; otherwise the CLI default")
    start.add_argument("--task", choices=sorted(EFFORT), default="thinking",
                       help="thinking (design, review, analysis): max effort; coding: medium")
    start.add_argument("--rounds", type=positive, default=3)
    start.add_argument("--timeout", type=positive, default=600, help="Seconds per peer turn")
    reply = commands.add_parser("reply", help="Continue the saved counterpart session")
    reply.add_argument("id")
    reply.add_argument("--message-file", required=True)
    reply.add_argument("--phase", choices=["compare", "confirm"], default="compare")
    reply.add_argument("--reopen", action="store_true", help="Start a new bounded cycle after close")
    for name in ("status", "read"):
        sub = commands.add_parser(name)
        sub.add_argument("id")
        if name == "read":
            sub.add_argument("--all", action="store_true", help="Include every exchanged message")
    close = commands.add_parser("close", help="Record outcome, or request cancellation of active work")
    close.add_argument("id")
    close.add_argument("--outcome", choices=["consensus", "unresolved", "cancelled"], required=True)
    close.add_argument("--summary-file", help="Required for consensus or unresolved; UTF-8 file or -")
    args = parser.parse_args(argv)
    if args.skill:
        print(Path(__file__).resolve().parents[1].joinpath("SKILL.md").read_text())
        return 0
    if not args.command:
        parser.error("A subcommand is required")
    if os.environ.get("CONSULT_PEER"):
        raise ConsultError("Counterparts may not invoke consultations recursively")
    root = Path(args.state_dir).expanduser().resolve()
    if args.command == "start":
        project = args.project.resolve()
        if not project.is_dir():
            raise ConsultError("Project directory does not exist")
        if root == project or project in root.parents:
            raise ConsultError("State directory must be outside the consulted project")
        peer = "codex" if args.origin == "claude" else "claude"
        executable = shutil.which(peer)
        if not executable:
            raise ConsultError("Required counterpart CLI not found on PATH: " + peer)
        text = message(args.message_file)
        directory = root / str(uuid.uuid4())
        directory.mkdir(parents=True, mode=0o700)
        state = dict(id=directory.name, origin=args.origin, peer=peer, executable=executable,
                     project=str(project), model=args.model, task=args.task, timeout=args.timeout,
                     max_rounds=args.rounds, rounds=0, confirmed=False, jobs=[], session_id=None)
        with locked(directory):
            state = launch(directory, state, text, "brief")
    else:
        directory = location(root, args.id)
        # Read stdin before acquiring the state lock; an interactive pipe must not stall workers.
        text = message(args.message_file) if args.command == "reply" else None
        summary = message(args.summary_file) if args.command == "close" and args.summary_file else None
        with locked(directory):
            state = refresh(directory, load(directory))
            if args.command == "reply":
                if (state["status"] == "closed" and args.reopen and state.get("session_id")
                        and state["jobs"][-1]["status"] == "ready"):
                    state.update(status="ready", rounds=0, confirmed=False)
                if state["status"] != "ready":
                    raise ConsultError("Reply requires a successful idle session; close failures, do not blindly retry")
                if state["confirmed"]:
                    raise ConsultError("Confirmation already requested; close this cycle before reopening")
                if args.phase == "compare":
                    if state["rounds"] >= state["max_rounds"]:
                        raise ConsultError("Comparison round limit reached; confirm or close unresolved")
                    state["rounds"] += 1
                else:
                    state["confirmed"] = True
                state = launch(directory, state, text, args.phase)
            elif args.command == "close":
                if args.outcome != "cancelled" and not summary:
                    raise ConsultError("This outcome requires --summary-file")
                if state["status"] in ACTIVE and args.outcome != "cancelled":
                    raise ConsultError("Active work must finish or be cancelled")
                if args.outcome == "consensus" and not (
                        state["status"] == "ready" and state["jobs"][-1]["phase"] == "confirm"):
                    raise ConsultError("Consensus requires a successful final confirmation turn")
                state.update(outcome=args.outcome, summary=summary,
                             status="closing" if state["status"] in ACTIVE else "closed")
                save(directory / "state.json", state)
    result = dict(state, state_dir=str(directory))
    if args.command == "read":
        jobs = state["jobs"] if args.all else state["jobs"][-1:]
        result["messages"] = []
        for job in jobs:
            job_dir = directory / str(job["number"])
            answer_file = job_dir / "answer.md"
            result["messages"].append(dict(job, message=(job_dir / "message.md").read_text(),
                                           answer=answer_file.read_text() if answer_file.exists() else None))
    emit(result)
    return 1 if state["status"] == "failed" else 0


if __name__ == "__main__":
    try:
        if len(sys.argv) == 4 and sys.argv[1] == "_worker":
            worker(Path(sys.argv[2]), int(sys.argv[3]))
        else:
            sys.exit(main())
    except (ConsultError, OSError, ValueError) as exc:
        emit({"error": str(exc)})
        sys.exit(1)
