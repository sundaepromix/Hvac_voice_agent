import type { Metadata } from "next";
import Link from "next/link";

import AnnaDemoLauncher from "./AnnaDemoLauncher";
import ChatWidgetLazy from "./ChatWidgetLazy";
import HearAnnaButton from "./HearAnnaButton";
import HeroBackdrop from "./HeroBackdrop";
import LiveTicker from "./LiveTicker";
import { MarketingTopbar } from "./MarketingShell";
import MissedCallStory from "./MissedCallStory";
import MobileAppsBand from "./MobileAppsBand";
import MockDashboard from "./MockDashboard";
import FeatureExplorer from "./FeatureExplorer";
import StatsBand from "./StatsBand";
import { getT } from "./lib/i18n-server";

const SITE_URL = "https://workflowauth.com";
const DEMO_URL = process.env.NEXT_PUBLIC_BOOKING_URL || "/contact";

export const metadata: Metadata = {
  title: "Workflow Auth — The 24/7 AI front desk for home-service teams",
  description:
    "Mary answers, qualifies, and books — so your crew sleeps and your calendar fills itself. Open-source AI receptionist for HVAC, plumbing, roofing, solar, and more.",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    title: "Workflow Auth — The 24/7 AI front desk for home-service teams",
    description:
      "Mary answers, qualifies, and books — so your crew sleeps and your calendar fills itself.",
    url: SITE_URL,
  },
};

const SOFTWARE_JSONLD = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "Workflow Auth",
  applicationCategory: "BusinessApplication",
  applicationSubCategory: "AI Receptionist",
  operatingSystem: "Web, Linux, Docker",
  description:
    "Open-source 24/7 AI front desk for home-service teams — phone, SMS, WhatsApp, email, chat. Mary qualifies leads and books appointments automatically.",
  url: SITE_URL,
  license: "https://www.gnu.org/licenses/agpl-3.0.html",
  isAccessibleForFree: true,
  offers: {
    "@type": "Offer",
    price: "0",
    priceCurrency: "USD",
    description: "Self-host under AGPL-3.0. Done-for-you setup available.",
  },
  author: {
    "@type": "Person",
    name: "the Workflow Auth team",
    url: "https://workflowauth.com",
  },
  publisher: {
    "@type": "Organization",
    name: "Workflow Auth",
  },
  aggregateRating: undefined,
  featureList: [
    "AI phone receptionist (Vapi + Twilio)",
    "AI chat assistant (web, SMS, WhatsApp)",
    "Unified support inbox (WhatsApp / SMS / email / web chat tickets)",
    "CRM integration (HubSpot, Pipedrive, Salesforce, ServiceTitan)",
    "Configurable per-trade pricing rules",
    "Live analytics dashboards",
  ],
};

