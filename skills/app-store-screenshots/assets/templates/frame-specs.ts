export type FrameSpec = {
  framePath: string;
  frameW: number;
  frameH: number;
  screen: {
    left: number;
    top: number;
    width: number;
    height: number;
    rx: number;
    ry: number;
  };
};

const MK_W = 1022;
const MK_H = 2082;

export const FALLBACK_FRAME_SPEC: FrameSpec = {
  framePath: "/mockup.png",
  frameW: MK_W,
  frameH: MK_H,
  screen: {
    left: (52 / MK_W) * 100,
    top: (46 / MK_H) * 100,
    width: (918 / MK_W) * 100,
    height: (1990 / MK_H) * 100,
    rx: (126 / 918) * 100,
    ry: (126 / 1990) * 100,
  },
};

export const FRAME_SPECS: Record<string, FrameSpec> = {
  "iphone-16-pro-max": {
    framePath: "/frames/iphone-16-pro-max.png",
    frameW: 1320,
    frameH: 2868,
    screen: { left: 4.0, top: 1.8, width: 92.0, height: 95.2, rx: 12.5, ry: 5.8 },
  },
  // Add measured fastlane frame specs here.
  // Preferred source: generate them with scripts/measure_frame_insets.py and copy
  // only the entries for frames you actually keep in public/frames/.
  // Typical next entries:
  // "iphone-16-pro-max-landscape": { ... }
  // "ipad-pro-13": { ... }
  // "ipad-pro-13-landscape": { ... }
  // "ipad-pro-11": { ... }
  // "ipad-pro-11-landscape": { ... }
};

export function getFrameSpec(framePath: string) {
  const key = framePath
    .split("/")
    .pop()
    ?.replace(/\.[a-z]+$/i, "")
    .toLowerCase();

  return (key && FRAME_SPECS[key]) || FALLBACK_FRAME_SPEC;
}
