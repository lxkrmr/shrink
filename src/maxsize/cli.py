from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer

from maxsize import __version__

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Agent-first macOS CLI for resizing screenshots to configured maximum dimensions.",
)

CONFIG_DIR = Path.home() / ".config" / "maxsize"
CONFIG_PATH = CONFIG_DIR / "config.toml"
DEFAULT_PROFILE_NAME = "default"
DEFAULT_EXTENSIONS = ["png"]


@dataclass
class ProfileConfig:
    name: str
    working_dir: Path
    max_width: int | None
    max_height: int | None
    extensions: list[str]


class MaxsizeError(Exception):
    pass


class ConfigError(MaxsizeError):
    pass


def emit_json(payload: dict[str, Any], *, exit_code: int = 0) -> None:
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    raise typer.Exit(exit_code)


def normalize_extensions(raw_extensions: Any) -> list[str]:
    if raw_extensions is None:
        return DEFAULT_EXTENSIONS.copy()
    if not isinstance(raw_extensions, list) or not raw_extensions:
        raise ConfigError("Profile extensions must be a non-empty list of strings.")

    normalized: list[str] = []
    for item in raw_extensions:
        if not isinstance(item, str) or not item.strip():
            raise ConfigError("Each extension must be a non-empty string.")
        value = item.strip().lower().lstrip(".")
        normalized.append(value)
    return normalized


def validate_limit(name: str, value: Any) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or value <= 0:
        raise ConfigError(f"{name} must be a positive integer when provided.")
    return value


def load_config(config_path: Path = CONFIG_PATH) -> tuple[dict[str, Any], dict[str, Any]]:
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        raw = tomllib.loads(config_path.read_text())
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in config file: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("Config root must be a TOML table.")

    return raw, raw.get("profiles", {})


def render_config_toml(
    *,
    profile: str,
    working_dir: Path,
    max_width: int | None,
    max_height: int | None,
    extensions: list[str],
) -> str:
    lines = [f'active_profile = "{profile}"', "", f"[profiles.{profile}]", f'working_dir = "{working_dir}"']

    if max_width is not None:
        lines.append(f"max_width = {max_width}")
    if max_height is not None:
        lines.append(f"max_height = {max_height}")

    rendered_extensions = ", ".join(f'"{ext}"' for ext in extensions)
    lines.append(f"extensions = [{rendered_extensions}]")
    lines.append("")
    return "\n".join(lines)


def resolve_profile(config_path: Path, selected_profile: str | None) -> ProfileConfig:
    raw_config, profiles = load_config(config_path)

    if not isinstance(profiles, dict) or not profiles:
        raise ConfigError("Config must define at least one profile under [profiles.<name>].")

    active_profile = selected_profile or raw_config.get("active_profile")
    if not active_profile:
        if len(profiles) == 1:
            active_profile = next(iter(profiles.keys()))
        else:
            raise ConfigError("No active_profile set and no --profile provided.")

    if not isinstance(active_profile, str) or active_profile not in profiles:
        raise ConfigError(f"Unknown profile: {active_profile}")

    profile_data = profiles[active_profile]
    if not isinstance(profile_data, dict):
        raise ConfigError(f"Profile '{active_profile}' must be a TOML table.")

    working_dir_raw = profile_data.get("working_dir")
    if not isinstance(working_dir_raw, str) or not working_dir_raw.strip():
        raise ConfigError(f"Profile '{active_profile}' must define a non-empty working_dir.")

    max_width = validate_limit("max_width", profile_data.get("max_width"))
    max_height = validate_limit("max_height", profile_data.get("max_height"))
    if max_width is None and max_height is None:
        raise ConfigError(
            f"Profile '{active_profile}' must define at least one of max_width or max_height."
        )

    return ProfileConfig(
        name=active_profile,
        working_dir=Path(working_dir_raw).expanduser(),
        max_width=max_width,
        max_height=max_height,
        extensions=normalize_extensions(profile_data.get("extensions")),
    )


