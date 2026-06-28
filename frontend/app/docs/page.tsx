import { getT } from "../lib/i18n-server";
import { MarketingFooter, MarketingTopbar } from "../MarketingShell";
import DemoCallLauncher from "../DemoCallLauncher";
import { BOOKING_URL } from "../lib/site";

export const metadata = {
  title: "How it works · WorkflowAuth",
  description:
    "How WorkflowAuth deploys a done-for-you AI front desk for home-service pros — HVAC, plumbing, solar, roofing, electrical. What Mary does, how we set you up, and what's included.",
  alternates: { canonical: "/docs" },
  openGraph: {
    title: "WorkflowAuth · How it works",
    description:
      "A done-for-you 24/7 AI front desk for home-service businesses. What Mary does, how we deploy it, and what's included.",
    url: "/docs",
  },
};

const HANDLES = [
  {
    title: "Answers every call",
    body: "Mary picks up inbound calls in two rings, day or night, in a voice you choose. No caller ever hits voicemail again.",
  },
  {
    title: "Qualifies & books the job",
    body: "She asks your intake questions, scores the lead, and books the appointment straight into your calendar with an SMS confirmation.",
  },
  {
    title: "Calls leads back",
    body: "New web or missed-call lead? Mary calls or texts back within seconds — speed-to-lead that wins the job before a competitor answers.",
  },
  {
    title: "Follows up & reactivates",
    body: "Scheduled follow-ups, reminder calls that cut no-shows, and reactivation of quotes that went quiet — all automatic.",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Free revenue audit",
    body: "We map where calls and leads are leaking today — missed calls, slow callbacks, dropped follow-ups — and what it's costing you each month.",
  },
  {
    n: "02",
    title: "We build & deploy Mary",
    body: "Your script, your voice, your hours, your trades, and your CRM. We wire up inbound answering and outbound callbacks, then test it end to end on real calls.",
  },
  {
    n: "03",
    title: "We run it for you",
    body: "Mary goes live on your number. We monitor, tune the script, and keep it humming — you just watch the booked jobs land. Done-for-you, fully managed.",
  },
];

const INCLUDED = [
  "24/7 inbound call answering in a voice you pick",
  "Outbound speed-to-lead, follow-ups, reactivation & reminder calls",
  "Lead capture + scoring tuned to your trade",
  "SMS / WhatsApp confirmations and follow-ups",
  "Warm transfer to your team on the conditions you set",
  "Post-call summaries pushed to your CRM and inbox",
  "Ongoing monitoring, tuning, and support",
];

const INTEGRATIONS = [
  { tag: "Voice", body: "Retell or Vapi for the phone line, with Twilio for SMS and WhatsApp." },
  { tag: "CRMs", body: "HubSpot, Pipedrive, Salesforce, Zoho — leads and call summaries sync in real time." },
  { tag: "Automation", body: "Anything else connects through n8n or a Python integration against our REST API." },
  { tag: "Calendar", body: "Bookings drop straight into Google Calendar or your scheduling tool." },
];

export default async function HowItWorksPage() {
  const { t } = await getT();

  return (
    <>
      <MarketingTopbar />

      <main>
        <section className="shell hero hero-tight">
          <span className="hero-platform-pill">
            <span className="hero-platform-dot" aria-hidden /> How it works
          </span>
          <h1 className="hero-title">
            A front desk that runs itself.<br />
            <span className="hero-title-em">Done for you, end to end.</span>
          </h1>
          <p className="hero-sub">
            WorkflowAuth deploys Mary — a 24/7 AI receptionist built for home-service pros (HVAC,
            plumbing, solar, roofing, and electrical). Here's exactly what she does, how we set her
            up, and what you get.
          </p>
          <div className="hero-actions">
            <DemoCallLauncher />
            <a href={BOOKING_URL} target="_blank" rel="noreferrer" className="hero-secondary-link">
              {t("contact.book.cta")} <span aria-hidden>→</span>
            </a>
          </div>
        </section>

        <div className="ember-line" aria-hidden />

        <section className="shell section-tight">
          <div className="section-head">
            <span className="section-flourish">What Mary does</span>
            <h2 className="section-title">One receptionist. Every call task.</h2>
            <p className="section-sub">
              From first ring to follow-up — across inbound and outbound calls.
            </p>
          </div>
          <div className="deploy-grid">
            {HANDLES.map((h) => (
              <div className="deploy-card" key={h.title}>
                <h3>{h.title}</h3>
                <p>{h.body}</p>
              </div>
            ))}
          </div>
        </section>

        <div className="ember-line" aria-hidden />

        <section className="shell section-tight">
          <div className="section-head">
            <span className="section-flourish">The process</span>
            <h2 className="section-title">From audit to live in about three days.</h2>
            <p className="section-sub">You stay on the tools. We handle the build, the deploy, and the calls.</p>
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

        <section className="shell section-tight">
          <div className="section-head">
            <span className="section-flourish">What's included</span>
            <h2 className="section-title">Everything, managed for you.</h2>
            <p className="section-sub">One simple monthly engagement — no software to run, nothing to host.</p>
          </div>
          <ul className="pricing-features included-list">
            {INCLUDED.map((i) => (
              <li key={i}>{i}</li>
            ))}
          </ul>
        </section>

        <div className="ember-line" aria-hidden />

        <section className="shell section-tight">
          <div className="section-head">
            <span className="section-flourish">Integrations</span>
            <h2 className="section-title">Plugs into the tools you already use.</h2>
          </div>
          <div className="deploy-grid">
            {INTEGRATIONS.map((it) => (
              <div className="deploy-card" key={it.tag}>
                <h3>{it.tag}</h3>
                <p>{it.body}</p>
              </div>
            ))}
          </div>
        </section>

        <div className="ember-line" aria-hidden />

        <section className="shell section-tight">
          <div className="final-cta">
            <h2 className="final-cta-title">{t("finalCta2.title")}</h2>
            <p className="final-cta-sub">{t("finalCta2.sub")}</p>
            <div className="final-cta-actions">
              <DemoCallLauncher variant="onDark" />
              <a href={BOOKING_URL} target="_blank" rel="noreferrer" className="btn btn-onDark-ghost">
                {t("btn.bookDemo")}
              </a>
            </div>
          </div>
        </section>

        <MarketingFooter />
      </main>
    </>
  );
}
