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

When you start a new session, Claude reads its default prompt ("You are a helpful agent…") and,
(mostly) any memory it knows about you, as well as any per-project context (like the `CLAUDE.md`
file in a code project), before you type your first message.

Then, every time you type a new message, it essentially does that all over again and reads the
past conversation up to the current message. Each time you type something, Claude reads a longer
and longer session text, up to its context limit (which is on the order of hundreds of thousands
to a million words, depending on the model, and maybe your plan). So the longer the conversation
gets, the more Claude has to read every time to keep up with what's going on.

I'm leaving out some detail here: Claude can, and will, compact its context when it gets full by
summarizing the conversation so far and reading that new shorter summary, but I think it's better
to manage its context yourself rather than relying on compaction.

Remember this for later on: my last tip about how to hand off between sessions might be the most
useful one.

## One topic per session

Claude does better when you keep each session focused on one major topic. This is especially true
if you try to change the topic at the end of a long session. All that previous session text tends
to crowd out the later discussion, so Claude can end up focusing too much of its attention on the
old topic and not on the new.

If you change topics, use `/clear` in Claude Code, or quit and start a new session everywhere
else, to flush out the context and start over.

## Don't let sessions get too long

Even if you keep each session to one topic, it's still better to keep a single session from
getting too long. As the context window fills up, Claude has a harder and harder time remembering
all the things at the beginning of the conversation, including really important things like
memories or your `CLAUDE.md` instructions. It will tend to want to use everything that's in its
context window which might not be helpful as you move through your discussion.

Keep an eye on the size of the context window; in Claude Code you can use the `/context` command
to check on it. Once it gets over half full, consider wrapping things up and starting a new
session (or clearing the context).

## Do some thinking up front before your first message

It's tempting to just start a conversation with what's on the top of your mind, and expect to add
detail as you go along. But it really pays off to think about what you want to accomplish before
you type your first message.

Claude puts a lot of weight on the very first thing you tell it, so if you make your first prompt
a detailed description of what you want to accomplish, that will give it a much better foundation
to build on for the whole conversation. A clean first turn produces clean context for every later
turn.

That's not to say that more is always better. Pasting in 500 lines of logs as your first message
isn't a good idea. Instead, think about how you would write a memo to a smart colleague:

- **Set constraints and non-goals.** What are you trying to accomplish? What are you specifically
  not trying to accomplish?
- **Point to prior art.** Are there other examples of the kind of thing you're working on? Be
  specific if you can; links are great resources.
- **Make the goal clear.** Don't just describe the next task; talk about the goal you're trying to
  achieve. Adding a goal helps guide Claude's judgement about how to structure the tasks along the
  way.
- **When are you done?** What is the end state you want to achieve: what tests should pass? What
  specifically can you check to know when to stop? Otherwise Claude might just guess when it
  should keep going versus declaring victory.

## When to give up

When things go south in a conversation, it's natural to keep trying to correct it. But that can be
counter-productive. Because Claude always reads everything in the whole history of the
conversation, if the earlier part has gone sideways, that will continue to pollute Claude's
context in spite of your attempts to correct it — Claude can't "forget" the part that you're
trying to correct.

Instead, when that happens, just give up and start over with a new conversation. It's better to
start again with a fresh statement of what you're trying to accomplish, and you can use the failed
attempt as feedback for you to refine your initial prompt and include the detail that might help
Claude to avoid whatever pitfalls led it astray in the previous attempt.

## Teach Claude how to hand off between sessions

If you take anything away from this guide, this is the one to remember.

When you start a new session, Claude knows nothing about your previous conversation, except what
it's explicitly committed to memory. This is a problem if you follow my advice on keeping sessions
short!

The solution is to have Claude write a "handoff prompt" for its next incarnation. The basic idea is
to tell Claude to write a prompt for an agent on how to continue from the current state of the
conversation. If it has important information that isn't saved somewhere, it should either save it
or include it directly in the handoff. The [`handoff`](../plugins/agent-workflow/skills/handoff/SKILL.md) skill in this
repo does exactly this: `/handoff` writes a `HANDOFF.md` the next session can cold-start from, and
reads it back on resume.

This is also a good way to do research with Claude Web and then hand off its conclusions to a
Claude Code session; you can copy or save the handoff prompt into your Code session and have the
agent there read it to pick up the results.