def sips_properties(path: Path) -> dict[str, int]:
    result = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise MaxsizeError(result.stderr.strip() or f"Failed to inspect image: {path}")

    width: int | None = None
    height: int | None = None
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("pixelWidth:"):
            width = int(stripped.split(":", 1)[1].strip())
        elif stripped.startswith("pixelHeight:"):
            height = int(stripped.split(":", 1)[1].strip())

    if width is None or height is None:
        raise MaxsizeError(f"Could not parse image dimensions for {path}")

    return {"width": width, "height": height}


def file_snapshot(path: Path) -> dict[str, int]:
    props = sips_properties(path)
    return {
        "width": props["width"],
        "height": props["height"],
        "bytes": path.stat().st_size,
    }


def list_candidate_files(profile: ProfileConfig) -> list[Path]:
    if not profile.working_dir.exists():
        return []

    allowed = {f".{ext.lower()}" for ext in profile.extensions}
    return sorted(
        path
        for path in profile.working_dir.iterdir()
        if path.is_file() and path.suffix.lower() in allowed
    )


def calculate_target_size(
    width: int,
    height: int,
    max_width: int | None,
    max_height: int | None,
) -> tuple[int, int]:
    scale = 1.0
    if max_width is not None:
        scale = min(scale, max_width / width)
    if max_height is not None:
        scale = min(scale, max_height / height)

    if scale >= 1.0:
        return width, height

    target_width = max(1, math.floor(width * scale))
    target_height = max(1, math.floor(height * scale))
    return target_width, target_height


