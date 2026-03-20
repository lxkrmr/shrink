# AGENTS.md

Project: `maxsize`

## Purpose
`maxsize` is an agent-first CLI for **macOS** that resizes screenshots and
other images to a configured maximum size.

The tool is:
- built for **AI/LLM agents**
- **JSON-first** in its output
- strongly inspired by **MCP protocol ideas**
- local, simple, and predictable

## Key product decisions
- The target platform is **macOS**.
- Image processing may rely on built-in macOS tools, especially `sips`.
- The CLI UX is **agent-first**: structured, stable, and machine-readable.
- Responses should be clear, complete, and reliable.
- The tool should communicate explicitly that it is intended for macOS.

## Architecture guardrails
- Language/runtime: **Python with `uv`**.
- No global Python package installation.
- CLI foundation: **Typer**.
- Installation should work directly from the GitHub repo via `uv`.
- Configuration lives in `~/.config/maxsize/` as **TOML**.
- The config supports **multiple profiles**.
- There is a `doctor` command that validates the local configuration.
- Resize rules must support at least:
  - maximum width
  - maximum height
- Working directory and limits come from config, not from hardcoded user
  workflows.

## Agent/CLI design
We strongly follow agent-safe CLI principles:
- prefer **machine-readable stdout**, especially JSON
- reserve **stderr** for warnings, errors, and human-readable hints
- no unnecessary decorative output
- deterministic field names
- sensible exit codes
- `--help` should remain useful for humans, but output formats must be easy for
  agents to parse
- a `describe`/schema-oriented approach is encouraged
- `doctor` should report in a structured way what is missing or misconfigured

## Agent identity and collaboration log
- There is a file named `LEARNING_AND_SHARING.md` in the project root.
- This file is a Star-Trek-Lower-Decks-style "Agent's Log": casual,
  personal, slightly blog-like.
- Agents maintain this file autonomously.
- When something noteworthy happens (error, misunderstanding, insight, real
  lesson), add an entry.
- Each entry contains:
  - a heading in the style `## Agent's Log — Terminal Time: YYYY.MM.DD | <model-name>`
  - its own title line directly below
  - prose written from the agent perspective, like a Lower Decks crew member
  - the concrete model name of the current session if known; otherwise keep the
    `<model-name>` placeholder
- New entries are added **autonomously**, but only when there is a real reason.
- The language is **English**.
- The tone is casual, honest, personal, slightly chaotic, observant, and if
  needed a little annoyed.
- Entries should read more like small stories than status reports.
- Avoid bullet lists inside entries unless the voice really needs them.
- Entries may be longer when the moment has enough substance.
- End every entry with a line starting with `Standing order:` containing the
  lasting lesson.
- Wrap prose lines to roughly 80 characters so terminals and diffs stay
  readable.
- `LEARNING_AND_SHARING.md` contains an insertion marker comment; insert new
  entries directly **below** that marker, newest first.
- The guidance should stay general enough that future sessions can follow it
  without extra interpretation.

## Files and docs
- `README.md` describes:
  1. Name
  2. Why
  3. Quickstart
- `CONTRIBUTOR.md` contains contribution rules, especially commit conventions.
- Do **not** duplicate commit conventions in this document; refer to
  `CONTRIBUTOR.md` instead.

## Commit policy
- Prefer small, meaningful commits.
- Commit messages follow **Conventional Commits** with **scope**.
- Details live in `CONTRIBUTOR.md`.

## Working style for agents
- Read first, then change.
- Keep changes small and understandable.
- Respect the existing structure.
- Prefer KISS.
- For CLI decisions, always ask:
  - is the output machine-readable?
  - is it stable?
  - is it easier for agents to consume than for humans?
- When human ergonomics and agent ergonomics conflict, prioritize agent
  ergonomics at the core without making the CLI unnecessarily unfriendly.

## Still open / to be specified
- final config schema
- profile selection mechanism
- exact JSON output format
- exit code semantics
- handling of unsupported file types
- handling of in-place resize vs. dry-run vs. future safety mechanisms
