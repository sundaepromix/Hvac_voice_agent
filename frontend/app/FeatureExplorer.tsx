"use client";

import { useState } from "react";

import PhoneWidget from "./PhoneWidget";
import { useI18n } from "./lib/i18n";

type FeatureKey = "phone" | "chat" | "crm" | "quote" | "kb" | "analytics";

const FEATURES: Array<{
  key: FeatureKey;
  num: string;
  nameKey: string;
  blurbKey: string;
}> = [
  { key: "phone", num: "01", nameKey: "fexp.f1.name", blurbKey: "fexp.f1.body" },
  { key: "chat", num: "02", nameKey: "fexp.f2.name", blurbKey: "fexp.f2.body" },
  { key: "crm", num: "03", nameKey: "fexp.f3.name", blurbKey: "fexp.f3.body" },
  { key: "quote", num: "04", nameKey: "fexp.f4.name", blurbKey: "fexp.f4.body" },
  { key: "kb", num: "05", nameKey: "fexp.f5.name", blurbKey: "fexp.f5.body" },
  { key: "analytics", num: "06", nameKey: "fexp.f6.name", blurbKey: "fexp.f6.body" },
];

export default function FeatureExplorer() {
  const { t } = useI18n();
  const [active, setActive] = useState<FeatureKey>("phone");

  return (
    <div className="fexp">
      <div className="fexp-list">
        {FEATURES.map((f) => (
          <button
            key={f.key}
            type="button"
            onClick={() => setActive(f.key)}
            className={`fexp-row ${active === f.key ? "active" : ""}`}
          >
            <div className="fexp-row-body">
              <div className="fexp-row-name">{t(f.nameKey)}</div>
              <div className="fexp-row-blurb">{t(f.blurbKey)}</div>
            </div>
            <span className="fexp-row-num">{f.num}</span>
          </button>
        ))}
      </div>

      <div className="fexp-stage">
        {active === "phone" && <PhoneWidget />}
        {active === "chat" && <ChatDemo t={t} />}
        {active === "crm" && <CrmDemo t={t} />}
        {active === "quote" && <QuoteDemo t={t} />}
        {active === "kb" && <KbDemo t={t} />}
        {active === "analytics" && <AnalyticsDemo t={t} />}
      </div>
    </div>
  );
}

type T = (k: string) => string;

function ChatDemo({ t }: { t: T }) {
  return (
    <div className="demo-card">
      <div className="demo-card-head">
        <span className="chat-avatar">A</span>
        <div>
          <div className="chat-name">Mary <span className="chat-online" /></div>
          <div className="chat-role">{t("demo.chat.role")}</div>
        </div>
      </div>
      <div className="demo-thread">
        <Bubble role="in">{t("demo.chat.in1")}</Bubble>
        <Bubble role="out">{t("demo.chat.out1")}</Bubble>
        <Bubble role="in">{t("demo.chat.in2")}</Bubble>
        <Bubble role="out">{t("demo.chat.out2")}</Bubble>
      </div>
      <div className="demo-foot">
        <span className="action-pill booked"><span className="action-dot" style={{ background: "#2563eb" }} /> {t("demo.chat.pillBooked")}</span>
        <span className="action-pill quote"><span className="action-dot" style={{ background: "#7c3aed" }} /> {t("demo.chat.pillEta")}</span>
      </div>
    </div>
  );
}

function CrmDemo({ t }: { t: T }) {
  return (
    <div className="demo-card">
      <div className="demo-card-head">
        <span className="demo-icon">🔄</span>
        <div>
          <div className="chat-name">{t("demo.crm.title")}</div>
          <div className="chat-role">{t("demo.crm.role")}</div>
        </div>
      </div>
      <div className="demo-fields">
        <Field label={t("demo.crm.contact")} value={t("demo.crm.contactVal")} />
        <Field label={t("demo.crm.source")} value={t("demo.crm.sourceVal")} />
        <Field label={t("demo.crm.trade")} value={t("demo.crm.tradeVal")} />
        <Field label={t("demo.crm.value")} value={t("demo.crm.valueVal")} />
        <Field label={t("demo.crm.temp")} value={t("demo.crm.tempVal")} />
        <Field label={t("demo.crm.owner")} value={t("demo.crm.ownerVal")} />
      </div>
      <div className="demo-foot">
        <span className="action-pill won"><span className="action-dot" style={{ background: "#16a34a" }} /> {t("demo.crm.pillCreated")}</span>
        <span className="action-pill status"><span className="action-dot" style={{ background: "#6b7280" }} /> {t("demo.crm.pillStage")}</span>
      </div>
    </div>
  );
}

