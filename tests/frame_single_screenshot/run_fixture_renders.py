#!/usr/bin/env python3
"""
Render the checked-in iPhone home screen fixtures through the single-frame skill.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_SCRIPT = ROOT / "skills" / "frame-single-screenshot" / "scripts" / "frame_single_screenshot.py"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "iphone-home-screens"
ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"

FIXTURES = [
    {
        "name": "iphone-se-3-home",
        "device": "iPhone SE",
        "frame_file": "Apple iPhone SE Red.png",
        "input": FIXTURE_DIR / "iphone-se-3-home.png",
        "output": ARTIFACT_DIR / "iphone-se-3-home-framed.png",
    },
    {
        "name": "iphone-14-pro-home",
        "device": "iPhone 14 Pro",
        "frame_file": "Apple iPhone 14 Pro Gold.png",
        "input": FIXTURE_DIR / "iphone-14-pro-home.png",
        "output": ARTIFACT_DIR / "iphone-14-pro-home-framed.png",
    },
    {
        "name": "iphone-14-pro-max-home",
        "device": "iPhone 14 Pro Max",
        "frame_file": "Apple iPhone 14 Pro Max Gold.png",
        "input": FIXTURE_DIR / "iphone-14-pro-max-home.png",
        "output": ARTIFACT_DIR / "iphone-14-pro-max-home-framed.png",
    },
    {
        "name": "iphone-15-pro-max-home",
        "device": "iPhone 15 Pro Max (using nearest cached Pro Max frame)",
        "frame_file": "Apple iPhone 14 Pro Max Gold.png",
        "input": FIXTURE_DIR / "iphone-15-pro-max-home.png",
        "output": ARTIFACT_DIR / "iphone-15-pro-max-home-framed.png",
    },
    {
        "name": "iphone-16-pro-max-home",
        "device": "iPhone 16 Pro Max (using nearest cached Pro Max frame)",
        "frame_file": "Apple iPhone 14 Pro Max Gold.png",
        "input": FIXTURE_DIR / "iphone-16-pro-max-home.png",
        "output": ARTIFACT_DIR / "iphone-16-pro-max-home-framed.png",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render the iPhone home screen fixtures through the framing skill.")
    parser.add_argument("--frame-dir", default=str(Path.home() / ".fastlane" / "frameit" / "latest"), help="Directory containing Fastlane frame PNGs")
    parser.add_argument("--output-dir", default=str(ARTIFACT_DIR), help="Directory for rendered fixture outputs")
    parser.add_argument("--clean", action="store_true", help="Remove existing output files before rendering")
    return parser.parse_args()


def ensure_inputs_exist() -> None:
    missing = [str(item["input"]) for item in FIXTURES if not Path(item["input"]).is_file()]
    if missing:
        raise SystemExit("Missing fixture inputs:\n" + "\n".join(missing))
    if not SKILL_SCRIPT.is_file():
        raise SystemExit(f"Skill script not found: {SKILL_SCRIPT}")


def render_fixture(item: dict, frame_dir: Path, output_dir: Path) -> dict:
    output_path = output_dir / item["output"].name
    command = [
        sys.executable,
        str(SKILL_SCRIPT),
        "--image",
        str(item["input"]),
        "--frame-file",
        str(item["frame_file"]),
        "--frame-dir",
        str(frame_dir),
        "--output",
        str(output_path),
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    return {
        "name": item["name"],
        "device": item["device"],
        "frame_file": item["frame_file"],
        "input": str(item["input"].relative_to(ROOT)),
        "output": str(output_path.relative_to(ROOT)),
        "stdout": completed.stdout.strip().splitlines(),
    }


def main() -> int:
    args = parse_args()
    ensure_inputs_exist()

    frame_dir = Path(args.frame_dir).expanduser()
    output_dir = Path(args.output_dir).expanduser()
    if args.clean and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = [render_fixture(item, frame_dir, output_dir) for item in FIXTURES]
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    print(f"[done] wrote {len(results)} framed fixtures to {output_dir}")
    for result in results:
        print(f'[fixture] {result["name"]} -> {result["output"]}')
    print(f"[manifest] {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
