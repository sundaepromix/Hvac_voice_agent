"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { useI18n } from "./lib/i18n";

type Action =
  | { kind: "deal-won"; amount: number }
  | { kind: "quote-generated"; amount: number }
  | { kind: "appointment-booked" }
  | { kind: "subsidy-checked" }
  | { kind: "qualifying" };

type Row = {
  id: number;
  contact: string;
  contactSub: string;
  assistant: string;
  initial: string;
  message: string;
  action: Action;
  ageSec: number;
};

// Channel keys — resolved through i18n at render time.
const CHANNEL_KEYS = [
  "mock.channel.phone",
  "mock.channel.sms",
  "mock.channel.whatsapp",
  "mock.channel.chat",
  "mock.channel.email",
];
// Business-style demo names — feels real but is obviously not personal PII.
const NAMES: Array<[string, string]> = [
  ["Bay Area Roofing", "+1 (000) 123-4567"],
  ["Acme HVAC Co.", "demo-002@example.test"],
  ["North Pine Windows", "+1 (000) 234-5678"],
  ["Stonebridge Solar", "demo-004@example.test"],
  ["Riverbend Plumbing", "+1 (000) 345-6789"],
  ["Cypress Garage Doors", "demo-006@example.test"],
  ["Westwood Electrical", "+1 (000) 456-7890"],
  ["Elm Street Landscaping", "demo-008@example.test"],
];
const MESSAGES: Array<{ key: string; action: Action }> = [
  { key: "mock.msg1", action: { kind: "deal-won", amount: 12300 } },
  { key: "mock.msg2", action: { kind: "quote-generated", amount: 8500 } },
  { key: "mock.msg3", action: { kind: "appointment-booked" } },
  { key: "mock.msg4", action: { kind: "subsidy-checked" } },
  { key: "mock.msg5", action: { kind: "quote-generated", amount: 1200 } },
  { key: "mock.msg6", action: { kind: "qualifying" } },
  { key: "mock.msg7", action: { kind: "deal-won", amount: 9450 } },
  { key: "mock.msg8", action: { kind: "appointment-booked" } },
];

function pickRowAt(id: number, idx: number, t: (k: string) => string): Row {
  const [contact, contactSub] = NAMES[idx % NAMES.length];
  const channelKey = CHANNEL_KEYS[idx % CHANNEL_KEYS.length];
  const m = MESSAGES[idx % MESSAGES.length];
  return {
    id,
    contact,
    contactSub,
    assistant: `Mary · ${t(channelKey)}`,
    initial: "V",
    message: t(m.key),
    action: m.action,
    ageSec: 0,
  };
}

function pickRandomRow(id: number, t: (k: string) => string): Row {
  const [contact, contactSub] = NAMES[Math.floor(Math.random() * NAMES.length)];
  const channelKey = CHANNEL_KEYS[Math.floor(Math.random() * CHANNEL_KEYS.length)];
  const m = MESSAGES[Math.floor(Math.random() * MESSAGES.length)];
  return {
    id,
    contact,
    contactSub,
    assistant: `Mary · ${t(channelKey)}`,
    initial: "V",
    message: t(m.key),
    action: m.action,
    ageSec: 0,
  };
}