def resize_in_place(path: Path, target_width: int, target_height: int) -> None:
    result = subprocess.run(
        ["sips", "--resampleHeightWidth", str(target_height), str(target_width), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise MaxsizeError(result.stderr.strip() or f"Failed to resize image: {path}")


@app.command()
def init(
    profile: str = typer.Option(DEFAULT_PROFILE_NAME, help="Profile name to create."),
    working_dir: Path = typer.Option(..., help="Working directory for images."),
    max_width: int | None = typer.Option(None, help="Maximum allowed width in pixels."),
    max_height: int | None = typer.Option(None, help="Maximum allowed height in pixels."),
    extensions: list[str] | None = typer.Option(None, help="Allowed file extensions. Repeat the option to add more values."),
    force: bool = typer.Option(False, help="Overwrite an existing config file."),
) -> None:
    try:
        validated_max_width = validate_limit("max_width", max_width)
        validated_max_height = validate_limit("max_height", max_height)
        if validated_max_width is None and validated_max_height is None:
            raise ConfigError("At least one of --max-width or --max-height must be provided.")

        normalized_extensions = normalize_extensions(extensions)
        normalized_working_dir = working_dir.expanduser()
        if not str(profile).strip():
            raise ConfigError("Profile name must be a non-empty string.")
        if not str(normalized_working_dir).strip():
            raise ConfigError("Working directory must be a non-empty path.")
    except ConfigError as exc:
        emit_json(
            {
                "tool": "maxsize",
                "version": __version__,
                "command": "init",
                "status": "error",
                "profile": profile,
                "configPath": str(CONFIG_PATH),
                "errors": [{"code": "INVALID_INIT_OPTIONS", "message": str(exc)}],
            },
            exit_code=1,
        )

    if CONFIG_PATH.exists() and not force:
        emit_json(
            {
                "tool": "maxsize",
                "version": __version__,
                "command": "init",
                "status": "error",
                "profile": profile,
                "configPath": str(CONFIG_PATH),
                "errors": [
                    {
                        "code": "CONFIG_ALREADY_EXISTS",
                        "message": f"Config file already exists: {CONFIG_PATH}",
                    }
                ],
            },
            exit_code=1,
        )

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        render_config_toml(
            profile=profile,
            working_dir=normalized_working_dir,
            max_width=validated_max_width,
            max_height=validated_max_height,
            extensions=normalized_extensions,
        )
    )

    emit_json(
        {
            "tool": "maxsize",
            "version": __version__,
            "command": "init",
            "status": "ok",
            "profile": profile,
            "configPath": str(CONFIG_PATH),
            "createdConfigDir": str(CONFIG_DIR),
            "overwroteExistingConfig": force,
            "config": {
                "activeProfile": profile,
                "workingDir": str(normalized_working_dir),
                "maxWidth": validated_max_width,
                "maxHeight": validated_max_height,
                "extensions": normalized_extensions,
            },
            "nextCommand": "maxsize doctor",
            "errors": [],
        }
    )


@app.command()
def describe() -> None:
    emit_json(
        {
            "tool": "maxsize",
            "version": __version__,
            "platform": "macOS",
            "config": {
                "path": str(CONFIG_PATH),
                "format": "toml",
                "supportsProfiles": True,
            },
            "commands": {
                "init": {
                    "mutatesFiles": True,
                    "summary": "Create an initial config file for a profile.",
                    "options": {
                        "profile": "Profile name to create.",
                        "workingDir": "Working directory for matching images.",
                        "maxWidth": "Optional maximum width in pixels.",
                        "maxHeight": "Optional maximum height in pixels.",
                        "extensions": "Allowed file extensions.",
                        "force": "Overwrite an existing config file.",
                    },
                },
                "describe": {
                    "mutatesFiles": False,
                    "summary": "Describe the CLI, config, and output model.",
                },
                "doctor": {
                    "mutatesFiles": False,
                    "summary": "Validate macOS prerequisites and local configuration.",
                },
                "run": {
                    "mutatesFiles": True,
                    "summary": "Resize matching images in place when they exceed configured limits.",
                    "options": {
                        "profile": "Optional profile override.",
                        "dryRun": "Report planned changes without mutating files.",
                    },
                },
            },
            "resultSchema": {
                "tool": "string",
                "version": "string",
                "command": "string",
                "status": "ok | error",
                "profile": "string | null",
                "images": "array",
                "errors": "array",
            },
        }
    )


@app.command()
def doctor(
    profile: str | None = typer.Option(None, help="Profile name override."),
) -> None:
    errors: list[dict[str, str]] = []
    checks: list[dict[str, Any]] = []
    resolved_profile: ProfileConfig | None = None
    next_command: str | None = None

    is_macos = sys.platform == "darwin"
    checks.append({"name": "platform", "ok": is_macos, "expected": "darwin", "actual": sys.platform})
    if not is_macos:
        errors.append({"code": "UNSUPPORTED_PLATFORM", "message": "maxsize currently supports macOS only."})

    sips_path = shutil.which("sips")
    checks.append({"name": "sips", "ok": sips_path is not None, "path": sips_path})
    if sips_path is None:
        errors.append({"code": "MISSING_SIPS", "message": "Required macOS tool 'sips' was not found."})

    config_exists = CONFIG_PATH.exists()
    checks.append({"name": "config", "ok": config_exists, "path": str(CONFIG_PATH)})
    if not config_exists:
        errors.append({"code": "MISSING_CONFIG", "message": f"Config file not found: {CONFIG_PATH}"})
        next_command = "maxsize init --working-dir /path/to/screenshots --max-width 1600 --max-height 1600"
    else:
        try:
            resolved_profile = resolve_profile(CONFIG_PATH, profile)
            checks.append(
                {
                    "name": "profile",
                    "ok": True,
                    "profile": resolved_profile.name,
                    "workingDir": str(resolved_profile.working_dir),
                    "maxWidth": resolved_profile.max_width,
                    "maxHeight": resolved_profile.max_height,
                    "extensions": resolved_profile.extensions,
                }
            )
            checks.append(
                {
                    "name": "working_dir",
                    "ok": resolved_profile.working_dir.exists() and resolved_profile.working_dir.is_dir(),
                    "path": str(resolved_profile.working_dir),
                }
            )
            if not resolved_profile.working_dir.exists() or not resolved_profile.working_dir.is_dir():
                errors.append(
                    {
                        "code": "INVALID_WORKING_DIR",
                        "message": f"Working directory does not exist: {resolved_profile.working_dir}",
                    }
                )
        except ConfigError as exc:
            checks.append({"name": "profile", "ok": False})
            errors.append({"code": "INVALID_CONFIG", "message": str(exc)})

    emit_json(
        {
            "tool": "maxsize",
            "version": __version__,
            "command": "doctor",
            "status": "ok" if not errors else "error",
            "profile": resolved_profile.name if resolved_profile else profile,
            "configPath": str(CONFIG_PATH),
            "checks": checks,
            "nextCommand": next_command,
            "errors": errors,
        },
        exit_code=0 if not errors else 1,
    )


@app.command()
def run(
    profile: str | None = typer.Option(None, help="Profile name override."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report changes without resizing files."),
) -> None:
    try:
        resolved_profile = resolve_profile(CONFIG_PATH, profile)
    except ConfigError as exc:
        emit_json(
            {
                "tool": "maxsize",
                "version": __version__,
                "command": "run",
                "status": "error",
                "profile": profile,
                "images": [],
                "errors": [{"code": "INVALID_CONFIG", "message": str(exc)}],
            },
            exit_code=1,
        )

    if sys.platform != "darwin":
        emit_json(
            {
                "tool": "maxsize",
                "version": __version__,
                "command": "run",
                "status": "error",
                "profile": resolved_profile.name,
                "images": [],
                "errors": [{"code": "UNSUPPORTED_PLATFORM", "message": "maxsize currently supports macOS only."}],
            },
            exit_code=1,
        )

    if shutil.which("sips") is None:
        emit_json(
            {
                "tool": "maxsize",
                "version": __version__,
                "command": "run",
                "status": "error",
                "profile": resolved_profile.name,
                "images": [],
                "errors": [{"code": "MISSING_SIPS", "message": "Required macOS tool 'sips' was not found."}],
            },
            exit_code=1,
        )

    if not resolved_profile.working_dir.exists() or not resolved_profile.working_dir.is_dir():
        emit_json(
            {
                "tool": "maxsize",
                "version": __version__,
                "command": "run",
                "status": "error",
                "profile": resolved_profile.name,
                "images": [],
                "errors": [
                    {
                        "code": "INVALID_WORKING_DIR",
                        "message": f"Working directory does not exist: {resolved_profile.working_dir}",
                    }
                ],
            },
            exit_code=1,
        )

    images: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for path in list_candidate_files(resolved_profile):
        try:
            before = file_snapshot(path)
            target_width, target_height = calculate_target_size(
                before["width"],
                before["height"],
                resolved_profile.max_width,
                resolved_profile.max_height,
            )

            if target_width == before["width"] and target_height == before["height"]:
                images.append(
                    {
                        "path": str(path),
                        "resized": False,
                        "current": before,
                    }
                )
                continue

            if dry_run:
                images.append(
                    {
                        "path": str(path),
                        "resized": False,
                        "wouldResize": True,
                        "before": before,
                        "target": {
                            "width": target_width,
                            "height": target_height,
                        },
                    }
                )
                continue

            resize_in_place(path, target_width, target_height)
            after = file_snapshot(path)
            images.append(
                {
                    "path": str(path),
                    "resized": True,
                    "before": before,
                    "after": after,
                }
            )
        except MaxsizeError as exc:
            errors.append({"code": "IMAGE_PROCESSING_FAILED", "message": f"{path}: {exc}"})

    emit_json(
        {
            "tool": "maxsize",
            "version": __version__,
            "command": "run",
            "status": "ok" if not errors else "error",
            "profile": resolved_profile.name,
            "dryRun": dry_run,
            "workingDir": str(resolved_profile.working_dir),
            "constraints": {
                "maxWidth": resolved_profile.max_width,
                "maxHeight": resolved_profile.max_height,
                "extensions": resolved_profile.extensions,
            },
            "images": images,
            "errors": errors,
        },
        exit_code=0 if not errors else 1,
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
