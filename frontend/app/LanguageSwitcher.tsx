"use client";

import { useEffect, useRef, useState } from "react";
import { LANGS, useI18n, type Lang } from "./lib/i18n";

export default function LanguageSwitcher({ className }: { className?: string }) {
  const { lang, setLang } = useI18n();
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const current = LANGS.find((l) => l.code === lang) ?? LANGS[0];

  return (
    <div className={`lang-switch notranslate ${className ?? ""}`} translate="no" ref={wrapRef}>
      <button
        type="button"
        className="lang-switch-btn"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={`Language: ${current.label}`}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="lang-switch-flag" aria-hidden>{current.flag}</span>
        <span className="lang-switch-code">{current.code.toUpperCase()}</span>
        <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
      {open && (
        <ul className="lang-switch-menu" role="listbox" aria-label="Choose language">
          {LANGS.map((l) => (
            <li key={l.code}>
              <button
                type="button"
                role="option"
                aria-selected={l.code === lang}
                className={`lang-switch-item ${l.code === lang ? "is-active" : ""}`}
                onClick={() => {
                  setLang(l.code as Lang);
                  setOpen(false);
                }}
              >
                <span className="lang-switch-flag" aria-hidden>{l.flag}</span>
                <span className="lang-switch-native">{l.native}</span>
                <span className="lang-switch-en">{l.label}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
