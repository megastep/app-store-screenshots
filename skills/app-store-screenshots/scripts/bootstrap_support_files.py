#!/usr/bin/env python3
"""
Copy the reusable support files for the App Store screenshots skill into a project.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
LOCALE_RE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
LOCALE_LABELS = {
    "ar": "Arabic",
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "he": "Hebrew",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "nl": "Dutch",
    "pl": "Polish",
    "pt-BR": "Portuguese (Brazil)",
    "pt-PT": "Portuguese (Portugal)",
    "ru": "Russian",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
}


def copy_file(source: Path, destination: Path, overwrite: bool) -> None:
    if destination.exists() and not overwrite:
        print(f"[skip] {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    print(f"[copy] {source.name} -> {destination}")


def write_file(destination: Path, content: str, overwrite: bool) -> None:
    if destination.exists() and not overwrite:
        print(f"[skip] {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    print(f"[write] {destination}")


def write_json(destination: Path, payload: object, overwrite: bool) -> None:
    write_file(destination, json.dumps(payload, indent=2, ensure_ascii=False) + "\n", overwrite)


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


def validate_identifier(value: str, label: str) -> str:
    if not IDENTIFIER_RE.fullmatch(value):
        raise SystemExit(f"Invalid {label}: {value!r}. Use only letters, digits, and underscores, and do not start with a digit.")
    return value


def parse_locales(value: str, label: str) -> list[str]:
    locales = [part.strip() for part in value.split(",") if part.strip()]
    if not locales:
        raise SystemExit(f"{label} must include at least one locale.")
    for locale in locales:
        if not LOCALE_RE.fullmatch(locale):
            raise SystemExit(f"Invalid locale code in {label}: {locale!r}")
    return locales


def infer_lang(locale: str) -> str:
    return locale.split("-")[0].lower()


def infer_label(locale: str) -> str:
    return LOCALE_LABELS.get(locale) or LOCALE_LABELS.get(infer_lang(locale)) or locale


def build_supported_locales(locales: list[str], default_locale: str, rtl_locales: set[str]) -> str:
    rows = []
    for locale in locales:
        rows.append(
            '  { code: "%s", lang: "%s", label: "%s", dir: "%s", source: %s },'
            % (
                locale,
                infer_lang(locale),
                infer_label(locale).replace('"', '\\"'),
                "rtl" if locale in rtl_locales else "ltr",
                "true" if locale == default_locale else "false",
            )
        )
    return "\n".join(rows)


def build_i18n_imports(locales: list[str]) -> str:
    lines: list[str] = []
    for locale in locales:
        alias = locale.replace("-", "_")
        lines.append(f'import {alias}Ui from "@/locales/{locale}/ui.json";')
        lines.append(f'import {alias}Slides from "@/locales/{locale}/slides.json";')
    return "\n".join(lines)


def build_i18n_resources(locales: list[str]) -> str:
    lines: list[str] = []
    for locale in locales:
        alias = locale.replace("-", "_")
        lines.extend(
            [
                f'  "{locale}": {{',
                f"    ui: {alias}Ui,",
                f"    slides: {alias}Slides,",
                "  },",
            ]
        )
    return "\n".join(lines)


def build_locallama_targets(locales: list[str], default_locale: str) -> str:
    targets = [locale for locale in locales if locale != default_locale]
    if not targets:
        return ""
    return ", ".join(json.dumps(locale) for locale in targets)


def build_translation_style_guide(default_locale: str, rtl_locales: set[str]) -> str:
    rtl_note = ", ".join(sorted(rtl_locales)) if rtl_locales else "none"
    return "\n".join(
        [
            "Keep translation copy short, concrete, and thumbnail-readable.",
            "Preserve screenshot export labels as compact slugs where possible.",
            "Keep product names, file names, and placeholders unchanged.",
            f"Source locale: {default_locale}.",
            f"RTL locales in this project: {rtl_note}.",
            "For RTL languages, preserve meaning first and avoid overlong headlines that break split layouts.",
            "",
        ]
    )


def build_ui_messages(locale: str, is_source: bool) -> dict[str, str]:
    if locale == "ar" and not is_source:
        return {
            "appTitle": "استوديو لقطات الشاشة",
            "localeLabel": "اللغة",
            "directionLabel": "الاتجاه",
            "exportCurrentLocale": "تصدير اللغة الحالية",
            "exportAllLocales": "تصدير كل اللغات",
            "rtlBadge": "من اليمين إلى اليسار",
            "ltrBadge": "من اليسار إلى اليمين",
            "slidesLabel": "الشرائح",
            "exportsLabel": "عمليات التصدير",
        }
    if not is_source:
        return {
            "appTitle": "",
            "localeLabel": "",
            "directionLabel": "",
            "exportCurrentLocale": "",
            "exportAllLocales": "",
            "rtlBadge": "",
            "ltrBadge": "",
            "slidesLabel": "",
            "exportsLabel": "",
        }
    label = infer_label(locale)
    return {
        "appTitle": "Screenshot Studio",
        "localeLabel": "Locale",
        "directionLabel": "Direction",
        "exportCurrentLocale": "Export current locale",
        "exportAllLocales": "Export all locales",
        "rtlBadge": "RTL",
        "ltrBadge": "LTR",
        "slidesLabel": "Slides",
        "exportsLabel": f"Exports ({label})",
    }


def build_slide_messages(locale: str, is_source: bool) -> dict[str, object]:
    if locale == "ar" and not is_source:
        return {
            "deck": {
                "appName": "بلوم كوفي",
                "tagline": "قهوة أفضل في كل مرة",
                "slides": {
                    "hero": {
                        "kicker": "مفكرة القهوة",
                        "title": "حضّر كوبًا أفضل كل صباح",
                        "body": "احفظ كل حبة ووصفة وملاحظة تذوق في مكان واحد.",
                        "exportLabel": "hero-ar",
                    },
                    "insights": {
                        "kicker": "رؤى التذوق",
                        "title": "اعرف ما الذي تغيّر بسرعة",
                        "body": "قارن بين التحضيرات جنبًا إلى جنب واعرف ما الذي تحسّن فعلًا.",
                        "exportLabel": "insights-ar",
                    },
                },
            }
        }
    if not is_source:
        return {
            "deck": {
                "appName": "",
                "tagline": "",
                "slides": {
                    "hero": {
                        "kicker": "",
                        "title": "",
                        "body": "",
                        "exportLabel": "",
                    },
                    "insights": {
                        "kicker": "",
                        "title": "",
                        "body": "",
                        "exportLabel": "",
                    },
                },
            }
        }
    return {
        "deck": {
            "appName": "Bloom Coffee",
            "tagline": "Brew with confidence",
            "slides": {
                "hero": {
                    "kicker": "Coffee journal",
                    "title": "Brew better every morning",
                    "body": "Save each bag, recipe, and tasting note in one place.",
                    "exportLabel": "hero",
                },
                "insights": {
                    "kicker": "Taste insights",
                    "title": "Spot what changed fast",
                    "body": "Compare brews side by side and see what actually improved.",
                    "exportLabel": "insights",
                },
            },
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy reusable screenshot generator support files into a Next.js project.")
    parser.add_argument("--project-root", default=".", help="Target project root. Default: current directory")
    parser.add_argument("--font-import", default="Inter", help="Google font import name used in layout.tsx")
    parser.add_argument("--font-const", default="font", help="Local font constant name used in layout.tsx")
    parser.add_argument("--locales", default="en,ar", help="Comma-separated locale codes to scaffold. Default: en,ar")
    parser.add_argument("--default-locale", default="en", help="Source/default locale code. Default: en")
    parser.add_argument("--rtl-locales", default="ar", help="Comma-separated RTL locale codes. Default: ar")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--with-layout", action="store_true", help="Also write src/app/layout.tsx from the template")
    args = parser.parse_args()

    font_import = validate_identifier(args.font_import, "font import")
    font_const = validate_identifier(args.font_const, "font const")
    locales = parse_locales(args.locales, "--locales")
    default_locale = args.default_locale.strip()
    if default_locale not in locales:
        raise SystemExit(f"--default-locale must be included in --locales. Missing: {default_locale!r}")
    rtl_locales = set(parse_locales(args.rtl_locales, "--rtl-locales")) if args.rtl_locales.strip() else set()
    unknown_rtl = sorted(rtl_locales - set(locales))
    if unknown_rtl:
        raise SystemExit(f"RTL locales must also appear in --locales: {', '.join(unknown_rtl)}")

    skill_root = Path(__file__).resolve().parents[1]
    templates_root = skill_root / "assets" / "templates"
    project_root = Path(args.project_root).resolve()

    copy_file(skill_root / "mockup.png", project_root / "public" / "mockup.png", args.overwrite)
    (project_root / "public" / "frames").mkdir(parents=True, exist_ok=True)
    (project_root / "public" / "screenshots" / "shared").mkdir(parents=True, exist_ok=True)
    for locale in locales:
        (project_root / "public" / "screenshots" / locale).mkdir(parents=True, exist_ok=True)

    copy_map = {
        templates_root / "frame-presets.ts": project_root / "src" / "lib" / "app-store-screenshots" / "frame-presets.ts",
        templates_root / "frame-specs.ts": project_root / "src" / "lib" / "app-store-screenshots" / "frame-specs.ts",
        templates_root / "phone-frame.tsx": project_root / "src" / "lib" / "app-store-screenshots" / "phone-frame.tsx",
        templates_root / "export-png.ts": project_root / "src" / "lib" / "app-store-screenshots" / "export-png.ts",
        templates_root / "layout-direction.ts": project_root / "src" / "lib" / "app-store-screenshots" / "layout-direction.ts",
        templates_root / "use-localized-screenshot-app.tsx": project_root / "src" / "lib" / "app-store-screenshots" / "use-localized-screenshot-app.tsx",
    }

    for source, destination in copy_map.items():
        copy_file(source, destination, args.overwrite)

    write_template(
        templates_root / "localization.ts.template",
        project_root / "src" / "lib" / "app-store-screenshots" / "localization.ts",
        args.overwrite,
        {
            "__I18N_IMPORTS__": build_i18n_imports(locales),
            "__SUPPORTED_LOCALES__": build_supported_locales(locales, default_locale, rtl_locales),
            "__DEFAULT_LOCALE__": default_locale,
            "__I18N_RESOURCES__": build_i18n_resources(locales),
        },
    )

    copy_file(
        templates_root / "screenshot-content.ts.template",
        project_root / "src" / "lib" / "app-store-screenshots" / "screenshot-content.ts",
        args.overwrite,
    )

    if args.with_layout:
        write_template(
            templates_root / "layout.tsx.template",
            project_root / "src" / "app" / "layout.tsx",
            args.overwrite,
            {
                "__FONT_IMPORT__": font_import,
                "__FONT_CONST__": font_const,
            },
        )

    for locale in locales:
        is_source = locale == default_locale
        write_json(project_root / "src" / "locales" / locale / "ui.json", build_ui_messages(locale, is_source), args.overwrite)
        write_json(project_root / "src" / "locales" / locale / "slides.json", build_slide_messages(locale, is_source), args.overwrite)

    write_template(
        templates_root / "locallama.config.json.template",
        project_root / "locallama.config.json",
        args.overwrite,
        {
            "__SOURCE_LANGUAGE__": default_locale,
            "__TARGET_LANGUAGES__": build_locallama_targets(locales, default_locale),
        },
    )

    write_file(
        project_root / "docs" / "translation-style-guide.txt",
        build_translation_style_guide(default_locale, rtl_locales),
        args.overwrite,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
