export const SIZES = [
  { key: "iphone-6.9-portrait", family: "iphone", label: '6.9"', orientation: "portrait", w: 1320, h: 2868 },
  { key: "iphone-6.9-landscape", family: "iphone", label: '6.9"', orientation: "landscape", w: 2868, h: 1320 },
  { key: "iphone-6.5-portrait", family: "iphone", label: '6.5"', orientation: "portrait", w: 1284, h: 2778 },
  { key: "iphone-6.5-landscape", family: "iphone", label: '6.5"', orientation: "landscape", w: 2778, h: 1284 },
  { key: "iphone-6.3-portrait", family: "iphone", label: '6.3"', orientation: "portrait", w: 1206, h: 2622 },
  { key: "iphone-6.3-landscape", family: "iphone", label: '6.3"', orientation: "landscape", w: 2622, h: 1206 },
  { key: "iphone-6.1-portrait", family: "iphone", label: '6.1"', orientation: "portrait", w: 1125, h: 2436 },
  { key: "iphone-6.1-landscape", family: "iphone", label: '6.1"', orientation: "landscape", w: 2436, h: 1125 },
  { key: "ipad-13-portrait", family: "ipad", label: '13"', orientation: "portrait", w: 2064, h: 2752 },
  { key: "ipad-13-landscape", family: "ipad", label: '13"', orientation: "landscape", w: 2752, h: 2064 },
  { key: "ipad-11-portrait", family: "ipad", label: '11"', orientation: "portrait", w: 1488, h: 2266 },
  { key: "ipad-11-landscape", family: "ipad", label: '11"', orientation: "landscape", w: 2266, h: 1488 },
  { key: "android-phone-compact-portrait", family: "android-phone", label: "Android Compact", orientation: "portrait", w: 1204, h: 2456 },
  { key: "android-phone-large-portrait", family: "android-phone", label: "Android Large", orientation: "portrait", w: 1564, h: 3320 },
  { key: "android-tablet-landscape", family: "android-tablet", label: "Android Tablet", orientation: "landscape", w: 3313, h: 2304 },
  { key: "macbook-air-landscape", family: "mac", label: "MacBook Air", orientation: "landscape", w: 3306, h: 1897 },
  { key: "macbook-pro-16-landscape", family: "mac", label: "MacBook Pro 16", orientation: "landscape", w: 3910, h: 2241 },
] as const;

