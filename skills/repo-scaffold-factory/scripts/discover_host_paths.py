"""Discover host-local paths for SDKs, engines, executables, and keystores.

This utility probes the current machine for tools that Scafforge templates
need at scaffold time.  It returns a flat dict of discovered paths (or None
when a tool is not found) so that ``bootstrap_repo_scaffold.py`` can populate
template placeholders with real values instead of hardcoded developer paths.

The script is intentionally pure-stdlib Python — no external dependencies.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def _which(name: str) -> str | None:
    return shutil.which(name)


def _home() -> Path:
    return Path.home()


def _is_executable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


# -- Blender -----------------------------------------------------------------

_BLENDER_CANDIDATE_DIRS: list[str] = [
    # Linux
    "/usr/bin",
    "/usr/local/bin",
    "/snap/bin",
    # macOS
    "/Applications/Blender.app/Contents/MacOS",
]


def discover_blender_executable() -> str | None:
    """Return the absolute path of the Blender binary, or None."""
    found = _which("blender")
    if found:
        return found

    home = _home()
    # ~/blender-*/blender  (common manual-install pattern)
    for candidate in sorted(home.glob("blender-*/blender"), reverse=True):
        if _is_executable(candidate):
            return str(candidate)

    for directory in _BLENDER_CANDIDATE_DIRS:
        candidate = Path(directory) / ("Blender" if "MacOS" in directory else "blender")
        if _is_executable(candidate):
            return str(candidate)

    return None


def discover_blender_mcp_project() -> str | None:
    """Return the path to the blender-agent MCP server project, or None."""
    env = os.environ.get("BLENDER_MCP_PROJECT")
    if env and Path(env).is_dir():
        return env

    home = _home()
    candidates = [
        home / "projects" / "blender-agent" / "mcp-server",
        home / "blender-agent" / "mcp-server",
        home / "src" / "blender-agent" / "mcp-server",
        home / "dev" / "blender-agent" / "mcp-server",
    ]
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "pyproject.toml").is_file():
            return str(candidate)

    return None


# -- Godot --------------------------------------------------------------------

def discover_godot_executable() -> str | None:
    """Return the command name or path of the Godot binary, or None."""
    for name in ("godot4", "godot"):
        found = _which(name)
        if found:
            return found

    home = _home()
    candidates = [
        home / ".local" / "bin" / "godot4",
        home / ".local" / "bin" / "godot",
        Path("/usr/local/bin/godot4"),
        Path("/usr/local/bin/godot"),
        Path("/snap/bin/godot"),
    ]
    if platform.system() == "Darwin":
        candidates.append(Path("/Applications/Godot.app/Contents/MacOS/Godot"))
    for candidate in candidates:
        if _is_executable(candidate):
            return str(candidate)

    return None


# -- Android / Keystore -------------------------------------------------------

def discover_android_sdk() -> str | None:
    """Return the Android SDK root, or None."""
    for var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        value = os.environ.get(var)
        if value and Path(value).is_dir():
            return value

    home = _home()
    candidates = [
        home / "Android" / "Sdk",
        home / "Library" / "Android" / "sdk",
    ]
    if platform.system() == "Windows":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            candidates.append(Path(local) / "Android" / "Sdk")
    for candidate in candidates:
        if candidate.is_dir():
            return str(candidate)

    return None


def discover_android_debug_keystore() -> str | None:
    """Return the path to an Android debug keystore, or None."""
    home = _home()
    candidates = [
        home / ".android" / "debug.keystore",
        home / ".local" / "share" / "godot" / "keystores" / "debug.keystore",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)

    return None


# -- Java ---------------------------------------------------------------------

def discover_java_home() -> str | None:
    """Return JAVA_HOME, or derive it from ``which java``."""
    env = os.environ.get("JAVA_HOME")
    if env and Path(env).is_dir():
        return env

    java = _which("java")
    if not java:
        return None
    try:
        resolved = Path(java).resolve()
        # java is typically at $JAVA_HOME/bin/java
        candidate = resolved.parent.parent
        if (candidate / "bin" / "java").exists():
            return str(candidate)
    except (OSError, ValueError):
        pass

    return None


# -- Aggregate ----------------------------------------------------------------

def discover_host_paths() -> dict[str, str | None]:
    """Run all discovery probes and return a flat dict of results."""
    return {
        "blender_executable": discover_blender_executable(),
        "blender_mcp_project": discover_blender_mcp_project(),
        "godot_executable": discover_godot_executable(),
        "android_debug_keystore": discover_android_debug_keystore(),
        "android_sdk_path": discover_android_sdk(),
        "java_home": discover_java_home(),
    }


def main() -> int:
    """Print discovered paths as JSON to stdout."""
    paths = discover_host_paths()
    json.dump(paths, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
