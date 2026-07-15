"use client";

import { useEffect, useRef, useState } from "react";

import { useI18n } from "./lib/i18n";

// Browser voice session with Mary via the Vapi Web SDK. The assistant itself
// (voice, transcriber, and the custom-LLM model pointed at our backend agent
// loop) is configured in the Vapi dashboard; here we only open/close the call
// and render live captions.
//
// Required public env (safe to expose — Vapi public keys are client-side):
//   NEXT_PUBLIC_VAPI_PUBLIC_KEY
//   NEXT_PUBLIC_VAPI_ASSISTANT_ID
const PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY || "";
const ASSISTANT_ID = process.env.NEXT_PUBLIC_VAPI_ASSISTANT_ID || "";

// Hard cap so a public demo line can't run up unbounded voice minutes.
const MAX_SECONDS = 300;

type Status = "idle" | "connecting" | "live" | "ended" | "error";
type Line = { role: "user" | "assistant"; text: string };

// reason: the Vapi Web SDK doesn't ship granular event types; we narrow the
// fields we read at the use site.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type VapiInstance = any;

export default function MaryLiveCall({ onClose }: { onClose?: () => void }) {
  const { t } = useI18n();
  const [status, setStatus] = useState<Status>("idle");
  const [lines, setLines] = useState<Line[]>([]);
  const [seconds, setSeconds] = useState(0);
  const [muted, setMuted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const vapiRef = useRef<VapiInstance | null>(null);
  const feedRef = useRef<HTMLDivElement | null>(null);
  const watchdogRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const connectedRef = useRef(false);
  const retriedRef = useRef(false);

  const configured = Boolean(PUBLIC_KEY && ASSISTANT_ID);

  function clearWatchdog() {
    if (watchdogRef.current) {
      clearTimeout(watchdogRef.current);
      watchdogRef.current = null;
    }
  }

  function fail(messageKey: string, detail?: unknown) {
    clearWatchdog();
    setError(t(messageKey));
    setStatus("error");
    try {
      vapiRef.current?.stop();
    } catch {
      /* noop */
    }
    if (detail !== undefined) {
      // eslint-disable-next-line no-console
      console.error("MaryLiveCall:", messageKey, detail);
    }
  }

  // Tick the call timer and auto-end at the cap.
  useEffect(() => {
    if (status !== "live") return;
    const id = setInterval(() => {
      setSeconds((s) => {
        if (s + 1 >= MAX_SECONDS) stop();
        return s + 1;
      });
    }, 1000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  // Keep the caption feed scrolled to the newest line.
  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight });
  }, [lines]);

  // Preload the Vapi SDK chunk so tapping "Start" doesn't also pay the
  // download cost — one less thing that can fail at connect time.
  useEffect(() => {
    import("@vapi-ai/web").catch(() => {
      /* network hiccup — the click path retries the import */
    });
  }, []);

  // Always tear the call down on unmount.
  useEffect(() => {
    return () => {
      clearWatchdog();
      try {
        vapiRef.current?.stop();
      } catch {
        /* noop */
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // One silent retry for transient connect failures (flaky network, a Vapi
  // hiccup) so a visitor doesn't see an error the first time they tap Start.
  // Mic-permission problems are never retried — they need user action.
  function failOrRetry(messageKey: string, detail?: unknown) {
    if (!connectedRef.current && !retriedRef.current) {
      retriedRef.current = true;
      // eslint-disable-next-line no-console
      console.warn("MaryLiveCall: connect failed, retrying once", detail);
      clearWatchdog();
      try {
        vapiRef.current?.stop();
      } catch {
        /* noop */
      }
      setTimeout(() => connect(), 1200);
      return;
    }
    fail(messageKey, detail);
  }

  async function start() {
    if (!configured || status === "connecting" || status === "live") return;
    setError(null);
    setLines([]);
    setSeconds(0);
    connectedRef.current = false;
    retriedRef.current = false;
    setStatus("connecting");

    // Surface an already-blocked mic WITHOUT grabbing the device. Acquiring the
    // mic here and stopping the tracks (the old approach) left Vapi/Daily unable
    // to publish the caller's audio → "assistant did not receive customer audio".
    // Vapi acquires and owns the mic itself inside vapi.start().
    try {
      const perm = await navigator.permissions?.query?.(
        { name: "microphone" as PermissionName },
      );
      if (perm && perm.state === "denied") {
        fail("mary.live.micError");
        return;
      }
    } catch {
      /* Permissions API unavailable — let Vapi prompt for the mic itself. */
    }

    await connect();
  }

  async function connect() {
    try {
      const { default: Vapi } = await import("@vapi-ai/web");
      const vapi: VapiInstance = new Vapi(PUBLIC_KEY);
      vapiRef.current = vapi;

      vapi.on("call-start", () => {
        connectedRef.current = true;
        clearWatchdog();
        setStatus("live");
      });
      // Ignore call-end before call-start: tearing down a failed connect
      // attempt (e.g. before the silent retry) also emits call-end, and that
      // must not flip the UI out of "connecting".
      vapi.on("call-end", () => {
        if (connectedRef.current) setStatus("ended");
      });
      vapi.on("error", (e: unknown) => failOrRetry("mary.live.error", e));
      vapi.on("call-start-failed", (e: unknown) => failOrRetry("mary.live.error", e));
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      vapi.on("message", (msg: any) => {
        if (msg?.type === "transcript" && msg?.transcriptType === "final") {
          const role: Line["role"] = msg.role === "user" ? "user" : "assistant";
          setLines((cur) => [...cur, { role, text: String(msg.transcript ?? "") }]);
        }
      });

      // Backstop: if neither call-start nor an error fires (e.g. a flaky
      // network or a misconfigured assistant), surface a real error.
      clearWatchdog();
      watchdogRef.current = setTimeout(() => {
        if (!connectedRef.current) failOrRetry("mary.live.timeout");
      }, 25000);

      const call = await vapi.start(ASSISTANT_ID);
      if (!call && !connectedRef.current) failOrRetry("mary.live.timeout");
    } catch (e) {
      failOrRetry("mary.live.error", e);
    }
  }

  function stop() {
    clearWatchdog();
    try {
      vapiRef.current?.stop();
    } catch {
      /* noop */
    }
    setStatus("ended");
  }

  function toggleMute() {
    const next = !muted;
    setMuted(next);
    try {
      vapiRef.current?.setMuted(next);
    } catch {
      /* noop */
    }
  }

  const mm = Math.floor(seconds / 60).toString().padStart(2, "0");
  const ss = (seconds % 60).toString().padStart(2, "0");

  if (!configured) {
    return (
      <div className="mlc">
        <div className="mlc-notice">
          <strong>{t("mary.live.soonTitle")}</strong>
          <p>{t("mary.live.soonBody")}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mlc">
      <div className={`mlc-orb status-${status}`} aria-hidden>
        <span className="mlc-orb-core" />
        {status === "live" && (
          <>
            <span className="mlc-orb-ring" />
            <span className="mlc-orb-ring delay" />
          </>
        )}
      </div>

      {(status === "idle" || status === "connecting") && (
        <p className="mlc-context">{t("mary.live.context")}</p>
      )}

      <div className="mlc-status">
        {status === "idle" && t("mary.live.ready")}
        {status === "connecting" && t("mary.live.connecting")}
        {status === "live" && (
          <>
            <span className="dot-pulse" aria-hidden /> {t("mary.live.live")} · {mm}:{ss}
          </>
        )}
        {status === "ended" && t("mary.live.ended")}
        {status === "error" && (error || t("mary.live.error"))}
      </div>

      {(status === "live" || lines.length > 0) && (
        <div className="mlc-feed" ref={feedRef} aria-live="polite">
          {lines.map((l, i) => (
            <div key={i} className={`mlc-bubble ${l.role}`}>
              <span className="mlc-bubble-who">
                {l.role === "assistant" ? "Mary" : t("mary.live.you")}
              </span>
              <span>{l.text}</span>
            </div>
          ))}
          {lines.length === 0 && status === "live" && (
            <div className="mlc-hint">{t("mary.live.sayHi")}</div>
          )}
        </div>
      )}

      <div className="mlc-actions">
        {(status === "idle" || status === "ended" || status === "error") && (
          <button type="button" className="btn btn-mary btn-lg" onClick={start}>
            <span className="btn-mary-dot" aria-hidden />{" "}
            {status === "ended" || status === "error" ? t("mary.live.again") : t("mary.live.start")}
          </button>
        )}
        {status === "connecting" && (
          <button type="button" className="btn btn-ghost" disabled>
            {t("mary.live.connecting")}
          </button>
        )}
        {status === "live" && (
          <>
            <button type="button" className="btn btn-ghost" onClick={toggleMute}>
              {muted ? t("mary.live.unmute") : t("mary.live.mute")}
            </button>
            <button type="button" className="btn btn-danger" onClick={stop}>
              {t("mary.live.hangup")}
            </button>
          </>
        )}
        {(status === "ended" || status === "error") && onClose && (
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            {t("mary.live.close")}
          </button>
        )}
      </div>

      <p className="mlc-consent">{t("mary.live.consent")}</p>
    </div>
  );
}
