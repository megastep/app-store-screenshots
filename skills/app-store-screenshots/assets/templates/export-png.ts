import { toPng } from "html-to-image";

const warmRenderCache = new WeakMap<HTMLElement, Set<string>>();

export async function exportNodeToPng(
  element: HTMLElement,
  width: number,
  height: number,
) {
  const previous = {
    left: element.style.left,
    opacity: element.style.opacity,
    zIndex: element.style.zIndex,
  };

  element.style.left = "0px";
  element.style.opacity = "1";
  element.style.zIndex = "-1";

  const options = {
    width,
    height,
    pixelRatio: 1,
    cacheBust: true,
  };

  const warmKey = `${width}x${height}`;
  const warmed = warmRenderCache.get(element) ?? new Set<string>();
  if (!warmRenderCache.has(element)) {
    warmRenderCache.set(element, warmed);
  }
  if (!warmed.has(warmKey)) {
    await toPng(element, options);
    warmed.add(warmKey);
  }
  const dataUrl = await toPng(element, options);

  element.style.left = previous.left;
  element.style.opacity = previous.opacity;
  element.style.zIndex = previous.zIndex;

  return dataUrl;
}
