---
name: app-store-screenshots
description: Use when building App Store screenshot pages, generating exportable marketing screenshots for Apple mobile, Android, or Mac apps, or creating programmatic screenshot generators with Next.js. Triggers on app store, screenshots, marketing assets, html-to-image, device mockup.
---

# App Store and Marketing Screenshots Generator

## Overview

Build a Next.js page that renders App Store screenshots and broader device-framed marketing screenshots as **advertisements** (not UI showcases) and exports them via `html-to-image` at the required platform resolutions. Screenshots are usually the single most important conversion asset on an app listing, and they also need to work as reusable campaign creative across Apple, Android, and Mac device classes.

## Core Principle

**Screenshots are advertisements, not documentation.** Every screenshot sells one idea. If you're showing UI, you're doing it wrong — you're selling a *feeling*, an *outcome*, or killing a *pain point*.

## Step 1: Ask the User These Questions

Before writing ANY code, ask the user all of these. Do not proceed until you have answers:

### Required

1. **App screenshots** — "Where are your app screenshots? (PNG files of actual device captures)"
2. **App icon** — "Where is your app icon PNG?"
3. **Brand colors** — "What are your brand colors? (accent color, text color, background preference)"
4. **Font** — "What font does your app use? (or what font do you want for the screenshots?)"
5. **Feature list** — "List your app's features in priority order. What's the #1 thing your app does?"
6. **Platforms and orientations** — "Which device families do you want to support: iPhone, iPad, Android phone, Android tablet, Mac, or a subset? For each, which orientations do you need?"
7. **Number of slides** — "How many screenshots do you want per device/orientation set? (Apple allows up to 10 per App Store set; marketing sets can vary.)"
8. **Style direction** — "What style do you want? Examples: warm/organic, dark/moody, clean/minimal, bold/colorful, gradient-heavy, flat. Share App Store or mobile/desktop marketing screenshot references if you have any."
9. **Locales** — "Which locales do you want to ship? What is the source/default locale? Do any of them need RTL layout?"
10. **Localized assets** — "Do screenshots, app icons, or overlays change by locale, or is the copy the only localized part?"

### Optional

1. **Component assets** — "Do you have any UI element PNGs (cards, widgets, etc.) you want as floating decorations? If not, that's fine — we'll skip them."
2. **Additional instructions** — "Any specific requirements, constraints, or preferences?"

### Derived from answers (do NOT ask — decide yourself)

Based on the user's style direction, brand colors, and app aesthetic, decide:

- **Background style**: gradient direction, colors, whether light or dark base
- **Decorative elements**: blobs, glows, geometric shapes, or none — match the style
- **Dark vs light slides**: how many of each, which features suit dark treatment
- **Typography treatment**: weight, tracking, line height — match the brand personality
- **Color palette**: derive text colors, secondary colors, shadow tints from the brand colors

**IMPORTANT:** If the user gives additional instructions at any point during the process, follow them. User instructions always override skill defaults.

## Step 2: Set Up the Project

### Runtime Requirements

The helper scripts in this skill assume a working Python 3 environment.

- Use Python 3.11+ if possible.
- `scaffold_next_app.py`, `bootstrap_support_files.py`, `download_fastlane_frames.py`, and `generate_frame_dimension_reference.py` use only the standard library.
- `measure_frame_insets.py` expects Pillow to be installed for practical cache-wide runs. Install it with `python -m pip install pillow` if it is missing.
- The inset measurer keeps a pure-Python PNG fallback, but that path is much slower and should be treated as a backup rather than the normal workflow.
- The generated app now expects `i18next`, which `scaffold_next_app.py` installs alongside `html-to-image`.

### Scaffold the Project

Use the bundled scaffold helper instead of retyping package-manager commands. It detects package managers with this priority: **bun > pnpm > yarn > npm**.

- Script: `scripts/scaffold_next_app.py`
- Dry run first to see the exact commands
- Pass `--execute` only when you are ready to scaffold/install

Example:

```bash
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/scaffold_next_app.py --project-root . --execute
```

That installs the runtime dependencies needed for screenshot export and localization (`html-to-image` and `i18next`).

### Device Frames

Prefer **fastlane `frameit` frames** over the bundled single mockup. They give you many more device choices and let you export screenshots that match the actual App Store size bucket more closely across iPhone and iPad, and they also unlock broader marketing mockups for Android phones, Android tablets, and Mac laptops.

