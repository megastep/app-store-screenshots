# Napkin

- 2026-03-10: The first `measure_frame_insets.py` implementation used a pure-Python PNG decoder for every frame. That worked on samples but was too slow across the full Fastlane cache. Prefer Pillow-backed alpha extraction for cache-wide passes and keep the manual decoder only as a fallback.
- 2026-03-10: Some cached `~/.fastlane/frameit/latest/*.png` files are actually HTML error pages. Treat extension-only image detection as untrusted and skip unreadable assets instead of aborting the whole measurement pass.
- 2026-03-10: Review bots correctly flagged CLI-fed template substitutions as a code injection surface. Any value inserted into generated code needs explicit validation, not just "trusted usage" assumptions.
- 2026-03-11: Cache-first asset resolution needs per-bucket fallback, not all-or-nothing fallback. A partially populated local cache is common and should not disable GitHub resolution for missing families.
- 2026-03-11: Fastlane iPhone frame alpha alone under-measures notch/Dynamic Island displays because the center top overlay is opaque. For single-image framing, extend portrait iPhone screen boxes upward by scanning for split transparent shoulder rows before pasting the screenshot.
- 2026-03-11: The shared `frame-insets` references should store the true full display rect for notch iPhones, plus an explicit `topOverlayCutout` box. A plain rectangular `screen` below the notch bakes the bug into every downstream renderer.
