"use client";

import { useEffect, useRef, useState } from "react";
import {
  startConversation,
  sendMessage,
  loadHistory,
  connectLiveSocket,
  pollLiveMessages,
  hasLiveSession,
  resetLiveSession,
  closeConversation,
  getStoredIdentity,
  setStoredIdentity,
  type SupportMessage,
  type LiveSocket,
} from "./lib/supportClient";
import { useI18n } from "./lib/i18n";

type Msg = { role: "ai" | "user" | "system" | "staff"; text: string; ts: number };
type Mode = "ai" | "intake" | "live";

const SCRIPT_KEYS: Array<{ uKey: string; aKeys: string[] }> = [
  { uKey: "chat.script.q1", aKeys: ["chat.script.a1a", "chat.script.a1b"] },
  { uKey: "chat.script.q2", aKeys: ["chat.script.a2a", "chat.script.a2b"] },
  { uKey: "chat.script.q3", aKeys: ["chat.script.a3a", "chat.script.a3b"] },
];

function fromSupport(m: SupportMessage): Msg {
  return {
    role: m.author_type === "staff" ? "staff" : m.author_type === "system" ? "system" : "user",
    text: m.body,
    ts: new Date(m.created_at).getTime(),
  };
}

export default function ChatWidget() {
  const { t } = useI18n();
  const INTRO: Msg = { role: "ai", text: t("chat.intro"), ts: Date.now() };
  const HANDOFF_INTRO: Msg = { role: "system", text: t("chat.handoffIntro"), ts: Date.now() };

  const [open, setOpen] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const [teaser, setTeaser] = useState(false);
  const [mode, setMode] = useState<Mode>("ai");
  const [messages, setMessages] = useState<Msg[]>([INTRO]);
  const [draft, setDraft] = useState("");
  const [thinking, setThinking] = useState(false);
  const [liveStatus, setLiveStatus] = useState<"idle" | "connecting" | "connected" | "error">("idle");
  const [identity, setIdentity] = useState<{ name: string; email: string }>({ name: "", email: "" });
  const [intakeError, setIntakeError] = useState<string | null>(null);
  const [closed, setClosed] = useState(false);
  const scriptIdx = useRef(0);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const wsRef = useRef<LiveSocket | null>(null);
  const pollerRef = useRef<{ stop: () => void } | null>(null);
  const seenIds = useRef<Set<string>>(new Set());

  function ingestSupportMessage(m: SupportMessage) {
    if (seenIds.current.has(m.id)) return;
    seenIds.current.add(m.id);
    if (m.author_type === "staff" || m.author_type === "system") {
      pushMessage(fromSupport(m));
    }
    if (m.author_type === "system" && /ended|resolved/i.test(m.body)) {
      setClosed(true);
    }
  }

  function startPollingFallback() {
    if (pollerRef.current) return;
    pollerRef.current = pollLiveMessages(ingestSupportMessage, 4000);
  }

  function stopPollingFallback() {
    pollerRef.current?.stop();
    pollerRef.current = null;
  }

  // Hydrate stored identity once on mount
  useEffect(() => {
    setIdentity(getStoredIdentity());
  }, []);

  // Reveal once visitor scrolls past hero
  useEffect(() => {
    function onScroll() {
      const trigger = Math.max(800, window.innerHeight * 1.4);
      if (window.scrollY > trigger) {
        setRevealed(true);
        setTeaser(true);
        window.removeEventListener("scroll", onScroll);
      }
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (!teaser) return;
    const t = setTimeout(() => setTeaser(false), 8000);
    return () => clearTimeout(t);
  }, [teaser]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, thinking]);

  // If a previous live session exists in localStorage, reload its history when widget opens
  useEffect(() => {
    if (!open || mode !== "ai") return;
    if (!hasLiveSession()) return;
    // Auto-resume live mode for returning visitors
    void resumeLive();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
      wsRef.current = null;
      pollerRef.current?.stop();
      pollerRef.current = null;
    };
  }, []);

  function pushMessage(m: Msg, dedupKey?: string) {
    if (dedupKey) {
      if (seenIds.current.has(dedupKey)) return;
      seenIds.current.add(dedupKey);
    }
    setMessages((prev) => [...prev, m]);
  }

  function send(text: string) {
    if (!text.trim()) return;
    if (mode === "live") {
      void sendLive(text);
      return;
    }
    sendAI(text);
  }

  function sendAI(text: string) {
    pushMessage({ role: "user", text, ts: Date.now() });
    setDraft("");
    setThinking(true);
    const idx = scriptIdx.current % SCRIPT_KEYS.length;
    const replies = SCRIPT_KEYS[idx].aKeys.map((k) => t(k));
    scriptIdx.current += 1;
    let delay = 900;
    replies.forEach((reply, i) => {
      setTimeout(() => {
        pushMessage({ role: "ai", text: reply, ts: Date.now() });
        if (i === replies.length - 1) setThinking(false);
      }, delay);
      delay += 1100;
    });
  }

  async function sendLive(text: string) {
    if (closed) return;
    pushMessage({ role: "user", text, ts: Date.now() });
    setDraft("");
    try {
      const msg = await sendMessage(text);
      // Mark as seen so the WS echo doesn't duplicate it
      seenIds.current.add(msg.id);
    } catch (e) {
      const msg = (e as Error).message || "";
      if (msg.includes("closed")) {
        setClosed(true);
        pushMessage({ role: "system", text: t("chat.error.closed"), ts: Date.now() });
      } else {
        pushMessage({ role: "system", text: t("chat.error.send"), ts: Date.now() });
      }
      console.error(e);
    }
  }

  function requestLiveChat() {
    const stored = getStoredIdentity();
    if (stored.name && stored.email) {
      void startLiveChat();
      return;
    }
    setIntakeError(null);
    setMode("intake");
  }

  async function submitIntake(name: string, email: string) {
    const trimmedName = name.trim();
    const trimmedEmail = email.trim();
    if (!trimmedName) { setIntakeError(t("chat.intake.errName")); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      setIntakeError(t("chat.intake.errEmail")); return;
    }
    setStoredIdentity(trimmedName, trimmedEmail);
    setIdentity({ name: trimmedName, email: trimmedEmail });
    await startLiveChat();
  }

  async function startLiveChat(prefill?: string) {
    setMode("live");
    setLiveStatus("connecting");
    pushMessage(HANDOFF_INTRO);

    const opener =
      prefill ||
      messages
        .filter((m) => m.role === "user")
        .slice(-1)[0]?.text ||
      "Hi, I'd like to talk to someone.";

    try {
      const stored = getStoredIdentity();
      const { message } = await startConversation({
        body: opener,
        name: stored.name,
        email: stored.email,
      });
      seenIds.current.add(message.id);

      // Reload existing history to surface staff replies if visitor was returning
      const history = await loadHistory();
      const newMsgs: Msg[] = history
        .filter((m) => !seenIds.current.has(m.id))
        .map((m) => {
          seenIds.current.add(m.id);
          return fromSupport(m);
        });
      if (newMsgs.length > 0) setMessages((prev) => [...prev, ...newMsgs]);

      // Open WebSocket for incoming staff replies (with auto-reconnect)
      wsRef.current?.close();
      stopPollingFallback();
      wsRef.current = connectLiveSocket(
        ingestSupportMessage,
        (status) => {
          setLiveStatus(
            status === "connected" ? "connected" : status === "connecting" ? "connecting" : "idle",
          );
          if (status === "connected") {
            stopPollingFallback();
          } else if (status === "closed") {
            // WS went away (server doesn't support it, e.g. Vercel) — poll instead.
            startPollingFallback();
          }
        },
      );
      // If the WS hasn't opened after 3 s, also start polling so the user
      // never sits with stale messages.
      setTimeout(() => {
        if (!wsRef.current?.isOpen()) startPollingFallback();
      }, 3000);
    } catch (e) {
      console.error(e);
      pushMessage({
        role: "system",
        text: t("chat.live.unreachable"),
        ts: Date.now(),
      });
      setLiveStatus("error");
      setMode("ai");
    }
  }

  async function resumeLive() {
    setMode("live");
    setLiveStatus("connecting");
    try {
      const history = await loadHistory();
      const fresh: Msg[] = history
        .filter((m) => {
          if (seenIds.current.has(m.id)) return false;
          seenIds.current.add(m.id);
          return true;
        })
        .map(fromSupport);
      if (fresh.length > 0) {
        setMessages((prev) => [
          ...prev,
          {
            role: "system",
            text: t("chat.live.welcomeBack"),
            ts: Date.now(),
          },
          ...fresh,
        ]);
      }
      wsRef.current?.close();
      stopPollingFallback();
      wsRef.current = connectLiveSocket(
        ingestSupportMessage,
        (status) => {
          setLiveStatus(
            status === "connected" ? "connected" : status === "connecting" ? "connecting" : "idle",
          );
          if (status === "connected") {
            stopPollingFallback();
          } else if (status === "closed") {
            // WS went away (server doesn't support it, e.g. Vercel) — poll instead.
            startPollingFallback();
          }
        },
      );
      // If the WS hasn't opened after 3 s, also start polling so the user
      // never sits with stale messages.
      setTimeout(() => {
        if (!wsRef.current?.isOpen()) startPollingFallback();
      }, 3000);
    } catch {
      resetLiveSession();
      setMode("ai");
      setLiveStatus("idle");
    }
  }

  function endLiveChat() {
    if (!closed) {
      // Tell backend so staff get notified + DB updates.
      void closeConversation();
    }
    wsRef.current?.close();
    wsRef.current = null;
    stopPollingFallback();
    resetLiveSession();
    seenIds.current.clear();
    setLiveStatus("idle");
    setMode("ai");
    setClosed(false);
    pushMessage({
      role: "system",
      text: t("chat.live.backToAnna"),
      ts: Date.now(),
    });
  }

  function trigger(presetText: string) {
    if (!open) setOpen(true);
    send(presetText);
  }

  return (
    <>
      {/* TEASER bubble */}
      {!open && revealed && teaser && (
        <div className="chat-teaser">
          <button
            type="button"
            className="chat-teaser-main"
            onClick={() => { setOpen(true); setTeaser(false); }}
            aria-label={t("chat.openLabel")}
          >
            <span className="chat-teaser-avatar">A</span>
            <div>
              <div className="chat-teaser-title">{t("chat.teaser.title")}</div>
              <div className="chat-teaser-body">{t("chat.teaser.body")}</div>
            </div>
          </button>
          <button
            type="button"
            className="chat-teaser-close"
            onClick={() => setTeaser(false)}
            aria-label={t("chat.dismissTeaser")}
          >
            ×
          </button>
        </div>
      )}

      {/* FAB launcher */}
      {!open && revealed && (
        <button className="chat-fab" onClick={() => { setOpen(true); setTeaser(false); }} aria-label={t("chat.openLabel")}>
          <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" width="22" height="22">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <span className="chat-fab-pulse" />
        </button>
      )}

      {/* PANEL */}
      {open && (
        <div className="chat-panel">
          <div className="chat-head">
            <div className="chat-head-left">
              <span className="chat-avatar">{mode === "live" ? "H" : "A"}</span>
              <div>
                <div className="chat-name">
                  {mode === "live" ? t("chat.live.support") : "Mary"} <span className="chat-online" />
                </div>
                <div className="chat-role">
                  {mode === "live"
                    ? liveStatus === "connected"
                      ? t("chat.live.connected")
                      : liveStatus === "connecting"
                      ? t("chat.live.connecting")
                      : t("chat.live.title")
                    : t("chat.role")}
                </div>
              </div>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label={t("chat.closeLabel")}>×</button>
          </div>

          {mode === "intake" ? (
            <IntakeForm
              initialName={identity.name}
              initialEmail={identity.email}
              error={intakeError}
              onCancel={() => setMode("ai")}
              onSubmit={submitIntake}
            />
          ) : (
            <>
              <div className="chat-messages" ref={scrollRef}>
                {messages.map((m, i) => (
                  <div key={i} className={`chat-msg ${m.role}`}>
                    {(m.role === "ai" || m.role === "staff") && (
                      <span className="chat-msg-avatar">{m.role === "staff" ? "H" : "A"}</span>
                    )}
                    <div className="chat-msg-bubble">{m.text}</div>
                  </div>
                ))}
                {thinking && (
                  <div className="chat-msg ai">
                    <span className="chat-msg-avatar">A</span>
                    <div className="chat-msg-bubble typing">
                      <span className="typing-dots"><i /><i /><i /></span>
                    </div>
                  </div>
                )}
              </div>

              {/* Quick replies / mode controls */}
              <div className="chat-quick">
                {mode === "ai" ? (
                  <>
                    <button onClick={() => trigger(t("chat.script.q1"))}>{t("chat.quick.quote")}</button>
                    <button onClick={() => trigger(t("chat.script.q2"))}>{t("chat.quick.book")}</button>
                    <button
                      onClick={requestLiveChat}
                      style={{ background: "#0f172a", color: "white", borderColor: "#0f172a" }}
                    >
                      {t("chat.quick.human")}
                    </button>
                  </>
                ) : closed ? (
                  <button
                    onClick={endLiveChat}
                    style={{ background: "#0f172a", color: "white", borderColor: "#0f172a" }}
                  >
                    {t("chat.live.startNew")}
                  </button>
                ) : (
                  <button onClick={endLiveChat}>{t("chat.live.end")}</button>
                )}
              </div>

              {closed && mode === "live" ? (
                <div className="chat-closed-banner">
                  {t("chat.live.closedBanner")}
                </div>
              ) : (
                <form
                  className="chat-input"
                  onSubmit={(e) => { e.preventDefault(); send(draft); }}
                >
                  <input
                    type="text"
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    placeholder={mode === "live" ? t("chat.live.placeholder") : t("chat.placeholder")}
                    autoFocus
                  />
                  <button type="submit" aria-label={t("chat.send")}>
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" /></svg>
                  </button>
                </form>
              )}
            </>
          )}
        </div>
      )}
    </>
  );
}

