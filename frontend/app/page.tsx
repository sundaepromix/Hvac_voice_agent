import type { Metadata } from "next";
import Link from "next/link";

import DemoCallLauncher from "./DemoCallLauncher";
import ChatWidgetLazy from "./ChatWidgetLazy";
import HearMaryButton from "./HearMaryButton";
import HeroBackdrop from "./HeroBackdrop";
import LiveTicker from "./LiveTicker";
import { MarketingTopbar } from "./MarketingShell";
import StatsBand from "./StatsBand";
import RoiCalculator from "./RoiCalculator";
import FounderCard from "./FounderCard";
import { FAQS } from "./faq/data";
import { getT } from "./lib/i18n-server";
import { BOOKING_URL } from "./lib/site";

const SITE_URL = "https://workflowauth.com";
const DEMO_URL = BOOKING_URL;

export const metadata: Metadata = {
  title: "WorkflowAuth — the AI front desk that never misses a lead",
  description:
    "WorkflowAuth answers every call your team misses, qualifies the lead, books the job, and calls back the ones that slip away. A 24/7 AI front desk for home-service pros — HVAC, plumbing, solar, roofing, and electrical.",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    title: "WorkflowAuth — AI front desk for inbound + outbound calls",
    description:
      "Stop losing revenue to missed calls. Answer every call, qualify the lead, book the job — around the clock.",
    url: SITE_URL,
  },
};

const SOFTWARE_JSONLD = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "WorkflowAuth",
  applicationCategory: "BusinessApplication",
  applicationSubCategory: "AI Voice Agent",
  operatingSystem: "Web",
  description:
    "Done-for-you 24/7 AI front desk — answers inbound calls and places outbound calls for speed-to-lead, follow-ups, reactivation, and appointment reminders for home-service pros: HVAC, plumbing, solar, roofing, and electrical.",
  url: SITE_URL,
  offers: {
    "@type": "Offer",
    priceCurrency: "USD",
    description: "Fully managed setup and operation — we build, deploy, and run it for you.",
  },
  author: {
    "@type": "Person",
    name: "Promise Sunday",
    url: "https://workflowauth.com",
  },
  publisher: {
    "@type": "Organization",
    name: "WorkflowAuth",
  },
  aggregateRating: undefined,
  featureList: [
    "AI phone receptionist for inbound calls (Retell / Vapi + Twilio)",
    "Outbound calling — speed-to-lead, follow-ups, reactivation, reminders",
    "AI chat assistant (web, SMS, WhatsApp)",
    "Configurable lead capture + lead scoring",
    "Human transfer rules + post-call digest",
    "CRM + workflow integration (HubSpot, Pipedrive, Salesforce, n8n, Python)",
  ],
};

