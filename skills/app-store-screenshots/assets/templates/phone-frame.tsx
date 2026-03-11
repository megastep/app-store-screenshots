import type { CSSProperties } from "react";

import { getFrameSpec } from "./frame-specs";

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
      <img src={spec.framePath} alt="" className="block h-full w-full" draggable={false} />
      <div
        className="absolute z-10 overflow-hidden"
        style={{
          left: `${spec.screen.left}%`,
          top: `${spec.screen.top}%`,
          width: `${spec.screen.width}%`,
          height: `${spec.screen.height}%`,
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
    </div>
  );
}