function IntakeForm({
  initialName,
  initialEmail,
  error,
  onCancel,
  onSubmit,
}: {
  initialName: string;
  initialEmail: string;
  error: string | null;
  onCancel: () => void;
  onSubmit: (name: string, email: string) => void;
}) {
  const { t } = useI18n();
  const [name, setName] = useState(initialName);
  const [email, setEmail] = useState(initialEmail);
  const [submitting, setSubmitting] = useState(false);

  return (
    <form
      className="chat-intake"
      onSubmit={async (e) => {
        e.preventDefault();
        setSubmitting(true);
        try {
          await onSubmit(name, email);
        } finally {
          setSubmitting(false);
        }
      }}
    >
      <div className="chat-intake-title">{t("chat.intake.title")}</div>
      <div className="chat-intake-sub">{t("chat.intake.sub")}</div>
      <label className="chat-intake-field">
        <span>{t("chat.intake.name")}</span>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t("chat.intake.namePh")}
          autoFocus
          required
        />
      </label>
      <label className="chat-intake-field">
        <span>{t("chat.intake.email")}</span>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder={t("chat.intake.emailPh")}
          required
        />
      </label>
      {error && <div className="chat-intake-error">{error}</div>}
      <div className="chat-intake-actions">
        <button type="button" className="chat-intake-cancel" onClick={onCancel}>
          {t("chat.intake.cancel")}
        </button>
        <button type="submit" className="chat-intake-submit" disabled={submitting}>
          {submitting ? t("chat.intake.submitting") : t("chat.intake.submit")}
        </button>
      </div>
    </form>
  );
}
