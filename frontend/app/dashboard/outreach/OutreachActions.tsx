"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function OutreachActions() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function reactivate() {
    setBusy(true);
    setMsg("");
    try {
      const res = await fetch("/api/proxy/calls/outbound/reactivate/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setMsg(`Queued ${data.queued ?? 0} reactivation call${data.queued === 1 ? "" : "s"}.`);
        router.refresh();
      } else {
        setMsg("Couldn't start the campaign.");
      }
    } catch {
      setMsg("Network error — try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app-pagebar-actions" style={{ display: "flex", gap: 10, alignItems: "center" }}>
      {msg && <span className="dash-card-meta">{msg}</span>}
      <button className="btn btn-primary" onClick={reactivate} disabled={busy}>
        {busy ? "Starting…" : "Start reactivation campaign"}
      </button>
    </div>
  );
}
