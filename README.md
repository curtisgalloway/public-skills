# public-skills

Reusable skills for coding agents. They are developed and tested mainly with Claude Code and
Google Antigravity (the `agy` CLI and the IDE), and are written to work with any agent that
supports skills or slash commands. Terms are defined in the [glossary](GLOSSARY.md).

## Plugins

Skills are grouped by theme into plugins, each with its own README. Three live under
`plugins/` here; `driver-porting` lives in its own repository,
[driver-lab](https://github.com/curtisgalloway/driver-lab), and this marketplace's entry for it
points there.

| Plugin | What it covers | Skills |
| --- | --- | --- |
| [`hardware-lab`](plugins/hardware-lab/README.md) | USB traffic capture, decoding and protocol reverse-engineering with a Cynthion; bench instruments | `cynthion-setup`, `cynthion-capture`, `cynthion-pcap-decode`, `cynthion-reverse-engineer`, `usb-device-profile`, `mcci-3411`, `bus-pirate`, `siglent-scope` |
| [`driver-porting`](https://github.com/curtisgalloway/driver-lab) (in driver-lab) | Clean-room driver specs from encumbered source, source-anchored specs and reviews for code you own, board specs and board experts | `os-investigator`, `cleanroom-spec`, `cleanroom-implementer`, `anchored-peripheral-spec`, `reference-driver-review`, `board-expert`, `rpi-expert`, `rpi4-expert`, `indiedroid-nova-expert`, `pixel10-expert`, `board-spec-scaffold`, `spec-verifier` |
| [`agent-workflow`](plugins/agent-workflow/README.md) | Working with a coding agent over time: design partnership, counterpart consultation, project planning, loop safety, lab notebooks, handoffs, session learning, document review, portable skill authoring | `design-partner`, `consult`, `project-plan`, `orchestrate-milestones`, `quota-strategy`, `lab-notebook`, `intern-mode`, `handoff`, `learn`, `teach`, `claude-session-transcript`, `gdoc-review-loop`, `agent-agnostic-skills` |
| [`dev-tools`](plugins/dev-tools/README.md) | Engineering utilities | `jj`, `dep-quality`, `cli-conventions`, `review-swarm`, `release-train` |

One more plugin, `everything`, bundles the three themes kept here; it cannot include
`driver-porting`, which is installed on its own. Install `everything` or the themed plugins,
not both, or every skill loads twice.

Each skill is a directory, `plugins/<theme>/skills/<name>/`, holding a `SKILL.md` and often
scripts, references, or templates.

## Installing

Most skills need a Unix-like shell (macOS or Linux), common tools such as `git` and `curl`,
and any dependencies their own docs list. The skills that read agent transcripts (`learn`,
`teach`, `claude-session-transcript`) still assume Claude Code's session layout and have not
been ported to other agents.

### Claude Code

This repo is a plugin marketplace. In a session, or with the `claude plugin` CLI, add it and
install the themes you want:

```
/plugin marketplace add curtisgalloway/public-skills
/plugin install hardware-lab@curtisg-skills
/plugin install driver-porting@curtisg-skills
/plugin install agent-workflow@curtisg-skills
/plugin install dev-tools@curtisg-skills
```

Or install `everything@curtisg-skills` to get the three themes kept here, plus
`driver-porting@curtisg-skills` if you want it. To use a local clone, pass its path to
`/plugin marketplace add` instead.

### Codex

Codex reads the same marketplace. From a shell:

```
codex plugin marketplace add curtisgalloway/public-skills
codex plugin add hardware-lab@curtisg-skills
codex plugin add driver-porting@curtisg-skills
codex plugin add agent-workflow@curtisg-skills
codex plugin add dev-tools@curtisg-skills
```

As with Claude Code, `everything@curtisg-skills` gets the three themes kept here, and a local clone's path works
in place of `curtisgalloway/public-skills`. Codex also loads any skill directory you link into
`~/.agents/skills/`.

### Any agent that reads `SKILL.md` directories

The layout follows the Agent Skills convention, so installers that scan a repo for skill
directories, such as Vercel's skills CLI, pick up every skill:

```
npx skills add curtisgalloway/public-skills
```

### Antigravity

Clone the repo and link the skills you want into a directory Antigravity scans:
`~/.gemini/antigravity/skills/` (all projects), `<workspace>/.agents/skills/` (one project),
or a plugin's `skills/` directory.

```bash
git clone https://github.com/curtisgalloway/public-skills ~/src/public-skills
ln -s ~/src/public-skills/plugins/agent-workflow/skills/handoff ~/.gemini/antigravity/skills/handoff
```

Run `/skills` to confirm they loaded. Antigravity has moved these paths between releases, so
check before assuming an install worked.

In [driver-lab](https://github.com/curtisgalloway/driver-lab), two pieces of `driver-porting`
are subagent roles, not skills: `os-investigator` and
`cleanroom-implementer/assets/driver-implementer.md`. Install each as
`<workspace>/.agents/agents/<name>.md` with `subagent: true` in the frontmatter; they appear
under `/agents`. Workspace-wide instructions go in `AGENTS.md` at the workspace root or in
`.agent/rules/`.

## Related

- **[fuchsia-skills](https://github.com/curtisgalloway/fuchsia-skills)**: Fuchsia-specific
  skills for checking out the source tree, bridging its Gemini-oriented agent config into
  Claude Code, running parallel workstreams, answering deep source questions, debugging driver
  binding, and the hardware bench and boot-test CI. They hand off to `driver-porting` skills
  (in [driver-lab](https://github.com/curtisgalloway/driver-lab)) by name.

  ```
  /plugin marketplace add curtisgalloway/fuchsia-skills
  /plugin install fuchsia-skills@fuchsia-skills
  ```

- **[QBranch](https://github.com/curtisgalloway/qbranch)**: the tool I use to manage skills,
  plugins, and agent config across machines.

- **[How To Claude](docs/how-to-claude.md)**: session hygiene for working with Claude. One
  topic per session, short context, thinking before the first message, knowing when to start
  over, and handing off between sessions (the reasoning behind the `handoff` skill).

## License

Apache 2.0. See [LICENSE](LICENSE).