export default async function HomePage() {
  const { t } = await getT();
  const INDUSTRIES = [
    { name: t("industries.i1.name"), sketch: <SkPipe />,       body: t("industries.i1.body"), tint: "water" },
    { name: t("industries.i2.name"), sketch: <SkWindow />,     body: t("industries.i2.body"), tint: "glass" },
    { name: t("industries.i3.name"), sketch: <SkSolar />,      body: t("industries.i3.body"), tint: "sun" },
    { name: t("industries.i4.name"), sketch: <SkInsulation />, body: t("industries.i4.body"), tint: "earth" },
    { name: t("industries.i5.name"), sketch: <SkGarage />,     body: t("industries.i5.body"), tint: "slate" },
    { name: t("industries.i6.name"), sketch: <SkBolt />,       body: t("industries.i6.body"), tint: "spark" },
    { name: t("industries.i7.name"), sketch: <SkLeaf />,       body: t("industries.i7.body"), tint: "leaf" },
    { name: t("industries.i8.name"), sketch: <SkSpray />,      body: t("industries.i8.body"), tint: "foam" },
    { name: t("industries.i9.name"), sketch: <SkBug />,        body: t("industries.i9.body"), tint: "moss" },
  ];

  return (
    <div translate="no" className="notranslate">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(SOFTWARE_JSONLD) }}
      />
      <MarketingTopbar showBuiltBy />

      <main>
        {/* HERO */}
        <section className="shell hero hero-illustrated">
          <HeroBackdrop />
          <span className="hero-platform-pill">
            <span className="hero-platform-dot" aria-hidden />
            {t("hero.platformPill")}
          </span>
          <h1 className="hero-title">
            {t("hero.title1")}<br />
            <span className="hero-title-em">{t("hero.title2")}</span>
          </h1>
          <p className="hero-sub">{t("hero.sub")}</p>
          <div className="hero-actions">
            <AnnaDemoLauncher />
            <a
              href={DEMO_URL}
              target="_blank"
              rel="noreferrer"
              className="hero-secondary-link"
            >
              {t("hero.secondary")} <span aria-hidden>→</span>
            </a>
          </div>

          <HearAnnaButton />

          <p className="hero-trades">
            <span className="hero-trades-label">{t("hero.tradesPrefix")}</span>
            <span className="hero-trades-list">{t("hero.tradesList")}</span>
          </p>

          <LiveTicker />
        </section>

        <section className="shell mock-dashboard-section">
          <MockDashboard />
        </section>

        <div className="ember-line" aria-hidden />

        <MissedCallStory />

        <div className="ember-line" aria-hidden />

        <section className="shell section-tight" id="features">
          <div className="section-head">
            <span className="section-flourish">{t("features.eyebrow")}</span>
            <h2 className="section-title">{t("features.title")}</h2>
            <p className="section-sub">{t("features.sub")}</p>
          </div>
          <FeatureExplorer />
        </section>

        <div className="ember-line" aria-hidden />

        <section className="shell section-tight" id="industries">
          <div className="section-head">
            <span className="section-flourish">{t("industries.eyebrow")}</span>
            <h2 className="section-title">{t("industries.title")}</h2>
            <p className="section-sub">{t("industries.sub")}</p>
          </div>
          <div className="industries-grid industries-grid-wide">
            {INDUSTRIES.slice(0, 3).map((it) => (
              <div className={`industry-card tint-${it.tint}`} key={it.name}>
                <span className="industry-sketch" aria-hidden>{it.sketch}</span>
                <h3>{it.name}</h3>
                <p>{it.body}</p>
              </div>
            ))}
          </div>
          <div className="industries-tagrow">
            <span className="industries-tagrow-label">Same engine for</span>
            {INDUSTRIES.slice(3).map((it) => (
              <span key={it.name} className="industries-tag">{it.name}</span>
            ))}
          </div>
          <p className="industries-note">
            {t("industries.note")}
            <a href={DEMO_URL} target="_blank" rel="noreferrer">{t("btn.tellUs")}</a>.
          </p>
        </section>

        <MobileAppsBand />

        <div className="ember-line" aria-hidden />

        <StatsBand />

        <section className="shell section-tight">
          <div className="config-band">
            <div className="config-band-text">
              <p className="section-eyebrow">{t("config.eyebrow")}</p>
              <h2 className="config-band-title">{t("config.title")}</h2>
              <p className="config-band-body">{t("config.body")}</p>
            </div>
            <ul className="config-knobs">
              <li><span>{t("config.k1.l")}</span><strong>{t("config.k1.v")}</strong></li>
              <li><span>{t("config.k2.l")}</span><strong>{t("config.k2.v")}</strong></li>
              <li><span>{t("config.k3.l")}</span><strong>{t("config.k3.v")}</strong></li>
              <li><span>{t("config.k4.l")}</span><strong>{t("config.k4.v")}</strong></li>
              <li><span>{t("config.k5.l")}</span><strong>{t("config.k5.v")}</strong></li>
              <li><span>{t("config.k6.l")}</span><strong>{t("config.k6.v")}</strong></li>
            </ul>
          </div>
        </section>

        <div className="ember-line" aria-hidden />

        <section className="shell section-tight">
          <div className="final-cta">
            <span className="final-cta-mark"><Flame /></span>
            <h2 className="final-cta-title">{t("finalCta.title")}</h2>
            <p className="final-cta-sub">{t("finalCta.sub")}</p>
            <div className="final-cta-actions">
              <AnnaDemoLauncher variant="onDark" />
              <a href={DEMO_URL} target="_blank" rel="noreferrer" className="btn btn-onDark-ghost">
                {t("btn.bookDemo")}
              </a>
            </div>
          </div>
        </section>

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
            <a href="#features">{t("nav.features")}</a>
            <a href="#industries">{t("nav.industries")}</a>
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
            <span>© {new Date().getFullYear()} Workflow Auth · {t("footer.copyright")}</span>
          </div>
        </footer>
      </main>

      <ChatWidgetLazy />
    </div>
  );
}

