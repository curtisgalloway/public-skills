# public-skills

A collection of reusable agent skills designed to be generally agent-neutral. Skills have been
developed and tested primarily with Google Antigravity (the `agy` CLI and the IDE) and Claude
Code, but are written to work with any agent that supports the skill/slash-command pattern.

The skills are packaged by theme. Each theme is a directory under `plugins/`, a plugin in this
repo's Claude Code marketplace, and has its own README with the details.

## Themes

| Plugin | What it covers | Skills |
| --- | --- | --- |
| [`hardware-lab`](plugins/hardware-lab/README.md) | USB traffic capture, decoding and protocol reverse-engineering with a Cynthion; bench instruments | `cynthion-setup`, `cynthion-capture`, `cynthion-pcap-decode`, `cynthion-reverse-engineer`, `usb-device-profile`, `mcci-3411`, `bus-pirate`, `siglent-scope` |
| [`driver-porting`](plugins/driver-porting/README.md) | Clean-room driver specs from encumbered source, source-anchored specs and reviews for code you own, board experts | `os-investigator`, `cleanroom-spec`, `cleanroom-implementer`, `anchored-peripheral-spec`, `reference-driver-review`, `rpi-expert`, `indiedroid-nova-expert` |
| [`agent-workflow`](plugins/agent-workflow/README.md) | Working with a coding agent over time: design partnership, loop safety, handoffs, summaries, session learning, document review, portable skill authoring | `design-partner`, `intern-mode`, `handoff`, `wrapup`, `learn`, `teach`, `claude-session-transcript`, `gdoc-review-loop`, `agent-agnostic-skills` |
| [`dev-tools`](plugins/dev-tools/README.md) | Engineering utilities | `jj`, `dep-quality` |

`public-skills` is a fifth marketplace entry that bundles all four. Install either it or the
themed plugins, not both, or every skill loads twice.

Each skill lives in `plugins/<theme>/skills/<name>/` and contains at minimum a `SKILL.md`
describing its purpose, triggers, and behavior. Many ship supporting scripts, references, or
templates alongside it.

### Fuchsia — its own repo

The Fuchsia skills live in
**[curtisgalloway/fuchsia-skills](https://github.com/curtisgalloway/fuchsia-skills)**:
checking out the tree, bridging its Gemini-oriented in-tree agent config into Claude Code,
running several workstreams on one machine, deep source questions, driver bind debugging, and
the hardware bench and boot-test CI pair. They hand off to `driver-porting`'s skills by name.

```
/plugin marketplace add curtisgalloway/fuchsia-skills
/plugin install fuchsia-skills@fuchsia-skills
```

## Installing

Most skills assume a Unix-like shell (macOS or Linux), standard CLI tools (`git`, `curl`, …)
on `PATH`, and whatever skill-specific dependencies their own docs call out.

### Claude Code

This repo is a Claude Code plugin marketplace (`.claude-plugin/marketplace.json`). In a
session, or with the `claude plugin` CLI outside one:

```
/plugin marketplace add curtisgalloway/public-skills
/plugin install hardware-lab@public-skills
/plugin install driver-porting@public-skills
/plugin install agent-workflow@public-skills
/plugin install dev-tools@public-skills
```

Install the themes you want; `/plugin install public-skills@public-skills` takes all of them
as one plugin. For a local clone, add the clone directory as the marketplace instead:

```
/plugin marketplace add /path/to/public-skills
/plugin install hardware-lab@public-skills
```

### Any agent that reads `SKILL.md` directories

The layout follows the Agent Skills convention, so installers that scan a repo for
`SKILL.md` directories, such as Vercel's skills CLI, pick every skill up:

```
npx skills add curtisgalloway/public-skills
```

### Antigravity

Skills are plain directories. Clone the repo and put the skills you want where your build
discovers them: `~/.gemini/antigravity/skills/` for user-level, `<workspace>/.agents/skills/`
for one project, or inside a plugin's `skills/` directory:

```bash
git clone https://github.com/curtisgalloway/public-skills ~/src/public-skills
ln -s ~/src/public-skills/plugins/driver-porting/skills/cleanroom-spec ~/.gemini/antigravity/skills/cleanroom-spec
```

Check with `/skills` that they loaded. Skills that are subagent roles (`os-investigator`, and
the shipped `cleanroom-implementer/assets/driver-implementer.md`) install instead as
`<workspace>/.agents/agents/<name>.md` with `subagent: true` in the frontmatter, and show up
under `/agents`. Workspace-wide instructions go in `AGENTS.md` at the workspace root, or as
rules under `.agent/rules/`.

Antigravity has relocated skills, hooks and settings between releases, so confirm the paths
your build actually reads before assuming an install took; the slash commands above are the
quickest check.

> Skills that read agent transcripts (`learn`, `teach`, `wrapup`, `claude-session-transcript`)
> are still written against Claude Code's session layout and have not been ported.

## Guides

- [How To Claude](docs/how-to-claude.md) — session hygiene for working with Claude: one topic
  per session, keeping context short, thinking before the first message, knowing when to start
  over, and handing off between sessions (the reasoning behind the `handoff` skill).

## License

Apache 2.0 — see [LICENSE](LICENSE).
