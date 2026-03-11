# App Store Screenshots Generator

A skill for AI-powered coding agents (Claude Code, Cursor, Windsurf, etc.) that generates production-ready App Store screenshots and broader marketing mockups. It scaffolds a Next.js project, designs advertisement-style screenshots, and exports them at required Apple resolutions with automatic device frame matching and locale-aware content scaffolding.

![Example output — Bloom coffee tracking app](example.png)

## What it does

- Asks you about your app's brand, features, and style preferences
- Scaffolds a minimal Next.js project (or works within an existing one)
- Includes a scaffold helper for the base Next.js + `html-to-image` setup
- Adds `i18next`-based localization helpers and starter locale files for the generated app
- Designs each screenshot as an **advertisement** — not a UI showcase
- Writes compelling copy using proven App Store copywriting patterns
- Renders screenshots at full resolution with fastlane `frameit` device frames when available
- Automatically matches the closest device frame to each Apple screenshot size bucket
- Supports iPad screenshot exports, including landscape orientation
- Supports broader marketing mockups using cached/downloaded Android phone, Android tablet, and Mac laptop frames
- Includes bootstrap templates for frame selection, frame specs, phone rendering, and PNG export
- Includes bootstrap templates for locale metadata, localized slide content, RTL-aware layout helpers, and `locallama` config
- Exports PNGs for iPhone and iPad size buckets, including landscape sets

## Included assets

- `mockup.png` — Pre-measured fallback iPhone frame with transparent screen area

## Frame strategy

The skill now prefers fastlane `frameit` frames over the bundled single mockup:

- Put fastlane frame PNGs in `public/frames/`
- Reuse cached frames from `~/.fastlane/frameit` before downloading anything
- Run the bundled helper to fetch only the best matching frames for the requested Apple, Android, or Mac frame families
- Download them from `fastlane/frameit-frames` or `fastlane frameit download_frames`
- The generator picks the closest frame for each export size automatically
- If a matching frame or screen inset definition is missing, it falls back to `mockup.png`

This gives you more device choices without forcing every screenshot size to reuse one bezel.

### Getting the frames

The documented workflow now includes a bundled script:

```bash
python skills/app-store-screenshots/scripts/download_fastlane_frames.py --out-dir public/frames --size-preset marketing-all
```

It first checks the local Fastlane cache at `~/.fastlane/frameit`, then falls back to `fastlane/frameit-frames` on GitHub, picks the nearest device for each requested Apple/Android/Mac bucket, and writes a manifest.

Common presets:

- `apple-mobile-all`
- `android-all`
- `desktop-all`
- `marketing-all`

### Quick frame reference

The repo now also includes a helper to generate a markdown/json dimensions reference from cached or selected frames:

```bash
python skills/app-store-screenshots/scripts/generate_frame_dimension_reference.py --frame-dir ~/.fastlane/frameit/latest --markdown-out frame-dimensions.md --json-out frame-dimensions.json
```

This is useful when trimming the cache down to the frames you actually want to keep or when checking which device/orientation variants exist.

The repo now also includes a pregenerated snapshot from the current local cache:

- [frame-dimensions-latest.md](skills/app-store-screenshots/references/frame-dimensions-latest.md)
- [frame-dimensions-latest.json](skills/app-store-screenshots/references/frame-dimensions-latest.json)

Refresh them with:

```bash
python skills/app-store-screenshots/scripts/generate_frame_dimension_reference.py --frame-dir ~/.fastlane/frameit/latest --markdown-out skills/app-store-screenshots/references/frame-dimensions-latest.md --json-out skills/app-store-screenshots/references/frame-dimensions-latest.json
```

The repo also includes an automatic inset measurer for bezel PNGs:

```bash
python skills/app-store-screenshots/scripts/measure_frame_insets.py --frame-dir ~/.fastlane/frameit/latest --source-label fastlane-frameit-latest --json-out frame-insets.json --markdown-out frame-insets.md --ts-out measured-frame-specs.ts
```

It reads the transparent screen opening from each readable frame image, emits a refreshable JSON/Markdown reference, and generates a TypeScript scaffold you can copy into `FRAME_SPECS`.

Pregenerated cache snapshots are checked in at:

- [frame-insets-latest.md](skills/app-store-screenshots/references/frame-insets-latest.md)
- [frame-insets-latest.json](skills/app-store-screenshots/references/frame-insets-latest.json)
- [frame-insets-latest.ts](skills/app-store-screenshots/references/frame-insets-latest.ts)

Refresh them with:

```bash
python skills/app-store-screenshots/scripts/measure_frame_insets.py --frame-dir ~/.fastlane/frameit/latest --source-label fastlane-frameit-latest --json-out skills/app-store-screenshots/references/frame-insets-latest.json --markdown-out skills/app-store-screenshots/references/frame-insets-latest.md --ts-out skills/app-store-screenshots/references/frame-insets-latest.ts
```

The docs also keep three lower-level fallback paths:

