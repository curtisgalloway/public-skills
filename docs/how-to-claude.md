<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# How To Claude

Curtis Galloway — 2026-08-28

Here are some tips for using Claude based on what I've learned by using it for a number of coding
and non-coding projects. While I haven't verified them with other AI tools, I think much of the
guidance is probably not Claude-specific.

## Some basics

A "session" is one conversation, either in Chat, Cowork or Code. A "turn" is one round of you
typing, Claude answering.

When you start a new session, Claude reads its default prompt ("You are a helpful agent…") and any
memory it knows about you, as well as any per-project context (like the `CLAUDE.md` file in a code
project), before you type your first message.

Then, every time you type a new message, it essentially does that all over again and reads the
past conversation up to the current message. Each time you type something, Claude reads a longer
and longer session text, up to its context limit (1 million "tokens" in Opus and Fable 5, which
roughly corresponds to three-quarters of a million words). So the longer the conversation gets,
the more Claude has to read every time to keep up with what's going on. Remember that for later
on.

## One topic per session

Claude does better when you keep each session focused on one major topic. This is especially true
if you try to change the topic at the end of a long session. All that previous session text tends
to crowd out the later discussion, so Claude can end up focusing too much of its attention on the
old topic and not on the new.

If you change topics, quit and start a new session, or use `/clear` to clear its context window,
which ends up being the same thing.

## Don't let sessions get too long

Even if you keep each session to one topic, it's still better to keep a single session from
getting too long. As the context window fills up, Claude has a harder and harder time remembering
all the things at the beginning of the conversation, including really important things like
memories or your `CLAUDE.md` instructions. It will tend to want to use everything that's in its
context window which might not be helpful as you move through your discussion.

Keep an eye on the size of the context window with the `/context` command; once it gets over half
full, consider wrapping things up and starting a new session (or clearing the context).

## Teach Claude how to hand off between sessions

When you start a new session, Claude knows nothing about your previous conversation, except what
it's explicitly committed to memory. This is a problem if you follow my advice on keeping sessions
short!

The solution is to have Claude write a "handoff prompt" for its next incarnation. The basic idea is
to tell Claude to write a prompt for an agent on how to continue from the current state of the
conversation. If it has important information that isn't saved somewhere, it should either save it
or include it directly in the handoff. The [`handoff`](../skills/handoff/SKILL.md) skill in this
repo does exactly this: `/handoff` writes a `HANDOFF.md` the next session can cold-start from, and
reads it back on resume.

This is also a good way to do research with Claude Web and then hand off its conclusions to a
Claude Code session; you can copy or save the handoff prompt into your Code session and have the
agent there read it to pick up the results.
