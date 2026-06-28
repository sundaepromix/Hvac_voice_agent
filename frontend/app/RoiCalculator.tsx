"use client";

import { useId, useState } from "react";

type Props = {
  callsLabel: string;
  valueLabel: string;
  resultLabel: string;
  foot: string;
};

// Share of missed calls WorkflowAuth converts into booked work. The displayed
// recovered revenue is this fraction of the gross (missed calls × avg value).
// ~1 in 3: answering 24/7 + instant callback recovers roughly a third of the
// calls a business currently misses.
const CAPTURE_RATE = 1 / 3;

function formatUSD(n: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(Math.max(0, Math.round(n)));
}

export default function RoiCalculator({ callsLabel, valueLabel, resultLabel, foot }: Props) {
  // Deterministic defaults so server and first client render match (no hydration drift).
  const [calls, setCalls] = useState(30);
  const [value, setValue] = useState(500);
  const callsId = useId();
  const valueId = useId();

  const recovered = calls * value * CAPTURE_RATE;

  return (
    <div className="roi-card">
      <div className="roi-inputs">
        <label className="roi-field" htmlFor={callsId}>
          <span>{callsLabel}</span>
          <input
            id={callsId}
            type="number"
            min={0}
            inputMode="numeric"
            value={calls}
            onChange={(e) => setCalls(Math.max(0, Number(e.target.value) || 0))}
          />
        </label>
        <label className="roi-field" htmlFor={valueId}>
          <span>{valueLabel}</span>
          <input
            id={valueId}
            type="number"
            min={0}
            inputMode="numeric"
            value={value}
            onChange={(e) => setValue(Math.max(0, Number(e.target.value) || 0))}
          />
        </label>
      </div>
      <div className="roi-result">
        <span className="roi-result-label">{resultLabel}</span>
        <strong className="roi-result-value">{formatUSD(recovered)}</strong>
      </div>
      <p className="roi-foot">{foot}</p>
    </div>
  );
}
