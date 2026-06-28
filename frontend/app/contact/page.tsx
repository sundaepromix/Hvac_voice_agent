"use client";

import { useEffect, useState } from "react";
import {
  getStoredIdentity,
  setStoredIdentity,
} from "../lib/supportClient";
import { useI18n } from "../lib/i18n";
import { MarketingFooter, MarketingTopbar } from "../MarketingShell";
import CalendlyInline from "../CalendlyInline";
import { BOOKING_URL, BOOKING_IS_EXTERNAL, BOOKING_IS_CALENDLY } from "../lib/site";

type Status = "idle" | "submitting" | "success" | "error";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const CALENDLY = BOOKING_URL;
const SUPPORT_EMAIL = "promise@workflowauth.com";

async function submitContactTicket(opts: {
  name: string;
  email: string;
  subject: string;
  body: string;
}): Promise<{ conversation_id: string; ticket_id: number }> {
  const res = await fetch(`${API_URL}/support/tickets/contact/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(opts),
  });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as { conversation_id: string; ticket_id: number };
}

export default function ContactPage() {
  const { t } = useI18n();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [ticketId, setTicketId] = useState<string | null>(null);

  useEffect(() => {
    const stored = getStoredIdentity();
    if (stored.name) setName(stored.name);
    if (stored.email) setEmail(stored.email);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!name.trim() || !email.trim() || !body.trim()) {
      setError(t("contact.error.required"));
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setError(t("contact.error.email"));
      return;
    }
    setStatus("submitting");
    try {
      const r = await submitContactTicket({
        name: name.trim(),
        email: email.trim(),
        subject: subject.trim() || "(no subject)",
        body: body.trim(),
      });
      setStoredIdentity(name.trim(), email.trim());
      setTicketId(r.conversation_id);
      setBody("");
      setSubject("");
      setStatus("success");
    } catch (err) {
      setError((err as Error).message || t("contact.error.fallback"));
      setStatus("error");
    }
  }

  return (
    <>
      <MarketingTopbar />
      <main className="contact-page">
        <section className="shell hero hero-tight">
          <span className="hero-meet">
            <span className="hero-meet-avatar">@</span>
            <span>{t("contact.heroEyebrow")}</span>
          </span>
          <h1 className="hero-title">
            {t("contact.heroT1")}<br />
            <span className="hero-title-em">{t("contact.heroT2")}</span>
          </h1>
          <p className="hero-sub">{t("contact.heroSub")}</p>
        </section>

        {BOOKING_IS_EXTERNAL && (
          <section className="shell section-tight" id="book">
            <div className="section-head">
              <span className="section-flourish">{t("contact.book.eyebrow")}</span>
              <h2 className="section-title">{t("contact.book.title")}</h2>
              <p className="section-sub">{t("contact.book.sub")}</p>
            </div>
            {BOOKING_IS_CALENDLY ? (
              <div className="calendly-shell">
                <CalendlyInline url={CALENDLY} />
              </div>
            ) : (
              <div className="book-cta">
                <a href={CALENDLY} target="_blank" rel="noreferrer" className="btn btn-primary btn-lg">
                  {t("contact.book.cta")} →
                </a>
              </div>
            )}
          </section>
        )}

        <section className="shell section-tight">
          <div className="contact-grid">
            {/* LEFT — channels */}
            <aside className="contact-channels">
              <ChannelCard
                icon={<CalIcon />}
                title={t("contact.ch1.title")}
                body={t("contact.ch1.body")}
                cta={`${t("contact.ch1.cta")} →`}
                href={CALENDLY}
                accent="#d2532b"
              />
              <ChannelCard
                icon={<MailIcon />}
                title={t("contact.ch2.title")}
                body={t("contact.ch2.body")}
                cta={SUPPORT_EMAIL}
                href={`mailto:${SUPPORT_EMAIL}`}
                accent="#2563eb"
              />
            </aside>

            {/* RIGHT — ticket form */}
            <div className="contact-card">
              <div className="contact-card-head">
                <h2 className="contact-card-title">{t("contact.cardTitle")}</h2>
                <p className="contact-card-sub">{t("contact.cardSub")}</p>
              </div>

              {status === "success" ? (
                <div className="contact-success">
                  <div className="contact-success-mark" aria-hidden>✓</div>
                  <h2>{t("contact.success.title")}</h2>
                  <p>
                    {name.split(" ")[0]} — <strong>{email}</strong>
                  </p>
                  {ticketId && (
                    <p className="contact-success-ref">
                      <code>{ticketId.slice(0, 8)}</code>
                    </p>
                  )}
                  <button
                    type="button"
                    className="contact-success-again"
                    onClick={() => {
                      setStatus("idle");
                      setTicketId(null);
                    }}
                  >
                    {t("contact.success.again")}
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="contact-form">
                  <div className="contact-row">
                    <label className="contact-field">
                      <span>{t("contact.f.name")}</span>
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Jane Doe"
                        required
                      />
                    </label>
                    <label className="contact-field">
                      <span>{t("contact.f.email")}</span>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="jane@example.com"
                        required
                      />
                    </label>
                  </div>
                  <label className="contact-field">
                    <span>{t("contact.f.subject")}</span>
                    <input
                      type="text"
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                      placeholder={t("contact.f.subjectPh")}
                    />
                  </label>
                  <label className="contact-field">
                    <span>{t("contact.f.body")}</span>
                    <textarea
                      value={body}
                      onChange={(e) => setBody(e.target.value)}
                      rows={6}
                      placeholder={t("contact.f.bodyPh")}
                      required
                    />
                  </label>

                  {error && <div className="contact-error">{error}</div>}

                  <div className="contact-actions">
                    <button
                      type="submit"
                      className="contact-submit"
                      disabled={status === "submitting"}
                    >
                      {status === "submitting" ? t("contact.f.sending") : `${t("contact.f.send")} →`}
                    </button>
                    <span className="contact-hint">{t("contact.f.hint")}</span>
                  </div>
                </form>
              )}
            </div>
          </div>
        </section>

        <MarketingFooter />
      </main>
    </>
  );
}

function ChannelCard({
  icon,
  title,
  body,
  cta,
  href,
  accent,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
  cta: string;
  href: string;
  accent: string;
}) {
  const external = href.startsWith("http") || href.startsWith("mailto:");
  return (
    <a
      href={href}
      target={external && !href.startsWith("mailto:") ? "_blank" : undefined}
      rel={external && !href.startsWith("mailto:") ? "noreferrer" : undefined}
      className="contact-channel"
      style={{ ["--accent" as string]: accent }}
    >
      <span className="contact-channel-icon" aria-hidden>{icon}</span>
      <div className="contact-channel-body">
        <strong>{title}</strong>
        <span>{body}</span>
        <span className="contact-channel-cta">{cta}</span>
      </div>
    </a>
  );
}

function CalIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  );
}
function MailIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <polyline points="22,6 12,13 2,6" />
    </svg>
  );
}
