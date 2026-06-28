"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { AgentAvatar } from "./AgentAvatar";
import MaryLiveCall from "./MaryLiveCall";
import { useI18n } from "./lib/i18n";
import { BOOKING_URL } from "./lib/site";

type Phase = "ringing" | "live" | "ended";

type Bubble = { role: "in" | "out"; text: string };

const SCRIPT_KEYS: Array<{ role: "in" | "out"; key: string; afterMs: number }> = [
  { role: "out", key: "maryModal.line1", afterMs: 600 },
  { role: "in",  key: "maryModal.line2", afterMs: 2600 },
  { role: "out", key: "maryModal.line3", afterMs: 4800 },
  { role: "in",  key: "maryModal.line4", afterMs: 7000 },
  { role: "out", key: "maryModal.line5", afterMs: 9000 },
];

const DEMO_URL = BOOKING_URL;

type Props = {
  open: boolean;
  onClose: () => void;
};

export default function DemoCallModal({ open, onClose }: Props) {
  const { t } = useI18n();
  const [phase, setPhase] = useState<Phase>("ringing");
  const [seconds, setSeconds] = useState(0);
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [typingFor, setTypingFor] = useState<"in" | "out" | null>(null);
  const [live, setLive] = useState(false);
  const [mounted, setMounted] = useState(false);
  const dialogRef = useRef<HTMLDivElement | null>(null);
  const closeBtnRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => { setMounted(true); }, []);

  useEffect(() => {
    if (!open) return;
    setPhase("ringing");
    setSeconds(0);
    setBubbles([]);
    setTypingFor(null);
    setLive(false);

    const ringTimer = setTimeout(() => {
      setPhase("live");
      setTypingFor("out");
    }, 2200);

    return () => clearTimeout(ringTimer);
  }, [open]);

  useEffect(() => {
    if (!open || phase !== "live") return;
    const tick = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(tick);
  }, [open, phase]);

  useEffect(() => {
    if (!open || phase !== "live") return;
    const timers: ReturnType<typeof setTimeout>[] = [];
    SCRIPT_KEYS.forEach((entry, i) => {
      timers.push(
        setTimeout(() => {
          setBubbles((cur) => [...cur, { role: entry.role, text: t(entry.key) }]);
          const next = SCRIPT_KEYS[i + 1];
          setTypingFor(next ? next.role : null);
          if (i === SCRIPT_KEYS.length - 1) {
            timers.push(setTimeout(() => setPhase("ended"), 2200));
          }
        }, entry.afterMs),
      );
    });
    return () => timers.forEach(clearTimeout);
  }, [open, phase, t]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    closeBtnRef.current?.focus();
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open || !mounted) return null;

  const mm = Math.floor(seconds / 60).toString().padStart(2, "0");
  const ss = (seconds % 60).toString().padStart(2, "0");

  return createPortal(
    <div
      className="mary-modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Mary live demo"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="mary-modal" ref={dialogRef}>
        <button
          ref={closeBtnRef}
          className="mary-modal-close"
          aria-label="Close demo"
          onClick={onClose}
          type="button"
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        <div className="mary-modal-head">
          <span className="mary-modal-eyebrow">
            <span className="dot-pulse" aria-hidden /> {t("maryModal.eyebrow")}
          </span>
          <h3 className="mary-modal-title">{t("maryModal.title")}</h3>
        </div>

        {live ? (
          <div className="mary-modal-live">
            <MaryLiveCall onClose={onClose} />
          </div>
        ) : (
        <div className="mary-modal-stage">
          {/* Phone card */}
          <div className={`mary-phone phase-${phase}`}>
            <div className="mary-phone-glow" aria-hidden />
            <div className="mary-phone-avatar">
              {phase === "ringing" && (
                <>
                  <span className="phone-avatar-ring" />
                  <span className="phone-avatar-ring delay" />
                </>
              )}
              <AgentAvatar size={56} />
            </div>
            <div className="mary-phone-name">Mary · WorkflowAuth</div>
            <div className="mary-phone-status">
              {phase === "ringing" && t("maryModal.statusRinging")}
              {phase === "live" && (
                <>
                  <span className="dot-pulse" aria-hidden /> {t("maryModal.statusConnected")} · {mm}:{ss}
                </>
              )}
              {phase === "ended" && t("maryModal.statusEnded")}
            </div>
          </div>

          {/* Transcript feed */}
          <div className="mary-feed" aria-live="polite">
            {phase === "ringing" && (
              <div className="mary-feed-empty">
                <span className="mary-feed-empty-dots"><i /><i /><i /></span>
                <span>{t("maryModal.dialing")}</span>
              </div>
            )}
            {phase !== "ringing" && (
              <>
                {bubbles.map((b, i) => (
                  <div key={i} className={`mary-feed-bubble ${b.role}`}>
                    <span className="mary-feed-avatar">
                      {b.role === "out" ? "A" : (
                        <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 4-7 8-7s8 3 8 7" /></svg>
                      )}
                    </span>
                    <span className="mary-feed-text">{b.text}</span>
                  </div>
                ))}
                {typingFor && phase === "live" && (
                  <div className={`mary-feed-bubble ${typingFor} typing`}>
                    <span className="mary-feed-avatar">
                      {typingFor === "out" ? "A" : (
                        <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 4-7 8-7s8 3 8 7" /></svg>
                      )}
                    </span>
                    <span className="mary-feed-text">
                      <span className="typing-dots"><i /><i /><i /></span>
                    </span>
                  </div>
                )}
                {phase === "ended" && (
                  <div className="mary-feed-summary">
                    <div className="mary-feed-summary-title">{t("maryModal.summaryTitle")}</div>
                    <ul>
                      <li>{t("maryModal.summary1")}</li>
                      <li>{t("maryModal.summary2")}</li>
                      <li>{t("maryModal.summary3")}</li>
                      <li>{t("maryModal.summary4")}</li>
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
        )}

        <div className="mary-modal-foot">
          {!live && (
            <button
              type="button"
              className="mary-live-cta"
              onClick={() => setLive(true)}
            >
              <span className="mary-live-cta-icon" aria-hidden>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
                  <path d="M19 10a7 7 0 0 1-14 0M12 17v4" />
                </svg>
              </span>
              {t("maryModal.talkLive")}
            </button>
          )}
          <p className="mary-modal-foot-note">{t("maryModal.foot")}</p>
          <div className="mary-modal-actions">
            <a href={DEMO_URL} target="_blank" rel="noreferrer" className="btn btn-primary">
              {t("maryModal.bookReal")}
            </a>
            {live ? (
              <button type="button" className="btn btn-ghost" onClick={() => setLive(false)}>
                ← {t("maryModal.backToDemo")}
              </button>
            ) : (
              <Link href="/dashboard/test-call" className="btn btn-ghost" onClick={onClose}>
                {t("maryModal.openSim")} →
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
}
