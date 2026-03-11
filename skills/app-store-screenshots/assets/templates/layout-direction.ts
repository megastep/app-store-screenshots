import type { CSSProperties } from "react";

import type { LocaleDirection } from "./localization";

export function textAlignForDir(dir: LocaleDirection): CSSProperties["textAlign"] {
  return dir === "rtl" ? "right" : "left";
}

export function inlinePositionForDir(
  dir: LocaleDirection,
  start: string | number | undefined,
  end: string | number | undefined,
): CSSProperties {
  return dir === "rtl" ? { right: start, left: end } : { left: start, right: end };
}

export function inlineTranslateForDir(dir: LocaleDirection, amount: string) {
  return dir === "rtl" ? amount.replace("-", "") : amount;
}

export function maybeMirrorRotation(dir: LocaleDirection, degrees: number) {
  return dir === "rtl" ? degrees * -1 : degrees;
}