export default async function HomePage() {
  const { t } = await getT();

  const INDUSTRIES = [
    { name: t("ind.hvac.name"),       body: t("ind.hvac.body"),       sketch: <SkHvac />,  tint: "water" },
    { name: t("ind.plumbing.name"),   body: t("ind.plumbing.body"),   sketch: <SkPipe />,  tint: "foam" },
    { name: t("ind.solar.name"),      body: t("ind.solar.body"),      sketch: <SkSolar />, tint: "sun" },
    { name: t("ind.roofing.name"),    body: t("ind.roofing.body"),    sketch: <SkRoof />,  tint: "earth" },
    { name: t("ind.electrical.name"), body: t("ind.electrical.body"), sketch: <SkBolt />,  tint: "spark" },
  ];

  const DEPLOY = [
    { icon: <DPhone />,  title: t("deploy.d1.title"), body: t("deploy.d1.body") },
    { icon: <DBolt />,   title: t("deploy.d2.title"), body: t("deploy.d2.body") },
    { icon: <DCal />,    title: t("deploy.d3.title"), body: t("deploy.d3.body") },
    { icon: <DRepeat />, title: t("deploy.d4.title"), body: t("deploy.d4.body") },
  ];

  const STEPS = [
    { n: t("how.s1.n"), title: t("how.s1.title"), body: t("how.s1.body") },
    { n: t("how.s2.n"), title: t("how.s2.title"), body: t("how.s2.body") },
    { n: t("how.s3.n"), title: t("how.s3.title"), body: t("how.s3.body") },
  ];

  const WHY_COLS = [t("why.col.us"), t("why.col.vm"), t("why.col.recept"), t("why.col.bot")];
  const WHY_ROWS: { l: string; cells: string[] }[] = [
    { l: t("why.r1.l"), cells: ["yes", "no", "no", "no"] },
    { l: t("why.r2.l"), cells: ["yes", "no", "yes", "no"] },
    { l: t("why.r3.l"), cells: ["yes", "no", "yes", "no"] },
    { l: t("why.r4.l"), cells: ["yes", "no", "no", "no"] },
    { l: t("why.r6.l"), cells: [t("why.r6.us"), t("why.r6.vm"), t("why.r6.recept"), t("why.r6.bot")] },
    { l: t("why.r7.l"), cells: ["yes", "yes", "no", "yes"] },
  ];

  const PROBLEM_WITHOUT = [
    t("problem.without.1"), t("problem.without.2"), t("problem.without.3"), t("problem.without.4"),
  ];
  const PROBLEM_WITH = [
    t("problem.with.1"), t("problem.with.2"), t("problem.with.3"), t("problem.with.4"),
  ];

  const LANDING_FAQS = FAQS.slice(0, 6);

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
            {t("hero2.pill")}
          </span>
          <h1 className="hero-title">
            {t("hero2.title1")}<br />
            <span className="hero-title-em">{t("hero2.title2")}</span>
          </h1>
          <p className="hero-sub">{t("hero2.sub")}</p>
          <div className="hero-actions">
            <DemoCallLauncher />
            <a href="#cost" className="hero-secondary-link">
              {t("hero2.secondary")} <span aria-hidden>→</span>
            </a>
          </div>

          <HearMaryButton />

          <p className="hero-trades">
            <span className="hero-trades-label">{t("hero2.tradesPrefix")}</span>
            <span className="hero-trades-list">{t("hero2.tradesList")}</span>
          </p>

          <LiveTicker />
        </section>

        {/* PROBLEM */}
        <section className="shell section-tight" id="problem">
          <div className="section-head">
            <span className="section-flourish">{t("problem.eyebrow")}</span>
            <h2 className="section-title">{t("problem.title")}</h2>
            <p className="section-sub">{t("problem.sub")}</p>
          </div>
          <div className="problem-stats">
            <div className="problem-stat">
              <div className="problem-stat-num">{t("problem.s1.num")}</div>
              <p>{t("problem.s1.label")}</p>
            </div>
            <div className="problem-stat">
              <div className="problem-stat-num">{t("problem.s2.num")}</div>
              <p>{t("problem.s2.label")}</p>
            </div>
            <div className="problem-stat">
              <div className="problem-stat-num">{t("problem.s3.num")}</div>
              <p>{t("problem.s3.label")}</p>
            </div>
          </div>
          <div className="compare-cols">
            <div className="compare-col compare-col-bad">
              <h3>{t("problem.without.title")}</h3>
              <ul>
                {PROBLEM_WITHOUT.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
            <div className="compare-col compare-col-good">
              <h3>{t("problem.with.title")}</h3>
              <ul>
                {PROBLEM_WITH.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        <div className="ember-line" aria-hidden />

        {/* REVENUE LOSS CALCULATOR */}
        <section className="shell section-tight" id="cost">
          <div className="section-head">
            <span className="section-flourish">{t("cost.eyebrow")}</span>
            <h2 className="section-title">{t("cost.title")}</h2>
            <p className="section-sub">{t("cost.sub")}</p>
          </div>
          <RoiCalculator
            callsLabel={t("roi.callsLabel")}
            valueLabel={t("roi.valueLabel")}
            resultLabel={t("roi.resultLabel")}
            foot={t("roi.foot")}
          />
        </section>

        <div className="ember-line" aria-hidden />

        {/* HOW IT WORKS */}
        <section className="shell section-tight" id="how">
          <div className="section-head">
            <span className="section-flourish">{t("how.eyebrow")}</span>
            <h2 className="section-title">{t("how.title")}</h2>
            <p className="section-sub">{t("how.sub")}</p>
          </div>
          <div className="steps-grid">
            {STEPS.map((s) => (
              <div className="step-card" key={s.n}>
                <span className="step-num" aria-hidden>{s.n}</span>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
              </div>
            ))}
          </div>
        </section>

        <div className="ember-line" aria-hidden />

        {/* WHAT WE DEPLOY */}
        <section className="shell section-tight" id="deploy">
          <div className="section-head">
            <span className="section-flourish">{t("deploy.eyebrow")}</span>
            <h2 className="section-title">{t("deploy.title")}</h2>
            <p className="section-sub">{t("deploy.sub")}</p>
          </div>
          <div className="deploy-grid">
            {DEPLOY.map((d) => (
              <div className="deploy-card" key={d.title}>
                <span className="deploy-icon" aria-hidden>{d.icon}</span>
                <h3>{d.title}</h3>
                <p>{d.body}</p>
              </div>
            ))}
          </div>
        </section>

        <div className="ember-line" aria-hidden />

        {/* INDUSTRIES */}
        <section className="shell section-tight" id="industries">
          <div className="section-head">
            <span className="section-flourish">{t("ind.eyebrow")}</span>
            <h2 className="section-title">{t("ind.title")}</h2>
            <p className="section-sub">{t("ind.sub")}</p>
          </div>
          <div className="industries-grid industries-grid-quint">
            {INDUSTRIES.map((it) => (
              <div className={`industry-card tint-${it.tint}`} key={it.name}>
                <span className="industry-sketch" aria-hidden>{it.sketch}</span>
                <h3>{it.name}</h3>
                <p>{it.body}</p>
              </div>
            ))}
          </div>
          <div className="industries-tagrow">
            <span className="industries-tagrow-label">{t("ind.also.label")}</span>
            <span className="industries-tag">{t("ind.also.1")}</span>
            <span className="industries-tag">{t("ind.also.2")}</span>
            <span className="industries-tag">{t("ind.also.3")}</span>
          </div>
          <p className="industries-note">
            {t("ind.note")}
            <a href={DEMO_URL} target="_blank" rel="noreferrer">{t("btn.tellUs")}</a>.
          </p>
        </section>

        {/* RESULTS */}
        <StatsBand />

        <div className="ember-line" aria-hidden />

        {/* WHY US */}
        <section className="shell section-tight" id="why">
          <div className="section-head">
            <span className="section-flourish">{t("why.eyebrow")}</span>
            <h2 className="section-title">{t("why.title")}</h2>
            <p className="section-sub">{t("why.sub")}</p>
          </div>
          <div className="compare-table-wrap">
            <table className="compare-table">
              <thead>
                <tr>
                  <th scope="col" className="ct-feature" />
                  {WHY_COLS.map((c, i) => (
                    <th scope="col" key={c} className={i === 0 ? "ct-us" : undefined}>
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {WHY_ROWS.map((row) => (
                  <tr key={row.l}>
                    <th scope="row" className="ct-feature">{row.l}</th>
                    {row.cells.map((cell, i) => (
                      <td key={i} className={i === 0 ? "ct-us" : undefined}>
                        <WhyCell value={cell} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <div className="ember-line" aria-hidden />

        {/* ABOUT / FOUNDER */}
        <section className="shell section-tight" id="founder">
          <FounderCard
            variant="about"
            eyebrow={t("about.eyebrow")}
            title={t("about.title")}
            name={t("about.name")}
            role={t("about.role")}
            note={t("about.body")}
          />
        </section>

        <div className="ember-line" aria-hidden />

        {/* FAQ */}
        <section className="shell section-tight" id="faq">
          <div className="section-head">
            <span className="section-flourish">{t("faq2.eyebrow")}</span>
            <h2 className="section-title">{t("faq2.title")}</h2>
            <p className="section-sub">{t("faq2.sub")}</p>
          </div>
          <div className="faq-list">
            {LANDING_FAQS.map((item) => (
              <details className="faq-item" key={item.q}>
                <summary>
                  <span>{item.q}</span>
                  <span className="faq-chevron" aria-hidden>+</span>
                </summary>
                <p>{item.aText}</p>
              </details>
            ))}
          </div>
          <p className="faq-more">
            <Link href="/faq">{t("faq2.more")}</Link>
          </p>
        </section>

        <div className="ember-line" aria-hidden />

        {/* FINAL CTA */}
        <section className="shell section-tight">
          <div className="final-cta">
            <span className="final-cta-mark"><Flame /></span>
            <h2 className="final-cta-title">{t("finalCta2.title")}</h2>
            <p className="final-cta-sub">{t("finalCta2.sub")}</p>
            <div className="final-cta-actions">
              <DemoCallLauncher variant="onDark" />
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
              <span>WorkflowAuth</span>
            </div>
            <p className="footer-tag">{t("footer.tag")}</p>
          </div>
          <div className="footer-col">
            <h5>{t("footer.product")}</h5>
            <a href="#deploy">{t("nav.deploy")}</a>
            <a href="#industries">{t("nav.industries")}</a>
            <a href="#why">{t("nav.why")}</a>
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
            <span className="footer-credit">
              <strong>{t("about.name")}</strong> · {t("about.role")}
            </span>
            <span>© {new Date().getFullYear()} WorkflowAuth · {t("footer.copyright")}</span>
          </div>
        </footer>
      </main>

      <ChatWidgetLazy />
    </div>
  );
}

function WhyCell({ value }: { value: string }) {
  if (value === "yes") {
    return (
      <span className="ct-yes" aria-label="Yes">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <path d="M20 6 L9 17 L4 12" />
        </svg>
      </span>
    );
  }
  if (value === "no") {
    return (
      <span className="ct-no" aria-label="No">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <path d="M6 6 L18 18 M18 6 L6 18" />
        </svg>
      </span>
    );
  }
  return <span className="ct-text">{value}</span>;
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

function SkHvac() {
  return (
    <svg {...sketchProps}>
      <rect x="8" y="14" width="48" height="30" rx="3" />
      <path d="M8 24h48M8 34h48" strokeOpacity="0.4" />
      <path d="M16 50v4M48 50v4" />
      <circle cx="20" cy="19" r="1.6" />
      <path d="M30 30c3-3 7 3 10 0" strokeOpacity="0.7" />
    </svg>
  );
}
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
function SkRoof() {
  return (
    <svg {...sketchProps}>
      <path d="M4 30 L32 8 L60 30" />
      <path d="M10 27 L10 54 L54 54 L54 27" />
      <path d="M14 38h12v16h-12zM34 38h16v10h-16z" strokeOpacity="0.6" />
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

const dProps = {
  viewBox: "0 0 24 24",
  fill: "none" as const,
  stroke: "currentColor",
  strokeWidth: 1.7,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

function DPhone() {
  return (
    <svg {...dProps}>
      <path d="M5 4h4l2 5-3 2a12 12 0 0 0 5 5l2-3 5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z" />
    </svg>
  );
}
function DBolt() {
  return (
    <svg {...dProps}>
      <path d="M13 2 L4 14 H11 L10 22 L20 9 H13 Z" />
    </svg>
  );
}
function DCal() {
  return (
    <svg {...dProps}>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 9h18M8 3v4M16 3v4" />
      <path d="M8 14l2.5 2.5L16 11" />
    </svg>
  );
}
function DRepeat() {
  return (
    <svg {...dProps}>
      <path d="M4 9a8 8 0 0 1 13-3l3 3M20 4v5h-5" />
      <path d="M20 15a8 8 0 0 1-13 3l-3-3M4 20v-5h5" />
    </svg>
  );
}