export default function MockDashboard() {
  const { t } = useI18n();

  // Deterministic seed derived from t() — re-renders when language changes.
  const initialRows = useMemo<Row[]>(
    () =>
      Array.from({ length: 6 }).map((_, i) => ({
        ...pickRowAt(i, i, t),
        ageSec: i * 60 + 10,
      })),
    [t],
  );

  const [rows, setRows] = useState<Row[]>(initialRows);
  const idRef = useRef<number>(initialRows.length);
  const [leads, setLeads] = useState(0);
  const [quotes, setQuotes] = useState(0);
  const [bookings, setBookings] = useState(0);

  // When language flips, reset rows so labels translate immediately.
  useEffect(() => {
    setRows(initialRows);
    idRef.current = initialRows.length;
  }, [initialRows]);

  useEffect(() => {
    const start = performance.now();
    const dur = 1400;
    const targets = { leads: 273, quotes: 99.8, bookings: 78 };
    let raf = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / dur);
      const e = 1 - Math.pow(1 - t, 3);
      setLeads(Math.round(targets.leads * e));
      setQuotes(Math.round(targets.quotes * 10 * e) / 10);
      setBookings(Math.round(targets.bookings * e));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setRows((prev) => {
        const aged = prev.map((r) => ({ ...r, ageSec: r.ageSec + 4 }));
        const next = pickRandomRow(idRef.current++, t);
        return [next, ...aged].slice(0, 6);
      });
    }, 4500);
    return () => clearInterval(interval);
  }, [t]);

  return (
    <div className="mock-dashboard">
      <div className="mock-shadow" />
      <div className="mock-frame">
        <aside className="mock-rail">
          <span className="mock-rail-mark">
            <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <path d="M8.5 14.5A2.5 2.5 0 0 0 11 17c1.5 0 2.5-.5 3-1.5 1-1.6.6-3.4-1-5-1.6-1.6-2-3.4-1-5C12.5 4 12 3 11 2.5 9.5 2 8 2.5 7 4 5.5 6 5 9 6.5 11c.5 1 .5 2.5-.5 3.5z" />
            </svg>
          </span>
          <RailIcon active>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="9" /><rect x="14" y="3" width="7" height="5" /><rect x="14" y="12" width="7" height="9" /><rect x="3" y="16" width="7" height="5" /></svg>
          </RailIcon>
          <RailIcon>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-6l-2 3h-4l-2-3H2" /><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" /></svg>
          </RailIcon>
          <RailIcon>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" /></svg>
          </RailIcon>
          <RailIcon>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
          </RailIcon>
          <span style={{ flex: 1 }} />
          <RailIcon>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg>
          </RailIcon>
        </aside>

        <div className="mock-body">
          <div className="mock-topbar">
            <div className="mock-crumbs">
              <strong>{t("mock.crumb")}</strong>
              <span className="mock-divider">/</span>
              <span>{t("mock.business")}</span>
            </div>
            <div className="mock-search">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></svg>
              <span>{t("mock.search")}</span>
              <kbd className="mock-kbd">⌘K</kbd>
            </div>
            <div className="mock-actions">
              <button className="mock-icon-btn" aria-label="Notifications">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" /></svg>
              </button>
              <span className="mock-avatar" aria-label="Owner avatar">RS</span>
            </div>
          </div>

          <div className="mock-kpis">
            <KpiCard label={t("mock.kpi.leads")} value={leads.toLocaleString()} delta={t("mock.kpi.leadsDelta")} />
            <KpiCard label={t("mock.kpi.quotes")} value={`$${quotes.toFixed(1)}k`} delta={t("mock.kpi.quotesDelta")} />
            <KpiCard label={t("mock.kpi.bookings")} value={bookings.toString()} delta={t("mock.kpi.bookingsDelta")} />
          </div>

          <div className="mock-section-head">
            <div className="mock-section-title">
              {t("mock.section.title")}
              <span className="mock-livefeed">
                <span className="mock-pulse" />
                {t("mock.live")}
              </span>
            </div>
            <button className="mock-filter-btn" type="button">
              <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 6h18M6 12h12M10 18h4" /></svg>
              {t("mock.filter")}
            </button>
          </div>

          <div className="mock-table">
            <div className="mock-thead">
              <span>{t("mock.col.contact")}</span>
              <span>{t("mock.col.assistant")}</span>
              <span>{t("mock.col.activity")}</span>
              <span>{t("mock.col.action")}</span>
            </div>
            {rows.map((r) => (
              <div className="mock-row" key={r.id}>
                <div className="mock-contact">
                  <span className="mock-msg-icon" aria-hidden>
                    <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
                  </span>
                  <div>
                    <div className="mock-contact-name">{r.contact}</div>
                    <div className="mock-contact-sub">{r.contactSub}</div>
                  </div>
                </div>
                <div className="mock-assist">
                  <span className="mock-assist-avatar">{r.initial}</span>
                  <span>{r.assistant}</span>
                </div>
                <div className="mock-activity">
                  <div className="mock-activity-text">{r.message}</div>
                  <div className="mock-activity-age">{formatAge(r.ageSec, t)}</div>
                </div>
                <div className="mock-action">
                  <ActionPill action={r.action} t={t} />
                </div>
              </div>
            ))}
          </div>
          <div className="mock-foot">
            {t("mock.foot")} · <a href="/dashboard">{t("mock.openReal")} →</a>
          </div>
        </div>
      </div>
    </div>
  );
}

function RailIcon({ children, active }: { children: React.ReactNode; active?: boolean }) {
  return <span className={`mock-rail-icon ${active ? "active" : ""}`}>{children}</span>;
}

function KpiCard({ label, value, delta }: { label: string; value: string; delta: string }) {
  return (
    <div className="kpi-card">
      <div className="kpi-card-label">{label}</div>
      <div className="kpi-card-value">{value}</div>
      <div className="kpi-card-delta up">
        <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><polyline points="18 15 12 9 6 15" /></svg>
        {delta}
      </div>
    </div>
  );
}

function ActionPill({ action, t }: { action: Action; t: (k: string) => string }) {
  if (action.kind === "deal-won") {
    return <span className="action-pill won"><Dot color="#16a34a" /> {t("pill.dealWon")} · ${action.amount.toLocaleString()}</span>;
  }
  if (action.kind === "quote-generated") {
    return <span className="action-pill quote"><Dot color="#7c3aed" /> {t("pill.quoteSent")} · ${action.amount.toLocaleString()}</span>;
  }
  if (action.kind === "appointment-booked") {
    return <span className="action-pill booked"><Dot color="#2563eb" /> {t("pill.booked")}</span>;
  }
  if (action.kind === "subsidy-checked") {
    return <span className="action-pill subsidy"><Dot color="#d2532b" /> {t("pill.subsidy")}</span>;
  }
  return <span className="action-pill status"><Dot color="#6b7280" /> {t("pill.qualifying")}</span>;
}

function Dot({ color }: { color: string }) {
  return <span className="action-dot" style={{ background: color }} />;
}

function formatAge(sec: number, t: (k: string) => string): string {
  if (sec < 30) return t("mock.justNow");
  if (sec < 60) return t("mock.secAgo").replace("{n}", String(sec));
  const m = Math.floor(sec / 60);
  if (m < 60) return t("mock.minAgo").replace("{n}", String(m));
  const h = Math.floor(m / 60);
  return t("mock.hourAgo").replace("{n}", String(h));
}
