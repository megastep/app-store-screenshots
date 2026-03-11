import { toPng } from "html-to-image";

const warmRenderCache = new WeakMap<HTMLElement, Set<string>>();

export type ExportDirection = "ltr" | "rtl";

export type ExportArtifactMeta = {
  locale: string;
  dir: ExportDirection;
  slideId: string;
  slideLabel?: string;
  index: number;
  sizeKey: string;
  width: number;
  height: number;
  framePath: string;
};

export type ExportManifestEntry = ExportArtifactMeta & {
  fileName: string;
  outputDir: string;
};

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

function slugifyPart(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

export function getLocaleExportDir(locale: string) {
  return `exports/${locale}`;
}

export function buildExportFileName(meta: ExportArtifactMeta) {
  const label = slugifyPart(meta.slideLabel ?? meta.slideId) || "slide";
  return `${String(meta.index + 1).padStart(2, "0")}-${label}-${meta.locale}-${meta.width}x${meta.height}.png`;
}

export function createExportManifestEntry(meta: ExportArtifactMeta): ExportManifestEntry {
  return {
    ...meta,
    fileName: buildExportFileName(meta),
    outputDir: getLocaleExportDir(meta.locale),
  };
}

export function downloadDataUrl(dataUrl: string, fileName: string) {
  const anchor = document.createElement("a");
  anchor.href = dataUrl;
  anchor.download = fileName;
  anchor.click();
}
