import type { CSSProperties } from "react";

import { getFrameSpec } from "./frame-specs";

const SCREEN_BLEED_PX = 2;

type PhoneFrameProps = {
  screenshotSrc: string;
  screenshotAlt: string;
  framePath?: string;
  style?: CSSProperties;
  className?: string;
};

export function PhoneFrame({
  screenshotSrc,
  screenshotAlt,
  framePath = "/mockup.png",
  style,
  className = "",
}: PhoneFrameProps) {
  const spec = getFrameSpec(framePath);

  return (
    <div
      className={`relative ${className}`}
      style={{ aspectRatio: `${spec.frameW}/${spec.frameH}`, ...style }}
    >
      <div
        className="absolute z-10 overflow-hidden"
        style={{
          left: `calc(${spec.screen.left}% - ${SCREEN_BLEED_PX}px)`,
          top: `calc(${spec.screen.top}% - ${SCREEN_BLEED_PX}px)`,
          width: `calc(${spec.screen.width}% + ${SCREEN_BLEED_PX * 2}px)`,
          height: `calc(${spec.screen.height}% + ${SCREEN_BLEED_PX * 2}px)`,
          borderRadius: `${spec.screen.rx}% / ${spec.screen.ry}%`,
        }}
      >
        <img
          src={screenshotSrc}
          alt={screenshotAlt}
          className="block h-full w-full object-cover object-top"
          draggable={false}
        />
      </div>
      <img
        src={spec.framePath}
        alt=""
        className="absolute inset-0 z-20 block h-full w-full"
        draggable={false}
      />
    </div>
  );
}
