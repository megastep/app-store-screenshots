# Napkin

- 2026-03-10: The first `measure_frame_insets.py` implementation used a pure-Python PNG decoder for every frame. That worked on samples but was too slow across the full Fastlane cache. Prefer Pillow-backed alpha extraction for cache-wide passes and keep the manual decoder only as a fallback.
- 2026-03-10: Some cached `~/.fastlane/frameit/latest/*.png` files are actually HTML error pages. Treat extension-only image detection as untrusted and skip unreadable assets instead of aborting the whole measurement pass.
- 2026-03-10: Review bots correctly flagged CLI-fed template substitutions as a code injection surface. Any value inserted into generated code needs explicit validation, not just "trusted usage" assumptions.
