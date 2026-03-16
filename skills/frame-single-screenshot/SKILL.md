---
name: frame-single-screenshot
description: Use when generating one framed device screenshot/mockup from an existing unframed PNG or JPG and a target device such as iPhone, iPad, Android phone, Android tablet, or Mac. Triggers on frame this screenshot, put this in a device frame, Fastlane frameit mockup, bezel mockup, single screenshot mockup.
---

# Frame a Single Screenshot

## Overview

Generate one framed device image from a flat screenshot and a target device. Prefer the bundled script over ad hoc image editing.

This skill is intentionally narrower than `app-store-screenshots`:

- one input image
- one target device
- one output image
- Fastlane `frameit` PNGs as the frame source
- optional output resize and format conversion

## Ask For

1. The unframed screenshot path
2. The target device, for example `iPhone 16 Pro Max`, `iPad Pro 13`, `Pixel 8 Pro`, or `MacBook Air`
3. The output path
4. Optional: orientation, preferred finish/color, exact frame filename, output size/format, landscape rotation direction, and screen bleed if the bezel shows a hairline seam

## Runtime Requirements

- Python 3.11+
- Pillow: `python -m pip install pillow`
- Fastlane frame PNGs available locally, usually in `~/.fastlane/frameit/latest`

## Default Workflow

Run the bundled script:

```bash
python /path/to/frame-single-screenshot/scripts/frame_single_screenshot.py --image /path/to/screenshot.png --device "iPhone 16 Pro Max" --output /path/to/framed.png
```

Useful variants:

```bash
# Prefer a specific orientation
python /path/to/frame-single-screenshot/scripts/frame_single_screenshot.py --image ./capture.png --device "iPad Pro 13" --orientation landscape --output ./framed-ipad.png

# Rotate a portrait bezel counterclockwise for a landscape screenshot
python /path/to/frame-single-screenshot/scripts/frame_single_screenshot.py --image ./capture-landscape.png --frame-file "Apple iPad Pro (11-inch) Silver.png" --landscape-rotation counterclockwise --output ./framed-ipad-landscape.png

# Prefer a specific finish/color
python /path/to/frame-single-screenshot/scripts/frame_single_screenshot.py --image ./capture.png --device "Pixel 8 Pro" --color-priority "black,obsidian,bay" --output ./framed-pixel.png

# Use an exact Fastlane filename if the user already picked one
python /path/to/frame-single-screenshot/scripts/frame_single_screenshot.py --image ./capture.png --frame-file "Apple iPhone 15 Pro Natural Titanium.png" --output ./framed-iphone.png

# Resize to a specific width while preserving aspect ratio
python /path/to/frame-single-screenshot/scripts/frame_single_screenshot.py --image ./capture.png --device "MacBook Air" --width 1600 --output ./framed-mac.png

# Export JPEG or WEBP instead of PNG
python /path/to/frame-single-screenshot/scripts/frame_single_screenshot.py --image ./capture.png --device "iPhone 16 Pro Max" --format webp --quality 90 --output ./framed.webp

# Increase the screenshot overscan under the bezel if you still see a 1-2px gap
python /path/to/frame-single-screenshot/scripts/frame_single_screenshot.py --image ./capture.png --device "Galaxy S24 Ultra" --screen-bleed 3 --output ./framed-galaxy.png

# Force an exact output size
python /path/to/frame-single-screenshot/scripts/frame_single_screenshot.py --image ./capture.png --device "iPad Pro 13" --width 2064 --height 2752 --output ./ipad-store-shot.jpg

# Show the best matching cached frames without rendering
python /path/to/frame-single-screenshot/scripts/frame_single_screenshot.py --image ./capture.png --device "Galaxy S24 Ultra" --list-matches
```

## Frame Resolution Rules

Use this order:

1. Exact `--frame-file` if the user provided one
2. Otherwise fuzzy-match the target device against the local Fastlane cache
3. Reuse the shared inset reference data if available
4. If the selected frame is missing from the shared inset reference, measure that one frame directly

Do not hand-edit bezel placements unless the generated result is obviously wrong.

## Landscape Behavior

- If the input screenshot is landscape but the selected Fastlane bezel asset is portrait, the script rotates the frame and its inset geometry automatically.
- The default rotation direction is `clockwise`.
- Override it with `--landscape-rotation counterclockwise` if the resulting composition is upside down or if you want the opposite home button / camera edge.
- This is especially useful for iPad fixtures because many local Fastlane caches only contain portrait iPad frames.

## Seam / Bleed Behavior

- The script slightly overfills the screen area under the bezel to avoid 1-2px seams from rounding at export time.
- Default overscan is `2px`.
- Override it with `--screen-bleed <pixels>` if a particular frame still shows a gap or if you want stricter edge matching.

## Test Fixtures

- Test-only screenshot fixtures live under `tests/frame_single_screenshot/fixtures/`, not inside the skill package itself.
- The bundled runner at `tests/frame_single_screenshot/run_fixture_renders.py` shells out to the real skill script and writes inspectable outputs to `tests/frame_single_screenshot/artifacts/`.
- That runner includes iPhone, iPad, Android phone, and Android tablet fixtures in both portrait and landscape where applicable.

## If Frames Are Missing

If `~/.fastlane/frameit/latest` does not contain usable frame PNGs, tell the user to fetch them first. If the full screenshot skill is present beside this one, prefer its downloader:

```bash
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/download_fastlane_frames.py --out-dir /tmp/frames --size-preset marketing-all
```

Otherwise use Fastlane directly:

```bash
fastlane frameit download_frames
```

Then rerun this skill with `--frame-dir`.

## Notes

- The script uses the lowercased Fastlane filename stem as the frame key, which avoids collisions like `S10` vs `S10+`.
- The output defaults to native frame size, but `--width` and `--height` can resize it after compositing.
- The output format defaults from the output extension, or `png` if none is obvious.
- JPEG output is flattened onto white because the format does not support alpha.
- The script defaults to `cover` fitting so the screen area is fully filled.
- Portrait frames can be reused for landscape inputs via rotation; `--landscape-rotation` controls the direction.
- `--screen-bleed` defaults to `2` so the screenshot slightly tucks under the frame instead of stopping exactly at the measured edge.
