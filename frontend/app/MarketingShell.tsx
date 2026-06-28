"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import LanguageSwitcher from "./LanguageSwitcher";
import ThemeToggle from "./ThemeToggle";
import { useI18n } from "./lib/i18n";
import { BOOKING_URL } from "./lib/site";

const DEMO_URL = BOOKING_URL;

export type NavLink = { href: string; label: string };

function defaultLinks(t: (k: string) => string): NavLink[] {
  return [
    { href: "/#how", label: t("nav.how") },
    { href: "/#deploy", label: t("nav.deploy") },
    { href: "/#industries", label: t("nav.industries") },
    { href: "/#why", label: t("nav.why") },
  ];
}

type TopbarProps = {
  links?: NavLink[];
  showBuiltBy?: boolean;
  ossPill?: string;
};

export function MarketingTopbar({
  links,
  showBuiltBy = false,
  ossPill,
}: TopbarProps) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const resolvedLinks = links ?? defaultLinks(t);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (!open) return;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = "";
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <>
    <div className={`topbar-wrap ${scrolled ? "is-scrolled" : ""}`}>
      <header className="topbar">
        <div className="brand-cluster">
          <Link href="/" className="brand" aria-label="Workflow Auth home">
            <span className="brand-mark"><Flame /></span>
            <span>Workflow Auth</span>
            {ossPill && <span className="oss-pill">{ossPill}</span>}
          </Link>
        </div>

        <nav className="nav-links" aria-label="Primary">
          {resolvedLinks.map((l) => (
            <Link key={l.href} href={l.href} className="nav-link">
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="topbar-right">
          <LanguageSwitcher />
          <ThemeToggle />
          <a
            href={DEMO_URL}
            target="_blank"
            rel="noreferrer"
            className="btn btn-primary topbar-cta"
          >
            {t("btn.bookDemo")}
          </a>
          <button
            type="button"
            className="topbar-burger"
            aria-label={open ? t("menu.close") : t("menu.open")}
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            <span className={`burger ${open ? "open" : ""}`}>
              <i /><i /><i />
            </span>
          </button>
        </div>
      </header>
    </div>

      {open && (
        <div className="mobile-sheet" role="dialog" aria-modal="true" aria-label={t("menu.open")}>
          <nav className="mobile-sheet-nav">
            {resolvedLinks.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="mobile-sheet-link"
                onClick={() => setOpen(false)}
              >
                {l.label}
              </Link>
            ))}
            <Link href="/faq" className="mobile-sheet-link" onClick={() => setOpen(false)}>
              {t("footer.faq")}
            </Link>
            <Link href="/contact" className="mobile-sheet-link" onClick={() => setOpen(false)}>
              {t("nav.contact")}
            </Link>
            <Link href="/login" className="mobile-sheet-link" onClick={() => setOpen(false)}>
              {t("btn.signIn")}
            </Link>
          </nav>
          <div className="mobile-sheet-actions">
            <a
              href={DEMO_URL}
              target="_blank"
              rel="noreferrer"
              className="btn btn-primary mobile-sheet-btn"
            >
              {t("btn.bookDemo")} →
            </a>
          </div>
        </div>
      )}
    </>
  );
}

export function MarketingFooter() {
  return <MarketingFooterInner />;
}

function MarketingFooterInner() {
  const { t } = useI18n();
  return (
    <footer className="shell footer">
      <div>
        <div className="brand" style={{ marginBottom: 12 }}>
          <span className="brand-mark"><Flame /></span>
          <span>Workflow Auth</span>
        </div>
        <p className="footer-tag">{t("footer.tag")}</p>
      </div>
      <div className="footer-col">
        <h5>{t("footer.product")}</h5>
        <Link href="/#features">{t("nav.features")}</Link>
        <Link href="/#industries">{t("nav.industries")}</Link>
        <Link href="/#apps">Mobile apps</Link>
        <Link href="/login">{t("btn.signIn")}</Link>
      </div>
      <div className="footer-col">
        <h5>{t("footer.resources")}</h5>
        <Link href="/faq">{t("footer.faq")}</Link>
        <Link href="/docs">{t("nav.docs")}</Link>
        <Link href="/contact">{t("nav.contact")}</Link>
        <a href={DEMO_URL} target="_blank" rel="noreferrer">{t("btn.bookDemo")}</a>
      </div>
      <div className="footer-col">
        <h5>{t("footer.legal")}</h5>
        <Link href="/privacy">{t("footer.privacy")}</Link>
        <Link href="/terms">{t("footer.terms")}</Link>
      </div>
      <div className="footer-bottom">
        <span>© {new Date().getFullYear()} Workflow Auth. {t("footer.copyright")}</span>
      </div>
    </footer>
  );
}

export function Flame() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M8.5 14.5A2.5 2.5 0 0 0 11 17c1.5 0 2.5-.5 3-1.5 1-1.6.6-3.4-1-5-1.6-1.6-2-3.4-1-5C12.5 4 12 3 11 2.5 9.5 2 8 2.5 7 4 5.5 6 5 9 6.5 11c.5 1 .5 2.5-.5 3.5z" />
    </svg>
  );
}

