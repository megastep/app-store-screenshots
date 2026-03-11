#!/usr/bin/env python3
"""
Copy the reusable support files for the App Store screenshots skill into a project.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def copy_file(source: Path, destination: Path, overwrite: bool) -> None:
    if destination.exists() and not overwrite:
        print(f"[skip] {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    print(f"[copy] {source.name} -> {destination}")


def write_template(source: Path, destination: Path, overwrite: bool, replacements: dict[str, str]) -> None:
    if destination.exists() and not overwrite:
        print(f"[skip] {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = source.read_text(encoding="utf-8")
    for key, value in replacements.items():
        content = content.replace(key, value)
    destination.write_text(content, encoding="utf-8")
    print(f"[write] {destination}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy reusable screenshot generator support files into a Next.js project.")
    parser.add_argument("--project-root", default=".", help="Target project root. Default: current directory")
    parser.add_argument("--font-import", default="Inter", help="Google font import name used in layout.tsx")
    parser.add_argument("--font-const", default="font", help="Local font constant name used in layout.tsx")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--with-layout", action="store_true", help="Also write src/app/layout.tsx from the template")
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parents[1]
    templates_root = skill_root / "assets" / "templates"
    project_root = Path(args.project_root).resolve()

    copy_file(skill_root / "mockup.png", project_root / "public" / "mockup.png", args.overwrite)
    (project_root / "public" / "frames").mkdir(parents=True, exist_ok=True)
    (project_root / "public" / "screenshots").mkdir(parents=True, exist_ok=True)

    template_map = {
        templates_root / "frame-presets.ts": project_root / "src" / "lib" / "app-store-screenshots" / "frame-presets.ts",
        templates_root / "frame-specs.ts": project_root / "src" / "lib" / "app-store-screenshots" / "frame-specs.ts",
        templates_root / "phone-frame.tsx": project_root / "src" / "lib" / "app-store-screenshots" / "phone-frame.tsx",
        templates_root / "export-png.ts": project_root / "src" / "lib" / "app-store-screenshots" / "export-png.ts",
    }

    for source, destination in template_map.items():
        copy_file(source, destination, args.overwrite)

    if args.with_layout:
        write_template(
            templates_root / "layout.tsx.template",
            project_root / "src" / "app" / "layout.tsx",
            args.overwrite,
            {
                "__FONT_IMPORT__": args.font_import,
                "__FONT_CONST__": args.font_const,
            },
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