function QuoteDemo({ t }: { t: T }) {
  return (
    <div className="demo-card">
      <div className="demo-card-head">
        <span className="demo-icon">📸</span>
        <div>
          <div className="chat-name">{t("demo.quote.title")}</div>
          <div className="chat-role">{t("demo.quote.role")}</div>
        </div>
      </div>
      <div className="demo-quote">
        <div className="demo-quote-row"><span>{t("demo.quote.row1")}</span><span>$2,900</span></div>
        <div className="demo-quote-row"><span>{t("demo.quote.row2")}</span><span>$300</span></div>
        <div className="demo-quote-row"><span>{t("demo.quote.row3")}</span><span>$150</span></div>
        <div className="demo-quote-row demo-quote-total"><span>{t("demo.quote.totalLabel")}</span><span>$3,618</span></div>
      </div>
      <div className="demo-foot">
        <span className="action-pill quote"><span className="action-dot" style={{ background: "#7c3aed" }} /> {t("demo.quote.pill")}</span>
      </div>
    </div>
  );
}

function KbDemo({ t }: { t: T }) {
  return (
    <div className="demo-card">
      <div className="demo-card-head">
        <span className="demo-icon">📚</span>
        <div>
          <div className="chat-name">{t("demo.kb.title")}</div>
          <div className="chat-role">{t("demo.kb.role")}</div>
        </div>
      </div>
      <div className="demo-thread">
        <Bubble role="in">{t("demo.kb.in1")}</Bubble>
        <Bubble role="out">{t("demo.kb.out1")}</Bubble>
        <Bubble role="in">{t("demo.kb.in2")}</Bubble>
        <Bubble role="out">{t("demo.kb.out2")}</Bubble>
      </div>
      <div className="demo-foot">
        <span className="action-pill subsidy"><span className="action-dot" style={{ background: "#d2532b" }} /> {t("demo.kb.pill")}</span>
      </div>
    </div>
  );
}

function AnalyticsDemo({ t }: { t: T }) {
  return (
    <div className="demo-card">
      <div className="demo-card-head">
        <span className="demo-icon">📊</span>
        <div>
          <div className="chat-name">{t("demo.analytics.title")}</div>
          <div className="chat-role">{t("demo.analytics.role")}</div>
        </div>
      </div>
      <div className="demo-stats">
        <div className="demo-stat"><strong>{t("demo.analytics.s1n")}</strong><span>{t("demo.analytics.s1l")}</span></div>
        <div className="demo-stat"><strong>{t("demo.analytics.s2n")}</strong><span>{t("demo.analytics.s2l")}</span></div>
        <div className="demo-stat"><strong>{t("demo.analytics.s3n")}</strong><span>{t("demo.analytics.s3l")}</span></div>
        <div className="demo-stat"><strong>{t("demo.analytics.s4n")}</strong><span>{t("demo.analytics.s4l")}</span></div>
      </div>
      <div className="demo-foot">
        <span className="action-pill won"><span className="action-dot" style={{ background: "#16a34a" }} /> {t("demo.analytics.pill")}</span>
      </div>
    </div>
  );
}

function Bubble({ role, children }: { role: "in" | "out"; children: React.ReactNode }) {
  return (
    <div className={`workflow-msg ${role}`}>
      {role === "in" && (
        <span className="workflow-avatar">
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 4-7 8-7s8 3 8 7" /></svg>
        </span>
      )}
      <div className="workflow-msg-bubble">{children}</div>
      {role === "out" && <span className="workflow-avatar ai">A</span>}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="demo-field">
      <span className="demo-field-label">{label}</span>
      <span className="demo-field-value">{value}</span>
    </div>
  );
}