export const FRAME_PRESETS = [
  { id: "iphone-16-pro-max", family: "iphone", orientation: "portrait", canvas: { w: 1320, h: 2868 }, aliases: ["iphone 16 pro max", "iphone16promax", "6.9"], priority: 100 },
  { id: "iphone-16-pro-max-landscape", family: "iphone", orientation: "landscape", canvas: { w: 2868, h: 1320 }, aliases: ["iphone 16 pro max landscape", "iphone16promaxlandscape", "6.9 landscape"], priority: 100 },
  { id: "iphone-15-plus", family: "iphone", orientation: "portrait", canvas: { w: 1284, h: 2778 }, aliases: ["iphone 15 plus", "iphone15plus", "6.5"], priority: 100 },
  { id: "iphone-15-plus-landscape", family: "iphone", orientation: "landscape", canvas: { w: 2778, h: 1284 }, aliases: ["iphone 15 plus landscape", "iphone15pluslandscape", "6.5 landscape"], priority: 100 },
  { id: "iphone-16-pro", family: "iphone", orientation: "portrait", canvas: { w: 1206, h: 2622 }, aliases: ["iphone 16 pro", "iphone16pro", "6.3"], priority: 100 },
  { id: "iphone-16-pro-landscape", family: "iphone", orientation: "landscape", canvas: { w: 2622, h: 1206 }, aliases: ["iphone 16 pro landscape", "iphone16prolandscape", "6.3 landscape"], priority: 100 },
  { id: "iphone-16", family: "iphone", orientation: "portrait", canvas: { w: 1179, h: 2556 }, aliases: ["iphone 16", "iphone16", "6.1", "iphone 14 pro"], priority: 100 },
  { id: "iphone-16-landscape", family: "iphone", orientation: "landscape", canvas: { w: 2556, h: 1179 }, aliases: ["iphone 16 landscape", "iphone16landscape", "6.1 landscape", "iphone 14 pro landscape"], priority: 100 },
  { id: "ipad-pro-13", family: "ipad", orientation: "portrait", canvas: { w: 2064, h: 2752 }, aliases: ["ipad pro 13", "ipadpro13", "13", "13 portrait"], priority: 100 },
  { id: "ipad-pro-13-landscape", family: "ipad", orientation: "landscape", canvas: { w: 2752, h: 2064 }, aliases: ["ipad pro 13 landscape", "ipadpro13landscape", "13 landscape"], priority: 100 },
  { id: "ipad-pro-11", family: "ipad", orientation: "portrait", canvas: { w: 1488, h: 2266 }, aliases: ["ipad pro 11", "ipadpro11", "11", "11 portrait"], priority: 100 },
  { id: "ipad-pro-11-landscape", family: "ipad", orientation: "landscape", canvas: { w: 2266, h: 1488 }, aliases: ["ipad pro 11 landscape", "ipadpro11landscape", "11 landscape"], priority: 100 },
  { id: "google-pixel-5", family: "android-phone", orientation: "portrait", canvas: { w: 1204, h: 2456 }, aliases: ["google pixel 5", "pixel 5", "android compact"], priority: 100 },
  { id: "google-pixel-4-xl", family: "android-phone", orientation: "portrait", canvas: { w: 1564, h: 3320 }, aliases: ["google pixel 4 xl", "pixel 4 xl", "android large"], priority: 96 },
  { id: "samsung-galaxy-s21-ultra-5g", family: "android-phone", orientation: "portrait", canvas: { w: 1540, h: 3324 }, aliases: ["galaxy s21 ultra", "s21 ultra", "samsung galaxy s21 ultra 5g"], priority: 95 },
  { id: "google-pixel-slate", family: "android-tablet", orientation: "landscape", canvas: { w: 3313, h: 2304 }, aliases: ["pixel slate", "google pixel slate", "android tablet"], priority: 100 },
  { id: "apple-macbook-air", family: "mac", orientation: "landscape", canvas: { w: 3306, h: 1897 }, aliases: ["macbook air", "apple macbook air"], priority: 100 },
  { id: "apple-macbook-pro-16", family: "mac", orientation: "landscape", canvas: { w: 3910, h: 2241 }, aliases: ["macbook pro 16", "apple macbook pro 16"], priority: 100 },
] as const;

export type SizeSpec = (typeof SIZES)[number];
export type FramePreset = (typeof FRAME_PRESETS)[number];

export function normalizeFrameName(input: string) {
  return input.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

export function scoreFrame(target: SizeSpec, preset: FramePreset) {
  const targetRatio = target.w / target.h;
  const presetRatio = preset.canvas.w / preset.canvas.h;
  const ratioPenalty = Math.abs(targetRatio - presetRatio) * 10_000;
  const areaPenalty = Math.abs(target.w * target.h - preset.canvas.w * preset.canvas.h) / 10_000;
  const familyPenalty = preset.family === target.family ? 0 : 1_000_000;
  const orientationPenalty = preset.orientation === target.orientation ? 0 : 100_000;
  return familyPenalty + orientationPenalty + ratioPenalty + areaPenalty - preset.priority;
}

export function selectFrameForSize(target: SizeSpec, availableFrames: string[]) {
  const normalized = availableFrames.map((file) => ({
    file,
    key: normalizeFrameName(file.replace(/\.[a-z]+$/i, "")),
  }));

  const exact = FRAME_PRESETS.find((preset) =>
    preset.family === target.family &&
    preset.orientation === target.orientation &&
    normalized.some((entry) => entry.key === preset.id),
  );
  if (exact) {
    return normalized.find((entry) => entry.key === exact.id)?.file ?? "/mockup.png";
  }

  const aliasHit = FRAME_PRESETS.find((preset) =>
    preset.family === target.family &&
    preset.orientation === target.orientation &&
    normalized.some((entry) => preset.aliases.map((alias) => normalizeFrameName(alias)).includes(entry.key)),
  );
  if (aliasHit) {
    const normalizedAliases = aliasHit.aliases.map((alias) => normalizeFrameName(alias));
    const match = normalized.find((entry) => normalizedAliases.includes(entry.key));
    return match?.file ?? "/mockup.png";
  }

  const ranked = FRAME_PRESETS
    .filter((preset) => normalized.some((entry) => entry.key === preset.id))
    .sort((a, b) => scoreFrame(target, a) - scoreFrame(target, b));

  return ranked.length
    ? normalized.find((entry) => entry.key === ranked[0].id)?.file ?? "/mockup.png"
    : "/mockup.png";
}