Use this order:

1. **Best**: Reuse the local Fastlane cache in `~/.fastlane/frameit` if it exists
2. **Next best**: Download matching `frameit` device PNGs into `public/frames/`
3. **Fallback**: Use the bundled `mockup.png` if no usable frame assets are available

If the project does not already include device frames, create `public/frames/` and populate it from the fastlane frame assets source. Keep the existing `mockup.png` available as a fallback.

### Automatically Download Fastlane Frames

When the project is missing frame assets, fetch them from the Fastlane frames repo before building the generator.

**Use the bundled helper script first**. It resolves the closest device frame for each requested App Store size, prefers the local Fastlane cache, and only hits GitHub if the cache does not have a usable match.

If the script needs to query GitHub repeatedly or runs in CI, provide `GITHUB_TOKEN` (or `GH_TOKEN`) so the repo tree lookup avoids low unauthenticated rate limits.

The script lives next to this skill at `scripts/download_fastlane_frames.py`. Run it from the project root:

```bash
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/download_fastlane_frames.py --out-dir public/frames
```

Common variants:

```bash
# Only fetch the large modern iPhone portrait sizes
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/download_fastlane_frames.py --out-dir public/frames --size-preset iphone-portrait

# Fetch Apple mobile frames only
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/download_fastlane_frames.py --out-dir public/frames --size-preset apple-mobile-all

# Fetch Android phones + tablet
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/download_fastlane_frames.py --out-dir public/frames --size-preset android-all

# Fetch Mac laptop frames
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/download_fastlane_frames.py --out-dir public/frames --size-preset desktop-all

# Fetch everything useful for broader marketing mockups
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/download_fastlane_frames.py --out-dir public/frames --size-preset marketing-all

# Prefer lighter device finishes
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/download_fastlane_frames.py --out-dir public/frames --color-priority "white,silver,natural titanium,black"

# Ignore the local Fastlane cache and force GitHub resolution
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/download_fastlane_frames.py --out-dir public/frames --size-preset universal-all --skip-cache

# Resolve matches without downloading
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/download_fastlane_frames.py --out-dir public/frames --dry-run

# Use authenticated GitHub requests when rate limits matter
GITHUB_TOKEN=... python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/download_fastlane_frames.py --out-dir public/frames --size-preset marketing-all
```

The script writes:

- the selected frame PNGs into `public/frames/`
- a manifest file describing which Fastlane asset matched each App Store size

By default it looks for cached frame assets under `~/.fastlane/frameit`. That catches outputs from prior `fastlane frameit download_frames` runs and avoids redundant network fetches.

### Generate a Quick Frame-Dimensions Reference

Use the bundled dimensions helper to build a markdown/json reference from either the local Fastlane cache or your narrowed `public/frames/` folder.

Examples:

```bash
# From the local Fastlane cache
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/generate_frame_dimension_reference.py --frame-dir ~/.fastlane/frameit/latest --markdown-out frame-dimensions.md --json-out frame-dimensions.json

# From the selected project frames only
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/generate_frame_dimension_reference.py --frame-dir public/frames --markdown-out public/frames/frame-dimensions.md --json-out public/frames/frame-dimensions.json
```

Use this reference when:

- picking which cached frame variant to keep
- verifying portrait vs landscape assets
- sanity-checking which devices/orientations exist before measuring insets

The repo includes a pregenerated cache snapshot at `references/frame-dimensions-latest.md` plus structured data at `references/frame-dimensions-latest.json`.

Refresh them with:

```bash
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/generate_frame_dimension_reference.py --frame-dir ~/.fastlane/frameit/latest --markdown-out /path/to/app-store-screenshots/skills/app-store-screenshots/references/frame-dimensions-latest.md --json-out /path/to/app-store-screenshots/skills/app-store-screenshots/references/frame-dimensions-latest.json
```

### Measure Frame Insets Automatically

Use the bundled inset measurer to detect the interior screen opening for every readable bezel PNG in the cache or in `public/frames/`.

Examples:

```bash
# Measure the full local Fastlane cache and emit refreshable references
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/measure_frame_insets.py --frame-dir ~/.fastlane/frameit/latest --source-label fastlane-frameit-latest --json-out frame-insets.json --markdown-out frame-insets.md --ts-out measured-frame-specs.ts

# Measure only the narrowed project frames you actually kept
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/measure_frame_insets.py --frame-dir public/frames --source-label public-frames --json-out public/frames/frame-insets.json --markdown-out public/frames/frame-insets.md --ts-out public/frames/measured-frame-specs.ts
```

