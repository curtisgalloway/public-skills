# AGENTS.md — public-skills

## Purpose

This repository contains agent skills intended for public sharing. Skills here are general-purpose and agent-neutral, though most have been tested primarily with Claude Code and Gemini.

## Privacy rules — read before committing

This is a **public** repository. Before staging or pushing any file, verify it contains none of the following:

- Hostnames, FQDNs, or IP addresses for private machines or networks
- Internal service names or URLs (e.g. `*.internal`, `*.local`, homelab domains)
- Email addresses, usernames, or account identifiers
- Local filesystem paths that reveal a username or home directory structure (use `~` or `<path>` placeholders)
- API keys, tokens, passwords, or any credential — even expired ones
- Organization-internal terminology, project codenames, or team names
- Vault names, secret item names, or any 1Password/secrets-manager path

If a skill was originally written for a private environment and you're porting it here, **scrub it first**. Replace private values with generic placeholders and add a comment explaining what to substitute.

## Skill structure

Each skill lives in `skills/<skill-name>/` and must contain:

- `SKILL.md` — purpose, trigger phrases, required tools, inputs/outputs, and any caveats
- Any supporting scripts or templates the skill needs

Skills should be self-contained. If a skill needs a third-party tool, call that dependency out clearly in `SKILL.md`.

## Writing portable skills

- Use generic placeholder names (`example.com`, `<your-host>`, `<path/to/file>`) instead of real values
- Avoid hardcoding shell paths — use `command -v` or `which` guards when a tool may not be present
- Prefer POSIX-compatible shell constructs; call out macOS/Linux differences explicitly
- Do not reference internal infrastructure, private repos, or personal accounts

## License

All skills in this repository are released under the Apache 2.0 license. Add the standard header to new source files:

```
# Copyright <year> contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
```