function Flame() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M8.5 14.5A2.5 2.5 0 0 0 11 17c1.5 0 2.5-.5 3-1.5 1-1.6.6-3.4-1-5-1.6-1.6-2-3.4-1-5C12.5 4 12 3 11 2.5 9.5 2 8 2.5 7 4 5.5 6 5 9 6.5 11c.5 1 .5 2.5-.5 3.5z" />
    </svg>
  );
}

const sketchProps = {
  viewBox: "0 0 64 64",
  fill: "none" as const,
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

function SkPipe() {
  return (
    <svg {...sketchProps}>
      <path d="M6 28h22a8 8 0 0 1 8 8v18" />
      <rect x="4" y="24" width="6" height="8" rx="1" />
      <rect x="32" y="52" width="10" height="6" rx="1" />
      <circle cx="36" cy="36" r="6" />
      <path d="M36 28v-6M30 36h-4M46 36h-4" />
    </svg>
  );
}
function SkWindow() {
  return (
    <svg {...sketchProps}>
      <rect x="10" y="8" width="44" height="48" rx="2" />
      <path d="M10 32h44M32 8v48" />
      <path d="M14 12h36M14 36h36" strokeOpacity="0.4" />
    </svg>
  );
}
function SkSolar() {
  return (
    <svg {...sketchProps}>
      <path d="M6 50 L24 14 L52 14 L34 50 Z" />
      <path d="M16 32 L42 32M22 22 L38 50M30 14 L24 50" />
      <circle cx="46" cy="10" r="4" />
      <path d="M46 4v3M46 13v3M40 10h3M52 10h3M42 6l2 2M48 14l2 2" />
    </svg>
  );
}
function SkInsulation() {
  return (
    <svg {...sketchProps}>
      <path d="M6 22 L32 6 L58 22 L58 58 L6 58 Z" />
      <path d="M14 30c4 0 4 4 8 4s4-4 8-4 4 4 8 4 4-4 8-4" />
      <path d="M14 42c4 0 4 4 8 4s4-4 8-4 4 4 8 4 4-4 8-4" />
      <path d="M14 54h36" />
    </svg>
  );
}
function SkGarage() {
  return (
    <svg {...sketchProps}>
      <path d="M6 24 L32 8 L58 24 L58 58 L6 58 Z" />
      <rect x="14" y="32" width="36" height="22" />
      <path d="M14 40h36M14 47h36M22 32v22M32 32v22M42 32v22" strokeOpacity="0.6" />
    </svg>
  );
}
function SkBolt() {
  return (
    <svg {...sketchProps}>
      <path d="M30 6 L14 36 L26 36 L20 58 L46 28 L34 28 L40 6 Z" />
    </svg>
  );
}
function SkLeaf() {
  return (
    <svg {...sketchProps}>
      <path d="M10 54c0-22 18-40 44-44 0 26-18 44-44 44z" />
      <path d="M14 50 L48 16" />
      <path d="M22 42q4-2 8-2M28 36q4-2 8-2M34 30q4-2 8-2" strokeOpacity="0.6" />
    </svg>
  );
}
function SkSpray() {
  return (
    <svg {...sketchProps}>
      <rect x="20" y="16" width="20" height="40" rx="2" />
      <rect x="22" y="6" width="16" height="10" rx="1" />
      <path d="M40 18 L52 14 L52 26 L40 22" />
      <path d="M48 16 L56 14M48 18 L56 18M48 20 L56 22" strokeOpacity="0.5" />
      <path d="M22 36h16" />
    </svg>
  );
}
function SkBug() {
  return (
    <svg {...sketchProps}>
      <ellipse cx="32" cy="36" rx="14" ry="18" />
      <circle cx="32" cy="20" r="6" />
      <path d="M26 16 L20 8M38 16 L44 8" />
      <path d="M18 30 L8 26M46 30 L56 26M18 40 L8 40M46 40 L56 40M18 50 L10 56M46 50 L54 56" />
      <path d="M32 22v32M26 30q6 4 12 0M26 42q6 4 12 0" strokeOpacity="0.5" />
    </svg>
  );
}
