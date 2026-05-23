"use client";

import { useEffect, useState } from "react";

import { useI18n } from "./lib/i18n";

type Kind = "call" | "quote" | "deal" | "subsidy" | "booked" | "sms";

const ITEM_KINDS: Kind[] = [
  "deal", "quote", "sms", "booked", "subsidy", "call",
  "deal", "quote", "call", "booked", "sms", "deal",
  "subsidy", "quote", "call", "booked", "sms", "deal",
];

const ICONS: Record<Kind, { color: string; symbol: string }> = {
  call: { color: "#16a34a", symbol: "●" },
  quote: { color: "#7c3aed", symbol: "●" },
  deal: { color: "#16a34a", symbol: "✓" },
  subsidy: { color: "#d2532b", symbol: "●" },
  booked: { color: "#2563eb", symbol: "●" },
  sms: { color: "#0ea5e9", symbol: "●" },
};

// Deterministic baseline so the counter "feels alive" without random hydration drift.
function baselineCount() {
  const start = new Date();
  start.setUTCHours(0, 0, 0, 0);
  const minutesSinceMidnight = Math.floor((Date.now() - start.getTime()) / 60000);
  return 247 + Math.floor(minutesSinceMidnight * 0.3);
}

export default function LiveTicker() {
  const { t } = useI18n();
  const items = ITEM_KINDS.map((kind, i) => ({
    kind,
    text: t(`ticker.i${i + 1}`),
  }));
  const loop = [...items, ...items];
  const [counter, setCounter] = useState(247);

  useEffect(() => {
    setCounter(baselineCount());
    const id = setInterval(() => setCounter((c) => c + 1), 3700);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="ticker-wrap">
      <div className="ticker-stat">
        <span className="ticker-pulse" />
        <strong>{counter}</strong>
        <span>{t("ticker.callsToday")}</span>
      </div>
      <div className="ticker-track-mask">
        <div className="ticker-track">
          {loop.map((it, i) => (
            <span className="ticker-item" key={i}>
              <span className="ticker-dot" style={{ background: ICONS[it.kind].color }}>
                {ICONS[it.kind].symbol}
              </span>
              {it.text}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