- sparse-clone [fastlane/frameit-frames](https://github.com/fastlane/frameit-frames)
- download the repo archive and copy the frame images into `public/frames/`
- use `fastlane frameit download_frames` if Fastlane is already installed

### Bootstrapping the project

The skill now bundles helper scripts instead of keeping the reusable setup code inline in `SKILL.md`:

```bash
python skills/app-store-screenshots/scripts/scaffold_next_app.py --project-root . --execute
python skills/app-store-screenshots/scripts/bootstrap_support_files.py --project-root . --with-layout --locales en,ar,fr --default-locale en
```

Those scripts handle package-manager-aware scaffolding, install `html-to-image` + `i18next`, copy `mockup.png`, create the expected `public/` folders, write starter locale files under `src/locales/`, and install reusable TypeScript helpers from the bundled templates, including a locale-state hook for multi-locale preview/export in one app build. RTL locales are inferred from the selected locale set by default, and the locale label map now covers the full current App Store metadata language set, so generated selectors show proper labels instead of raw codes for supported App Store locales.

## Install

### Using npx skills (recommended)

```bash
npx skills add megastep/app-store-screenshots
```

This works with Claude Code, Cursor, Windsurf, OpenCode, Codex, and [40+ other agents](https://github.com/vercel-labs/skills#available-agents).

Install globally (available across all projects):

```bash
npx skills add megastep/app-store-screenshots -g
```

Install for a specific agent:

```bash
npx skills add megastep/app-store-screenshots -a claude-code
```

### Manual (git clone)

```bash
git clone https://github.com/megastep/app-store-screenshots ~/.claude/skills/app-store-screenshots
```

## Usage

Once installed, the skill triggers automatically when you ask Claude Code to:

- Build App Store screenshots
- Generate marketing screenshots for a mobile or desktop app
- Create exportable screenshot assets

Or just tell Claude Code what you need:

```
> Build App Store screenshots for my app
```

Claude will ask you about your app's screenshots, brand colors, font, features, style direction, and number of slides before building anything.
It should also ask about locales, default/source language, RTL needs, and whether screenshots/assets vary by locale.

## What gets scaffolded

If starting from an empty folder, the skill creates:

```
project/
├── public/
│   ├── mockup.png          # Fallback frame (copied from skill)
│   ├── frames/             # Fastlane frameit device PNGs
│   ├── app-icon.png        # Your app icon
│   └── screenshots/        # Shared + per-locale screenshots
├── src/app/
│   ├── layout.tsx          # Font setup
│   └── page.tsx            # Screenshot generator (single file)
├── src/lib/app-store-screenshots/
│   ├── localization.ts
│   ├── screenshot-content.ts
│   ├── use-localized-screenshot-app.tsx
│   └── export-png.ts
├── src/locales/
│   ├── en/
│   │   ├── ui.json
│   │   └── slides.json
│   └── ar/
│       ├── ui.json
│       └── slides.json
├── locallama.config.json
├── package.json
└── ...
```

The screenshot composition still lives in a **single `page.tsx` file**, but the reusable runtime now lives under `src/lib/app-store-screenshots/` so locale switching, deck loading, direction syncing, and export metadata do not have to be reimplemented in the page itself.

## Export sizes

| Display | Resolution |
|---------|-----------|
| iPhone 6.9" portrait | 1320 x 2868 |
| iPhone 6.5" portrait | 1284 x 2778 |
| iPhone 6.3" portrait | 1206 x 2622 |
| iPhone 6.1" portrait | 1125 x 2436 |
| iPad 13" portrait | 2064 x 2752 |
| iPad 13" landscape | 2752 x 2064 |
| iPad 11" portrait | 1488 x 2266 |
| iPad 11" landscape | 2266 x 1488 |
| Android phone compact | 1204 x 2456 |
| Android phone large | 1564 x 3320 |
| Android tablet landscape | 3313 x 2304 |
| MacBook Air landscape | 3306 x 1897 |
| MacBook Pro 16 landscape | 3910 x 2241 |

Design within the largest target for each Apple family/orientation set, then scale down within that group where needed. For Android and Mac presets, use the frame-native canvas unless your campaign has a separate export spec.

## Tech stack

| Dependency | Purpose |
|-----------|---------|
| Next.js | Dev server + static image serving |
| TypeScript | Type safety |
| Tailwind CSS | Styling |
| html-to-image | PNG export at exact resolutions |
| i18next | Multi-locale content loading |
| React | Component composition |

## Key design principles

- **Screenshots are ads, not docs** — each slide sells one idea
- **Copy follows the "one second" rule** — readable at thumbnail size in the App Store
- **Layouts vary** — no two adjacent slides share the same phone placement
- **Style is user-driven** — no hardcoded colors, gradients, or fonts
- **Frame choice is size-aware** — use the nearest fastlane device frame for each output size

## Requirements

- Node.js 20+
- One of: bun, pnpm, yarn, or npm (detected automatically, bun preferred)
- Python 3.11+ for the bundled helper scripts
- Pillow for `measure_frame_insets.py` if you want practical cache-wide inset measurement

## License

MIT