The script:

- reads the alpha channel from each PNG
- finds the largest interior transparent window
- emits pixel-space and percent-space inset values
- flags likely cutout/notch frames
- skips invalid cache files or implausible detections instead of aborting the whole run

The repo includes a pregenerated snapshot from the current Fastlane cache at:

- `references/frame-insets-latest.json`
- `references/frame-insets-latest.md`
- `references/frame-insets-latest.ts`

Refresh them with:

```bash
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/measure_frame_insets.py --frame-dir ~/.fastlane/frameit/latest --source-label fastlane-frameit-latest --json-out /path/to/app-store-screenshots/skills/app-store-screenshots/references/frame-insets-latest.json --markdown-out /path/to/app-store-screenshots/skills/app-store-screenshots/references/frame-insets-latest.md --ts-out /path/to/app-store-screenshots/skills/app-store-screenshots/references/frame-insets-latest.ts
```

Use the generated TypeScript file as a scaffold, then copy only the entries that match the frames you actually retain in `public/frames/`.

Only fall back to the manual approaches below if the script is blocked or the user needs unusual device coverage beyond the bundled Apple/Android/Mac presets.

Preferred source:

- Repo: `https://github.com/fastlane/frameit-frames`
- Hosted index: `https://fastlane.github.io/frameit-frames/`

Use one of these approaches:

#### Option A: Sparse clone just the assets

```bash
git clone --depth=1 --filter=blob:none --sparse https://github.com/fastlane/frameit-frames.git /tmp/frameit-frames
cd /tmp/frameit-frames
git sparse-checkout set .
mkdir -p /path/to/project/public/frames
find . -type f \( -iname '*.png' -o -iname '*.jpg' \) -exec cp {} /path/to/project/public/frames/ \;
```

Then clean the folder down to only the devices you need for the current export buckets.

#### Option B: Download the archive

```bash
curl -L https://github.com/fastlane/frameit-frames/archive/refs/heads/master.tar.gz -o /tmp/frameit-frames.tar.gz
mkdir -p /tmp/frameit-frames-extract
tar -xzf /tmp/frameit-frames.tar.gz -C /tmp/frameit-frames-extract
mkdir -p /path/to/project/public/frames
find /tmp/frameit-frames-extract -type f \( -iname '*.png' -o -iname '*.jpg' \) -exec cp {} /path/to/project/public/frames/ \;
```

#### Option C: Use `fastlane frameit download_frames`

If Fastlane is already installed for the user’s project, prefer the built-in downloader:

```bash
fastlane frameit download_frames
mkdir -p /path/to/project/public/frames
find ./fastlane/screenshots -type f \( -iname '*.png' -o -iname '*.jpg' \) -exec cp {} /path/to/project/public/frames/ \;
```

After download:

1. Rename the handful of files you keep into stable kebab-case names like `iphone-16-pro-max.png`, `google-pixel-5.png`, or `apple-macbook-air.png`.
2. Delete everything you are not going to match against.
3. Run `measure_frame_insets.py` against the retained files and copy the matching generated entries into `FRAME_SPECS`.
4. Keep `mockup.png` in `public/` as the last-resort fallback.

### File Structure

```
project/
├── public/
│   ├── mockup.png              # Fallback frame (included with skill)
│   ├── frames/                 # Fastlane frameit device PNGs
│   │   ├── iphone-16-pro-max.png
│   │   ├── ipad-pro-13.png
│   │   ├── google-pixel-5.png
│   │   ├── google-pixel-slate.png
│   │   ├── apple-macbook-air.png
│   │   └── ...
│   ├── app-icon.png            # User's app icon
│   └── screenshots/            # User's app screenshots
│       ├── home.png
│       ├── feature-1.png
│       └── ...
├── src/app/
│   ├── layout.tsx              # Font setup
│   └── page.tsx                # The screenshot generator (single file)
└── package.json
```

**The entire generator is a single `page.tsx` file.** No routing, no extra layouts, no API routes.

### Bootstrap Reusable Files

Use the support-file bootstrap script before you start writing the actual screenshot page.

