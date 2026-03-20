# maxsize

`maxsize` is an agent-friendly CLI for resizing screenshots and other images
to configured maximum dimensions.

## Why

Modern dev workflows create huge screenshots, especially on 4K displays. That
is great for detail and terrible for tickets, QA handoffs, and everyday file
sharing.

`maxsize` exists to keep that workflow simple:
- save screenshots to a working directory
- define one or more profiles in config
- resize images that exceed a configured max width and/or max height
- return structured, machine-readable results that work well for agents

The tool uses a small Python-based image processing stack to keep the design
predictable and easy to install with `uv` on macOS and Linux.

## Quickstart

### Requirements

- macOS or Linux
- `uv`

### Install with `uv`

Install directly from GitHub:

```bash
uv tool install git+https://github.com/lxkrmr/maxsize.git
```

This makes the `maxsize` command available without a global Python package
installation.

### Create config

Initialize a config file with a profile:

```bash
maxsize init --profile jira --working-dir /path/to/screenshots --max-width 1600 --max-height 1600
```

This creates `~/.config/maxsize/config.toml`.

Example result:

```toml
active_profile = "jira"

[profiles.jira]
working_dir = "/path/to/screenshots"
max_width = 1600
max_height = 1600
extensions = ["png"]
```

The config supports multiple profiles. A profile defines the working directory
and the resize limits used by the CLI.

If you prefer to start from an example file instead, copy
`config.example.toml` to `~/.config/maxsize/config.toml` and edit it.

### Verify local setup

```bash
maxsize doctor
```

The doctor command checks whether the config exists, whether the selected
profile is valid, and whether the local setup looks usable on supported
platforms. If no config exists yet, it returns a suggested `nextCommand` for
`maxsize init`.

### Describe the CLI

```bash
maxsize describe
```

This prints a structured description of the CLI, supported platforms, config
schema, command surface, exit-code semantics, known error codes, value
constraints, and example command outputs.

To get a minimal example config from the tool itself:

```bash
maxsize config-example
```

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

## License

MIT
