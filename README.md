# maxsize

`maxsize` is a macOS-first, agent-friendly CLI for resizing screenshots and
other images to configured maximum dimensions.

## Why

Modern dev workflows create huge screenshots, especially on 4K displays. That
is great for detail and terrible for tickets, QA handoffs, and everyday file
sharing.

`maxsize` exists to keep that workflow simple:
- save screenshots to a working directory
- define one or more profiles in config
- resize images that exceed a configured max width and/or max height
- return structured, machine-readable results that work well for agents

The tool is intentionally built for macOS and leans on native system tooling
where that keeps the design smaller and more predictable.

## Quickstart

### Install with `uv`

Run directly from the GitHub repository:

```bash
uv tool install git+ssh://[email protected]/lxkrmr/maxsize.git
```

If you prefer HTTPS:

```bash
uv tool install git+https://github.com/lxkrmr/maxsize.git
```

### Create config

Create a config file at:

```bash
mkdir -p ~/.config/maxsize
cp config.example.toml ~/.config/maxsize/config.toml
$EDITOR ~/.config/maxsize/config.toml
```

Example:

```toml
active_profile = "jira"

[profiles.jira]
working_dir = "/Users/me/Desktop/screenshots"
max_width = 1600
max_height = 1600
extensions = ["png"]
```

The config supports multiple profiles. A profile defines the working directory
and the resize limits used by the CLI.

### Verify local setup

```bash
maxsize doctor
```

The doctor command checks whether the config exists, whether the selected
profile is valid, and whether the local setup looks usable on macOS.

### Describe the CLI

```bash
maxsize describe
```

This prints a structured description of the CLI, config location, and command
surface.

### Resize files

```bash
maxsize run
```

Preview changes without mutating files:

```bash
maxsize run --dry-run
```

The CLI is designed for agents, so commands return structured JSON with clear
results and predictable fields.