- Script: `scripts/bootstrap_support_files.py`
- Copies `mockup.png`
- Creates `public/frames/` and `public/screenshots/`
- Creates locale-aware screenshot folders under `public/screenshots/`
- Writes starter locale files under `src/locales/`
- Copies reusable TypeScript helpers into `src/lib/app-store-screenshots/`
- Writes a project-local `locallama.config.json`
- Optionally writes `src/app/layout.tsx` from a template
- Uses a locale label map that covers the full current App Store metadata language set
- Infers RTL locales from the selected locale set unless you override `--rtl-locales`

Example:

```bash
python /path/to/app-store-screenshots/skills/app-store-screenshots/scripts/bootstrap_support_files.py --project-root . --with-layout --font-import Inter --font-const font --locales en,ar,fr --default-locale en
```

Bundled template files:

- `assets/templates/layout.tsx.template`
- `assets/templates/frame-presets.ts`
- `assets/templates/frame-specs.ts`
- `assets/templates/phone-frame.tsx`
- `assets/templates/export-png.ts`
- `assets/templates/localization.ts.template`
- `assets/templates/screenshot-content.ts.template`
- `assets/templates/use-localized-screenshot-app.tsx`
- `assets/templates/layout-direction.ts`
- `assets/templates/locallama.config.json.template`

The bootstrap step also creates:

- `src/locales/<locale>/ui.json`
- `src/locales/<locale>/slides.json`
- `docs/translation-style-guide.txt`
- `locallama.config.json`

Use the generated locale helpers in `page.tsx` instead of hardcoding English strings:

- `src/lib/app-store-screenshots/localization.ts`
  Contains locale metadata, `i18next` setup, `lang` / `dir` helpers, and export folder helpers
- `src/lib/app-store-screenshots/screenshot-content.ts`
  Contains the base slide schema and locale-aware deck builder
- `src/lib/app-store-screenshots/use-localized-screenshot-app.tsx`
  Contains the runtime locale loader/hook for single-build multi-locale preview and export flows
- `src/lib/app-store-screenshots/layout-direction.ts`
  Contains RTL/LTR-aware layout helpers for split and asymmetric compositions

## Step 3: Plan the Slides

### Screenshot Framework (Narrative Arc)

Adapt this framework to the user's requested slide count. Not all slots are required — pick what fits:

| Slot | Purpose | Notes |
|------|---------|-------|
| #1 | **Hero / Main Benefit** | App icon + tagline + home screen. This is the ONLY one most people see. |
| #2 | **Differentiator** | What makes this app unique vs competitors |
| #3 | **Ecosystem** | Widgets, extensions, watch — beyond the main app. Skip if N/A. |
| #4+ | **Core Features** | One feature per slide, most important first |
| 2nd to last | **Trust Signal** | Identity/craft — "made for people who [X]" |
| Last | **More Features** | Pills listing extras + coming soon. Skip if few features. |

**Rules:**

- Each slide sells ONE idea. Never two features on one slide.
- Vary layouts across slides — never repeat the same template structure.
- Include 1-2 contrast slides (inverted bg) for visual rhythm.

## Step 4: Write Copy FIRST

Get all headlines approved before building layouts. Bad copy ruins good design.

### The Iron Rules

1. **One idea per headline.** Never join two things with "and."
2. **Short, common words.** 1-2 syllables. No jargon unless it's domain-specific.
3. **3-5 words per line.** Must be readable at thumbnail size in the App Store.
4. **Line breaks are intentional.** Control where lines break with `<br />`.

### Three Approaches (pick one per slide)

| Type | What it does | Example |
|------|-------------|---------|
| **Paint a moment** | You picture yourself doing it | "Check your coffee without opening the app." |
| **State an outcome** | What your life looks like after | "A home for every coffee you buy." |
| **Kill a pain** | Name a problem and destroy it | "Never waste a great bag of coffee." |

### What NEVER Works

