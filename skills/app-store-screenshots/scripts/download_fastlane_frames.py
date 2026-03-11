#!/usr/bin/env python3
"""
Download the closest matching Fastlane frameit device frames for marketing sizes.

Supports Apple mobile, Android mobile/tablet, and Mac laptop frame families,
and prefers the local Fastlane cache at ~/.fastlane/frameit when available.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


API_TREE_URL = "https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"
RAW_URL = "https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
DEFAULT_OWNER = "fastlane"
DEFAULT_REPO = "frameit-frames"
DEFAULT_REFS = ("gh-pages", "master", "main")
DEFAULT_CACHE_DIR = str(Path.home() / ".fastlane" / "frameit")
SIZE_PRESETS = {
    "iphone-portrait": ("iphone-6.9-portrait", "iphone-6.5-portrait", "iphone-6.3-portrait", "iphone-6.1-portrait"),
    "iphone-all": ("iphone-6.9-portrait", "iphone-6.9-landscape", "iphone-6.5-portrait", "iphone-6.5-landscape", "iphone-6.3-portrait", "iphone-6.3-landscape", "iphone-6.1-portrait", "iphone-6.1-landscape"),
    "ipad-all": ("ipad-13-portrait", "ipad-13-landscape", "ipad-11-portrait", "ipad-11-landscape"),
    "apple-mobile-all": ("iphone-6.9-portrait", "iphone-6.9-landscape", "iphone-6.5-portrait", "iphone-6.5-landscape", "iphone-6.3-portrait", "iphone-6.3-landscape", "iphone-6.1-portrait", "iphone-6.1-landscape", "ipad-13-portrait", "ipad-13-landscape", "ipad-11-portrait", "ipad-11-landscape"),
    "android-phones": ("android-phone-compact-portrait", "android-phone-large-portrait"),
    "android-all": ("android-phone-compact-portrait", "android-phone-large-portrait", "android-tablet-landscape"),
    "desktop-all": ("macbook-air-landscape", "macbook-pro-16-landscape"),
    "marketing-all": ("iphone-6.9-portrait", "iphone-6.9-landscape", "iphone-6.5-portrait", "iphone-6.5-landscape", "iphone-6.3-portrait", "iphone-6.3-landscape", "iphone-6.1-portrait", "iphone-6.1-landscape", "ipad-13-portrait", "ipad-13-landscape", "ipad-11-portrait", "ipad-11-landscape", "android-phone-compact-portrait", "android-phone-large-portrait", "android-tablet-landscape", "macbook-air-landscape", "macbook-pro-16-landscape"),
}
DEFAULT_SIZE_PRESET = "apple-mobile-all"
DEFAULT_COLOR_PRIORITY = (
    "black",
    "space black",
    "midnight",
    "space gray",
    "natural titanium",
    "white",
    "silver",
    "starlight",
    "gold",
    "rose gold",
)


@dataclass(frozen=True)
class Bucket:
    key: str
    family: str
    orientation: str
    size_label: str
    output_name: str
    resolution: tuple[int, int]
    device_candidates: tuple[str, ...]


BUCKETS = {
    "iphone-6.9-portrait": Bucket("iphone-6.9-portrait", "iphone", "portrait", '6.9"', "iphone-16-pro-max.png", (1320, 2868), ("iphone 16 pro max", "iphone 15 pro max", "iphone 14 pro max")),
    "iphone-6.9-landscape": Bucket("iphone-6.9-landscape", "iphone", "landscape", '6.9"', "iphone-16-pro-max-landscape.png", (2868, 1320), ("iphone 16 pro max landscape", "iphone 15 pro max landscape", "iphone 14 pro max landscape", "iphone 16 pro max")),
    "iphone-6.5-portrait": Bucket("iphone-6.5-portrait", "iphone", "portrait", '6.5"', "iphone-15-plus.png", (1284, 2778), ("iphone 15 plus", "iphone 14 plus", "iphone 11 pro max", "iphone xs max", "iphone 8 plus")),
    "iphone-6.5-landscape": Bucket("iphone-6.5-landscape", "iphone", "landscape", '6.5"', "iphone-15-plus-landscape.png", (2778, 1284), ("iphone 15 plus landscape", "iphone 14 plus landscape", "iphone 11 pro max landscape", "iphone xs max landscape", "iphone 15 plus")),
    "iphone-6.3-portrait": Bucket("iphone-6.3-portrait", "iphone", "portrait", '6.3"', "iphone-16-pro.png", (1206, 2622), ("iphone 16 pro", "iphone 15 pro")),
    "iphone-6.3-landscape": Bucket("iphone-6.3-landscape", "iphone", "landscape", '6.3"', "iphone-16-pro-landscape.png", (2622, 1206), ("iphone 16 pro landscape", "iphone 15 pro landscape", "iphone 16 pro")),
    "iphone-6.1-portrait": Bucket("iphone-6.1-portrait", "iphone", "portrait", '6.1"', "iphone-16.png", (1125, 2436), ("iphone 16", "iphone 15", "iphone 14 pro", "iphone 14", "iphone 13 pro", "iphone 13", "iphone 12 pro", "iphone 12", "iphone 11 pro", "iphone xr")),
    "iphone-6.1-landscape": Bucket("iphone-6.1-landscape", "iphone", "landscape", '6.1"', "iphone-16-landscape.png", (2436, 1125), ("iphone 16 landscape", "iphone 15 landscape", "iphone 14 pro landscape", "iphone 16")),
    "ipad-13-portrait": Bucket("ipad-13-portrait", "ipad", "portrait", '13"', "ipad-pro-13.png", (2064, 2752), ("ipad pro 13", "ipad air 13", "ipad pro 12 9", "ipad pro 12.9")),
    "ipad-13-landscape": Bucket("ipad-13-landscape", "ipad", "landscape", '13"', "ipad-pro-13-landscape.png", (2752, 2064), ("ipad pro 13 landscape", "ipad air 13 landscape", "ipad pro 12 9 landscape", "ipad pro 13")),
    "ipad-11-portrait": Bucket("ipad-11-portrait", "ipad", "portrait", '11"', "ipad-pro-11.png", (1488, 2266), ("ipad pro 11", "ipad air 11", "ipad air 10.9", "ipad pro 10.5")),
    "ipad-11-landscape": Bucket("ipad-11-landscape", "ipad", "landscape", '11"', "ipad-pro-11-landscape.png", (2266, 1488), ("ipad pro 11 landscape", "ipad air 11 landscape", "ipad air 10.9 landscape", "ipad pro 11")),
    "android-phone-compact-portrait": Bucket("android-phone-compact-portrait", "android-phone", "portrait", "Android Compact", "google-pixel-5.png", (1204, 2456), ("google pixel 5", "pixel 5", "google pixel 4", "pixel 4", "google pixel quite black")),
    "android-phone-large-portrait": Bucket("android-phone-large-portrait", "android-phone", "portrait", "Android Large", "google-pixel-4-xl.png", (1564, 3320), ("google pixel 4 xl", "pixel 4 xl", "samsung galaxy s21 ultra 5g", "galaxy s21 ultra", "google pixel 3 xl")),
    "android-tablet-landscape": Bucket("android-tablet-landscape", "android-tablet", "landscape", "Android Tablet", "google-pixel-slate.png", (3313, 2304), ("google pixel slate", "pixel slate")),
    "macbook-air-landscape": Bucket("macbook-air-landscape", "mac", "landscape", "MacBook Air", "apple-macbook-air.png", (3306, 1897), ("apple macbook air", "macbook air")),
    "macbook-pro-16-landscape": Bucket("macbook-pro-16-landscape", "mac", "landscape", "MacBook Pro 16", "apple-macbook-pro-16.png", (3910, 2241), ("apple macbook pro 16", "macbook pro 16", "macbook pro")),
}


def normalize(value: str) -> str:
    lowered = value.lower().replace("_", " ").replace("-", " ")
    lowered = lowered.replace("+", " plus ")
    lowered = re.sub(r"[^a-z0-9.]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def parse_csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "app-store-screenshots-fastlane-frame-downloader"},
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def fetch_repo_tree(owner: str, repo: str, refs: Iterable[str]) -> tuple[str, list[dict]]:
    errors: list[str] = []
    for ref in refs:
        url = API_TREE_URL.format(owner=owner, repo=repo, ref=urllib.parse.quote(ref, safe=""))
        try:
            payload = fetch_json(url)
            tree = payload.get("tree")
            if isinstance(tree, list):
                return ref, tree
            errors.append(f"{ref}: malformed response")
        except urllib.error.HTTPError as exc:
            errors.append(f"{ref}: HTTP {exc.code}")
        except urllib.error.URLError as exc:
            errors.append(f"{ref}: {exc.reason}")
    raise RuntimeError(f"Could not fetch frame tree from {owner}/{repo}. Tried {', '.join(errors)}")


def infer_asset_family(path: str) -> str:
    lowered = path.lower()
    if "macbook" in lowered:
        return "mac"
    if "pixel slate" in lowered:
        return "android-tablet"
    if any(term in lowered for term in ("pixel", "galaxy", "nexus", "htc", "huawei", "moto")):
        return "android-phone"
    if "ipad" in lowered:
        return "ipad"
    if "iphone" in lowered:
        return "iphone"
    return "other"


def is_candidate_asset(path: str) -> bool:
    lowered = path.lower()
    if not lowered.endswith((".png", ".jpg", ".jpeg")):
        return False
    if any(term in lowered for term in ("watch", "tv")):
        return False
    return infer_asset_family(path) != "other"


def collect_local_cache_assets(cache_dir: Path) -> list[str]:
    if not cache_dir.exists():
        return []
    return [str(path) for path in cache_dir.rglob("*") if path.is_file() and is_candidate_asset(str(path))]


def score_path(path: str, bucket: Bucket, color_priority: tuple[str, ...]) -> tuple[int, int, int, int, int, int, str]:
    normalized_path = normalize(path)

    family_rank = 0 if infer_asset_family(path) == bucket.family else 1
    if family_rank == 1:
        return (sys.maxsize, sys.maxsize, sys.maxsize, sys.maxsize, sys.maxsize, sys.maxsize, path)

    device_rank = None
    for index, device_name in enumerate(bucket.device_candidates):
        if device_name in normalized_path:
            device_rank = index
            break
    if device_rank is None:
        return (sys.maxsize, sys.maxsize, sys.maxsize, sys.maxsize, sys.maxsize, sys.maxsize, path)

    color_rank = len(color_priority) + 1
    for index, color_name in enumerate(color_priority):
        if color_name in normalized_path:
            color_rank = index
            break

    orientation_rank = 0 if bucket.orientation in normalized_path else 1
    latest_rank = 0 if "/latest/" in f"/{path.lower()}" else 1
    extension_rank = 0 if path.lower().endswith(".png") else 1
    depth_rank = path.count("/")
    return (family_rank, device_rank, color_rank, orientation_rank, latest_rank, extension_rank, depth_rank, path)


def select_best_asset(paths: Iterable[str], bucket: Bucket, color_priority: tuple[str, ...]) -> str | None:
    scored = [score_path(path, bucket, color_priority) for path in paths]
    valid = [entry for entry in scored if entry[0] != sys.maxsize]
    if not valid:
        return None
    return min(valid)[-1]


def download_file(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "app-store-screenshots-fastlane-frame-downloader"})
    with urllib.request.urlopen(request) as response:
        data = response.read()
    destination.write_bytes(data)


def copy_local_file(source: Path, destination: Path) -> None:
    destination.write_bytes(source.read_bytes())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download the closest matching Fastlane frameit frames for Apple, Android, and Mac marketing sizes.")
    parser.add_argument("--out-dir", default="public/frames", help="Directory to write the downloaded frame images into. Default: public/frames")
    parser.add_argument("--size-preset", choices=tuple(SIZE_PRESETS.keys()), default=DEFAULT_SIZE_PRESET, help=f"Named size bundle to fetch. Default: {DEFAULT_SIZE_PRESET}")
    parser.add_argument("--sizes", help="Comma-separated explicit size bucket keys. Overrides --size-preset. Example: android-phone-large-portrait,macbook-air-landscape")
    parser.add_argument("--color-priority", default=",".join(DEFAULT_COLOR_PRIORITY), help="Comma-separated list of color keywords to prefer when multiple frame variants exist.")
    parser.add_argument("--owner", default=DEFAULT_OWNER, help="GitHub owner. Default: fastlane")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repo. Default: frameit-frames")
    parser.add_argument("--refs", default=",".join(DEFAULT_REFS), help="Comma-separated Git refs to try in order. Default: gh-pages,master,main")
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="Local Fastlane frame cache root to prefer before network download. Default: ~/.fastlane/frameit")
    parser.add_argument("--skip-cache", action="store_true", help="Ignore the local Fastlane cache and resolve frames from GitHub only.")
    parser.add_argument("--manifest-name", default="fastlane-frame-manifest.json", help="Manifest file name written inside out-dir. Default: fastlane-frame-manifest.json")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite already-downloaded output files instead of keeping existing files.")
    parser.add_argument("--dry-run", action="store_true", help="Resolve and print matches without downloading files.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    requested_sizes = parse_csv(args.sizes) if args.sizes else SIZE_PRESETS[args.size_preset]
    unknown_sizes = [size for size in requested_sizes if size not in BUCKETS]
    if unknown_sizes:
        parser.error(f"Unsupported size buckets: {', '.join(unknown_sizes)}")

    color_priority = parse_csv(args.color_priority)
    refs = parse_csv(args.refs)
    out_dir = Path(args.out_dir).expanduser()
    cache_dir = Path(args.cache_dir).expanduser()

    local_candidate_paths: list[str] = []
    if not args.skip_cache:
        local_candidate_paths = collect_local_cache_assets(cache_dir)

    ref = None
    remote_candidate_paths: list[str] = []
    if not local_candidate_paths:
        ref, tree = fetch_repo_tree(args.owner, args.repo, refs)
        remote_candidate_paths = [entry["path"] for entry in tree if entry.get("type") == "blob" and is_candidate_asset(entry["path"])]

    if not local_candidate_paths and not remote_candidate_paths:
        raise RuntimeError(f"No candidate image assets found in local cache {cache_dir} or {args.owner}/{args.repo}")

    manifest: dict[str, object] = {
        "source": f"{args.owner}/{args.repo}",
        "ref": ref,
        "out_dir": str(out_dir),
        "cache_dir": str(cache_dir),
        "used_cache": bool(local_candidate_paths),
        "size_preset": args.size_preset if not args.sizes else None,
        "matches": [],
    }

    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    resolved_any = False
    for size_key in requested_sizes:
        bucket = BUCKETS[size_key]
        asset_path = select_best_asset(local_candidate_paths or remote_candidate_paths, bucket, color_priority)
        match = {
            "key": bucket.key,
            "family": bucket.family,
            "orientation": bucket.orientation,
            "size": bucket.size_label,
            "resolution": {"width": bucket.resolution[0], "height": bucket.resolution[1]},
            "output_name": bucket.output_name,
            "device_candidates": list(bucket.device_candidates),
            "asset_path": asset_path,
        }

        if asset_path is None:
            manifest["matches"].append(match)
            print(f"[warn] No frame match found for {bucket.key}")
            continue

        resolved_any = True
        destination = out_dir / bucket.output_name
        match["destination"] = str(destination)
        if local_candidate_paths:
            match["source_type"] = "cache"
            match["source_path"] = asset_path
        else:
            asset_url = RAW_URL.format(owner=args.owner, repo=args.repo, ref=ref, path=urllib.parse.quote(asset_path, safe="/"))
            match["source_type"] = "github"
            match["asset_url"] = asset_url
        manifest["matches"].append(match)

        print(f"[match] {bucket.key} -> {asset_path} -> {destination}")

        if args.dry_run:
            continue
        if destination.exists() and not args.overwrite:
            print(f"[skip] {destination} already exists")
            continue
        if local_candidate_paths:
            copy_local_file(Path(asset_path), destination)
            print(f"[done] Copied {destination}")
        else:
            download_file(asset_url, destination)
            print(f"[done] Downloaded {destination}")

    if not resolved_any:
        print("[error] Could not resolve any matching frame assets", file=sys.stderr)
        return 1

    if not args.dry_run:
        manifest_path = out_dir / args.manifest_name
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"[done] Wrote manifest {manifest_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
