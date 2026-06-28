"use client";

import { useEffect, useRef, useState } from "react";

// Scripted, vertical-agnostic inbound call. This is a simulated preview — the
// real voice agent runs on each business's own script, voice, and knowledge base.
type Line = { who: "mar" | "caller"; text: string };

const SCRIPT: Line[] = [
  { who: "mar", text: "Thanks for calling — this is Mary. How can I help today?" },
  { who: "caller", text: "Hi, I'd like to book an appointment and check your pricing." },
  { who: "mar", text: "Happy to help. Can I grab your name and a good number to reach you?" },
  { who: "caller", text: "It's Jordan, and this number's fine." },
  { who: "mar", text: "Thanks, Jordan. I've got an opening tomorrow at 9:30 AM — shall I book it?" },
  { who: "caller", text: "Yes, please." },
  { who: "mar", text: "Booked! I'll text your confirmation. Anything else I can do?" },
  { who: "caller", text: "That's everything, thanks." },
  { who: "mar", text: "Great — talk soon. Bye now!" },
];

// Captured-data rows reveal as the call progresses (after which script line).
const CAPTURE = [
  { afterLine: 3, label: "Lead", value: "Jordan" },
  { afterLine: 4, label: "Appointment", value: "Tomorrow · 9:30 AM" },
  { afterLine: 6, label: "Lead score", value: "92 · Hot" },
  { afterLine: 6, label: "SMS confirmation", value: "Sent" },
];

type Phase = "idle" | "connecting" | "connected" | "ended";

function fmt(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export default function MarLiveDemo() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [shown, setShown] = useState(0); // number of script lines revealed
  const [seconds, setSeconds] = useState(0);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  function clearTimers() {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  }

  useEffect(() => clearTimers, []);

  // Tick the call timer while connected.
  useEffect(() => {
    if (phase !== "connected") return;
    const id = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [phase]);

  function start() {
    clearTimers();
    setShown(0);
    setSeconds(0);
    setPhase("connecting");
    timers.current.push(
      setTimeout(() => {
        setPhase("connected");
        SCRIPT.forEach((_, i) => {
          timers.current.push(
            setTimeout(() => {
              setShown(i + 1);
              if (i === SCRIPT.length - 1) {
                timers.current.push(setTimeout(() => setPhase("ended"), 1400));
              }
            }, i * 1700),
          );
        });
      }, 1300),
    );
  }

  function reset() {
    clearTimers();
    setPhase("idle");
    setShown(0);
    setSeconds(0);
  }

  const captured = CAPTURE.filter((c) => shown >= c.afterLine);

  return (
    <div className="mar-demo">
      <div className="mar-phone">
        <div className="mar-phone-notch" aria-hidden />
        <div className="mar-phone-head">
          <div className="mar-avatar" aria-hidden>M</div>
          <div className="mar-phone-titles">
            <strong>Mary</strong>
            <span>AI Voice Assist · WorkflowAuth</span>
          </div>
          <span className={`mar-status mar-status-${phase}`}>
            {phase === "idle" && "Ready"}
            {phase === "connecting" && "Connecting…"}
            {(phase === "connected" || phase === "ended") && (
              <>
                <span className="mar-status-dot" aria-hidden /> {fmt(seconds)}
              </>
            )}
          </span>
        </div>

        <div className="mar-thread" aria-live="polite">
          {phase === "idle" && (
            <div className="mar-thread-empty">
              <p>Tap the button to hear how Mary handles a live call.</p>
            </div>
          )}
          {phase !== "idle" &&
            SCRIPT.slice(0, shown).map((l, i) => (
              <div key={i} className={`mar-bubble mar-bubble-${l.who}`}>
                {l.text}
              </div>
            ))}
          {phase === "connecting" && <div className="mar-bubble mar-bubble-mar mar-typing">…</div>}
        </div>

        <div className="mar-phone-actions">
          {phase === "idle" || phase === "ended" ? (
            <button type="button" className="mar-call-btn" onClick={start}>
              <PhoneIcon /> {phase === "ended" ? "Replay call with Mary" : "Tap to call Mary"}
            </button>
          ) : (
            <button type="button" className="mar-call-btn mar-call-btn-end" onClick={reset}>
              <PhoneIcon /> End call
            </button>
          )}
        </div>
      </div>

      <div className="mar-capture">
        <div className="mar-capture-head">Captured in real time</div>
        {captured.length === 0 ? (
          <p className="mar-capture-empty">As Mary talks, the lead is captured, scored, and booked here — and pushed to your CRM.</p>
        ) : (
          <ul className="mar-capture-list">
            {captured.map((c) => (
              <li key={c.label}>
                <span className="mar-capture-check" aria-hidden>✓</span>
                <span className="mar-capture-label">{c.label}</span>
                <strong className="mar-capture-value">{c.value}</strong>
              </li>
            ))}
          </ul>
        )}
        <p className="mar-capture-foot">Simulated demo. Your real agent runs on your business's own script, voice, and data.</p>
      </div>
    </div>
  );
}

function PhoneIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z" />
    </svg>
  );
}
