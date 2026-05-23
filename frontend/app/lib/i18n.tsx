"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";

import { DICTS, en, tFor } from "./dicts";
import { isLang, LANG_COOKIE, LANGS, type Lang } from "./langs";

export { LANGS };
export type { Lang };

type Ctx = {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;
};

const I18nContext = createContext<Ctx | null>(null);

const STORAGE_KEY = LANG_COOKIE;

function detectInitial(): Lang {
  if (typeof window === "undefined") return "en";
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (isLang(stored)) return stored;
  } catch {}
  // Also try cookie (set by previous session or server)
  try {
    const m = document.cookie.match(new RegExp("(?:^|; )" + LANG_COOKIE + "=([^;]+)"));
    if (m && isLang(m[1])) return m[1] as Lang;
  } catch {}
  const nav = (typeof navigator !== "undefined" ? navigator.language : "en")
    .slice(0, 2)
    .toLowerCase();
  return isLang(nav) ? nav : "en";
}

function writeCookie(l: Lang) {
  if (typeof document === "undefined") return;
  const expire = "expires=Fri, 31 Dec 9999 23:59:59 GMT";
  document.cookie = `${LANG_COOKIE}=${l}; path=/; ${expire}; SameSite=Lax`;
}

function applyHtmlLang(l: Lang) {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("lang", l);
  const meta = LANGS.find((x) => x.code === l);
  document.documentElement.setAttribute("dir", meta?.rtl ? "rtl" : "ltr");
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");

  useEffect(() => {
    const initial = detectInitial();
    setLangState(initial);
    applyHtmlLang(initial);
    writeCookie(initial);
  }, []);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    try {
      localStorage.setItem(STORAGE_KEY, l);
    } catch {}
    writeCookie(l);
    applyHtmlLang(l);
    if (typeof window !== "undefined") {
      // Reload so server-rendered pages re-fetch with the new cookie.
      window.location.reload();
    }
  }, []);

  const t = useCallback((key: string) => tFor(lang, key), [lang]);

  return <I18nContext.Provider value={{ lang, setLang, t }}>{children}</I18nContext.Provider>;
}

export function useI18n(): Ctx {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    return {
      lang: "en",
      setLang: () => {},
      t: (k: string) => en[k] ?? k,
    };
  }
  return ctx;
}

export { DICTS };
