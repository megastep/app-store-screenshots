"use client";

import { startTransition, useEffect, useState } from "react";
import type { TFunction, i18n } from "i18next";

import {
  createLocalization,
  DEFAULT_LOCALE,
  getLocaleOptions,
  getSupportedLocale,
  SUPPORTED_LOCALES,
  syncDocumentLocale,
  type LocaleDefinition,
  type LocaleNamespace,
} from "./localization";
import { buildLocalizedDeck, type LocalizedDeck } from "./screenshot-content";

export type LocalizedScreenshotApp = {
  i18n: i18n;
  locale: LocaleDefinition;
  deck: LocalizedDeck;
  t: TFunction<LocaleNamespace, undefined>;
};

export type LocalizedScreenshotAppState = {
  status: "loading" | "ready" | "error";
  localeCode: string;
  locale: LocaleDefinition;
  deck?: LocalizedDeck;
  t?: TFunction<LocaleNamespace, undefined>;
  error?: Error;
};

export async function loadLocalizedScreenshotApp(localeCode: string): Promise<LocalizedScreenshotApp> {
  const { i18n, locale, t } = await createLocalization(localeCode);
  syncDocumentLocale(locale.code);
  return {
    i18n,
    locale,
    deck: buildLocalizedDeck(i18n, locale.code),
    t,
  };
}

export async function loadAllLocalizedScreenshotApps(localeCodes = SUPPORTED_LOCALES.map((locale) => locale.code)) {
  return Promise.all(localeCodes.map((localeCode) => loadLocalizedScreenshotApp(localeCode)));
}

export function useLocalizedScreenshotApp(initialLocaleCode = DEFAULT_LOCALE.code) {
  const initialLocale = getSupportedLocale(initialLocaleCode);
  const [localeCode, setLocaleCode] = useState(initialLocale.code);
  const [state, setState] = useState<LocalizedScreenshotAppState>({
    status: "loading",
    localeCode: initialLocale.code,
    locale: initialLocale,
  });

  useEffect(() => {
    let cancelled = false;
    const targetLocale = getSupportedLocale(localeCode);

    setState((current) => ({
      ...current,
      status: "loading",
      localeCode: targetLocale.code,
      locale: targetLocale,
      error: undefined,
    }));

    void loadLocalizedScreenshotApp(targetLocale.code)
      .then((app) => {
        if (cancelled) {
          return;
        }
        setState({
          status: "ready",
          localeCode: app.locale.code,
          locale: app.locale,
          deck: app.deck,
          t: app.t,
        });
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        setState((current) => ({
          ...current,
          status: "error",
          error: error instanceof Error ? error : new Error(String(error)),
        }));
      });

    return () => {
      cancelled = true;
    };
  }, [localeCode]);

  return {
    ...state,
    localeOptions: getLocaleOptions(),
    setActiveLocale(nextLocaleCode: string) {
      startTransition(() => {
        setLocaleCode(getSupportedLocale(nextLocaleCode).code);
      });
    },
  };
}
