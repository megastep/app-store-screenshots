#!/usr/bin/env python3
"""
Scaffold the base Next.js project used by the App Store screenshots skill.

By default this prints the commands it would run. Pass --execute to actually run
them. It detects the package manager using the skill's preferred priority:
bun > pnpm > yarn > npm.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


CREATE_ARGS = [
    "--typescript",
    "--tailwind",
    "--app",
    "--src-dir",
    "--no-eslint",
    "--import-alias",
    "@/*",
]


def detect_package_manager(preferred: str | None = None) -> str:
    if preferred:
        return preferred
    for candidate in ("bun", "pnpm", "yarn", "npm"):
        if shutil.which(candidate):
            return candidate
    raise RuntimeError("No supported package manager found. Expected bun, pnpm, yarn, or npm.")


def build_commands(package_manager: str, project_root: Path) -> list[list[str]]:
    root_arg = str(project_root)
    commands: list[list[str]] = []

    package_json_exists = (project_root / "package.json").exists()
    if not package_json_exists:
        if package_manager == "bun":
            commands.append(["bunx", "create-next-app@latest", root_arg, *CREATE_ARGS])
        elif package_manager == "pnpm":
            commands.append(["pnpx", "create-next-app@latest", root_arg, *CREATE_ARGS])
        elif package_manager == "yarn":
            commands.append(["yarn", "create", "next-app", root_arg, *CREATE_ARGS])
        else:
            commands.append(["npx", "create-next-app@latest", root_arg, *CREATE_ARGS])

    if package_manager == "bun":
        commands.append(["bun", "add", "html-to-image"])
    elif package_manager == "pnpm":
        commands.append(["pnpm", "add", "html-to-image"])
    elif package_manager == "yarn":
        commands.append(["yarn", "add", "html-to-image"])
    else:
        commands.append(["npm", "install", "html-to-image"])

    return commands


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold the Next.js project for the App Store screenshot generator.")
    parser.add_argument("--project-root", default=".", help="Target project root. Default: current directory")
    parser.add_argument("--package-manager", choices=("bun", "pnpm", "yarn", "npm"), help="Override auto-detected package manager")
    parser.add_argument("--execute", action="store_true", help="Run the commands instead of only printing them")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    package_manager = detect_package_manager(args.package_manager)
    commands = build_commands(package_manager, project_root)

    print(f"[info] package manager: {package_manager}")
    for command in commands:
        print("[cmd]", " ".join(command))

    if not args.execute:
        return 0

    project_root.mkdir(parents=True, exist_ok=True)
    for index, command in enumerate(commands):
        cwd = project_root.parent if index == 0 and not (project_root / "package.json").exists() else project_root
        subprocess.run(command, cwd=cwd, check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