- **Feature lists as headlines**: "Log every item with tags, categories, and notes"
- **Two ideas joined by "and"**: "Track X and never miss Y"
- **Compound clauses**: "Save and customize X for every Y you own"
- **Vague aspirational**: "Every item, tracked"
- **Marketing buzzwords**: "AI-powered tips" (unless it's actually AI)

### Copy Process

1. Write 3 options per slide using the three approaches
2. Read each at arm's length — if you can't parse it in 1 second, it's too complex
3. Check: does each line have 3-5 words? If not, adjust line breaks
4. Present options to the user with reasoning for each

### Reference Apps for Copy Style

- **Raycast** — specific, descriptive, one concrete value per slide
- **Turf** — ultra-simple action verbs, conversational
- **Mela / Notion** — warm, minimal, elegant

## Step 5: Build the Page

### Architecture

Keep `page.tsx` focused on slide composition. Reuse the bootstrapped helper files instead of pasting the support code inline.

- `src/lib/app-store-screenshots/frame-presets.ts`
  Contains `SIZES`, `FRAME_PRESETS`, and `selectFrameForSize(...)`
- `src/lib/app-store-screenshots/frame-specs.ts`
  Contains the fallback mockup measurements and your measured fastlane frame metadata
- `src/lib/app-store-screenshots/phone-frame.tsx`
  Contains the reusable device/frame overlay component
- `src/lib/app-store-screenshots/export-png.ts`
  Contains the `html-to-image` export helper plus locale-aware filename and manifest helpers
- `src/lib/app-store-screenshots/localization.ts`
  Contains supported locale metadata, `i18next` resources, and document locale syncing
- `src/lib/app-store-screenshots/screenshot-content.ts`
  Contains the localized slide/content schema and locale-aware deck builder
- `src/lib/app-store-screenshots/use-localized-screenshot-app.tsx`
  Contains the runtime locale state hook plus loaders for one-app multi-locale previews and exports
- `src/lib/app-store-screenshots/layout-direction.ts`
  Contains RTL/LTR-aware alignment and mirroring helpers

For App Store work, design each Apple device/orientation set at its largest required size and scale down within that family where needed.
For Android and Mac marketing mockups, treat the frame canvas as the native composition size for that preset unless you have campaign-specific export requirements.

### Auto-Match Frame Choice By Size

Do **not** hardcode one frame for every export. The bundled `frame-presets.ts` already implements the matching logic:

1. Normalize filenames in `public/frames/`
2. Try exact preset id matches
3. Try aliases
4. Score nearest candidates by aspect ratio and area
5. Fall back to `mockup.png`

Use that helper for both preview rendering and export rendering so each output size gets the closest matching device frame automatically.

### Rendering Strategy

Each screenshot is designed at the largest required resolution for its current device/orientation family. Two copies exist:

1. **Preview**: CSS `transform: scale()` via ResizeObserver to fit a grid card
2. **Export**: Offscreen at `position: absolute; left: -9999px` at true resolution

### Phone Component and Frame Specs

Do not retype the mockup math in the skill body. Reuse:

- `frame-specs.ts` for the bundled fallback mockup measurements
- `phone-frame.tsx` for the device frame + screenshot overlay component

### Frame Metadata Rules

Fastlane frames are not all measured the same way. Do not assume every PNG shares the `mockup.png` screen inset values.

Use this approach:

1. Keep per-frame screen inset metadata in a `FRAME_SPECS` object keyed by the lowercased frame filename stem.
2. Add entries only for the frames actually present in `public/frames/`.
3. Prefer generating those entries with `scripts/measure_frame_insets.py` rather than hand-measuring every bezel.
4. Reuse one preset across color variants of the same device/orientation pair.
5. If a fastlane frame exists but has no measured inset yet, temporarily route that size to `mockup.png` rather than guessing and shipping a misaligned result.

The bundled `frame-specs.ts` includes:

- a `FALLBACK_FRAME_SPEC` for `mockup.png`
- a starter `FRAME_SPECS` object
- `getFrameSpec(framePath)` so the UI can route unknown frames back to the fallback spec

The important part is the workflow: **auto-measure once per frame, then auto-select by target screenshot size**. Do not handwire slide components to a single device.

### Localization Workflow

Do not keep screenshot copy inline in `page.tsx`. Treat locale files as the source of truth.

Use this approach:

1. Keep locale metadata in `src/lib/app-store-screenshots/localization.ts`.
2. Keep screenshot UI strings in `src/locales/<locale>/ui.json`.
3. Keep localized slide copy in `src/locales/<locale>/slides.json`.
4. Keep non-translated slide structure in `src/lib/app-store-screenshots/screenshot-content.ts`.
5. Use `src/lib/app-store-screenshots/use-localized-screenshot-app.tsx` as the app-level locale state source so previews and exports can switch locales without rebuilding.
6. Allow locale-specific screenshot asset overrides through the locale slide JSON when a market needs different imagery.
7. Sync `document.documentElement.lang` and `dir` when the active locale changes.

For translation maintenance, prefer the bundled `locallama.config.json`:

```bash
locallama --config ./locallama.config.json stats
locallama --config ./locallama.config.json fill --lang ar,fr
locallama --config ./locallama.config.json check
```

Use `docs/translation-style-guide.txt` as the project-specific guidance file when you need to tighten copy style before filling or reviewing translations.

### Layout and Orientation Notes

- iPhone portrait remains the default hero layout.
- For iPhone landscape and iPad landscape, treat the canvas as editorial spread space: put headline/caption on one side and device imagery on the other.
- For iPad portrait, give the device more breathing room than iPhone portrait. The bezel is visually lighter, so compensate with stronger composition and larger type blocks.
- For Android phones, expect tighter screen cutouts and slightly less generous bezel padding than iPhone frames.
- For Mac laptop frames, use wider editorial layouts, smaller tilt angles, and more surrounding whitespace than phone/tablet compositions.
- Do not blindly rotate portrait compositions into landscape. Re-compose them.

### Typography (Resolution-Independent)

All sizing relative to canvas width W:

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| Category label | `W * 0.028` | 600 (semibold) | default |
| Headline | `W * 0.09` to `W * 0.1` | 700 (bold) | 1.0 |
| Hero headline | `W * 0.1` | 700 (bold) | 0.92 |

### Device Placement Patterns

Vary across slides — NEVER use the same layout twice in a row:

**Centered device** (hero, single-feature, mostly portrait):

```
bottom: 0, width: "82-86%", translateX(-50%) translateY(12-14%)
```

**Two devices layered** (comparison, before/after, ecosystem):

```
Back: left: "-8%", width: "65%", rotate(-4deg), opacity: 0.55
Front: right: "-4%", width: "82%", translateY(10%)
```

**Device + floating elements** (only if user provided component PNGs):

```
Cards should NOT block the device's main content.
Position at edges, slight rotation (2-5deg), drop shadows.
If distracting, push partially off-screen or make smaller.
```

**Landscape split** (best default for iPad landscape, Android tablet, Mac, and wide iPhone slides):
```
Text block: left 8-10%, width 34-40%, vertically centered
Device: right 4-8%, width 52-58%, slight tilt only if it helps
```

### "More Features" Slide (Optional)

Dark/contrast background with app icon, headline ("And so much more."), and feature pills. Can include a "Coming Soon" section with dimmer pills.

## Step 6: Export

### Why html-to-image, NOT html2canvas

`html2canvas` breaks on CSS filters, gradients, drop-shadow, backdrop-filter, and complex clipping. `html-to-image` uses native browser SVG serialization — handles all CSS faithfully.

### Export Implementation

Do not paste the export workaround from memory. Reuse `src/lib/app-store-screenshots/export-png.ts`.

### Key Rules

- **Double-call trick**: First `toPng()` loads fonts/images lazily. Second produces clean output. Without this, exports are blank.
- **On-screen for capture**: Temporarily move to `left: 0` before calling `toPng`.
- **Offscreen container**: Use `position: absolute; left: -9999px` (not `fixed`).
- **Resizing**: Load data URL into Image, draw onto canvas at target size.
- 300ms delay between sequential exports.
- Set `fontFamily` on the offscreen container.
- **Numbered filenames**: Prefix exports with zero-padded index so they sort correctly: `01-hero-1320x2868.png`, `02-freshness-1320x2868.png`, etc. Use `String(index + 1).padStart(2, "0")`.
- Keep export outputs grouped by locale, for example `exports/en/...` and `exports/ar/...`.
- Record locale, direction, size key, and frame path in the export manifest entries so localized screenshot sets stay auditable.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| All slides look the same | Vary device position (center, left, right, layered devices, text-led) |
| Decorative elements invisible | Increase size and opacity — better too visible than invisible |
| Copy is too complex | "One second at arm's length" test |
| Floating elements block the device | Move off-screen edges or above the frame |
| Plain white/black background | Use gradients — even subtle ones add depth |
| Too cluttered | Remove floating elements, simplify to device + caption |
| Too simple/empty | Add larger decorative elements, floating items at edges |
| Headlines use "and" | Split into two slides or pick one idea |
| No visual contrast across slides | Mix light and dark backgrounds |
| Export is blank | Use double-call trick; move element on-screen before capture |
