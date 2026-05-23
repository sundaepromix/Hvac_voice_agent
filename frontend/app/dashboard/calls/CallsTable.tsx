"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState, useTransition } from "react";

import { fmtAge, type Call } from "../format";
import { StatusPill } from "../parts";

export default function CallsTable({
  calls, defaultPersona,
}: {
  calls: Call[];
  defaultPersona: string;
}) {
  const router = useRouter();
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [busy, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const allIds = useMemo(() => calls.map((c) => c.id), [calls]);
  const allSelected = calls.length > 0 && selected.size === calls.length;
  const someSelected = selected.size > 0 && !allSelected;

  function toggleOne(id: number, on: boolean) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (on) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  function toggleAll(on: boolean) {
    setSelected(on ? new Set(allIds) : new Set());
  }

  async function deleteOne(id: number) {
    if (!confirm("Delete this call? This can't be undone.")) return;
    setError(null);
    const res = await fetch(`/api/proxy/calls/${id}`, { method: "DELETE" });
    if (!res.ok && res.status !== 204) {
      setError("Failed to delete call");
      return;
    }
    setSelected((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
    startTransition(() => router.refresh());
  }

  async function deleteSelected() {
    if (selected.size === 0) return;
    if (!confirm(`Delete ${selected.size} call${selected.size === 1 ? "" : "s"}? This can't be undone.`)) return;
    setError(null);
    const res = await fetch("/api/proxy/calls/bulk-delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids: Array.from(selected) }),
    });
    if (!res.ok) {
      setError("Failed to delete calls");
      return;
    }
    setSelected(new Set());
    startTransition(() => router.refresh());
  }

  async function deleteAll() {
    if (!confirm("Delete ALL calls? This wipes every call in the table and can't be undone.")) return;
    setError(null);
    const res = await fetch("/api/proxy/calls/bulk-delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ all: true }),
    });
    if (!res.ok) {
      setError("Failed to delete calls");
      return;
    }
    setSelected(new Set());
    startTransition(() => router.refresh());
  }

  return (
    <>
      <div className="leads-bulkbar">
        <div className="leads-bulkbar-left">
          <label className="leads-checkbox">
            <input
              type="checkbox"
              checked={allSelected}
              ref={(el) => { if (el) el.indeterminate = someSelected; }}
              onChange={(e) => toggleAll(e.target.checked)}
              disabled={calls.length === 0}
            />
            <span>{selected.size > 0 ? `${selected.size} selected` : `Select all (${calls.length})`}</span>
          </label>
        </div>
        <div className="leads-bulkbar-right">
          {selected.size > 0 && (
            <button type="button" className="btn btn-danger" onClick={deleteSelected} disabled={busy}>
              Delete selected
            </button>
          )}
          <button type="button" className="btn btn-ghost btn-danger-ghost" onClick={deleteAll} disabled={busy || calls.length === 0}>
            Delete all
          </button>
        </div>
      </div>

      {error && <div className="leads-error">{error}</div>}

      <section className="app-table">
        <div className="app-table-head cols-calls-select">
          <span />
          <span>Caller</span>
          <span>Provider</span>
          <span>Summary</span>
          <span style={{ textAlign: "right" }}>Status</span>
          <span />
        </div>
        {calls.length === 0 ? (
          <div className="app-table-empty">
            <h3>No calls match these filters</h3>
            <p>Wire a Vapi or Twilio webhook to <code>/api/calls/webhooks/vapi/</code>.</p>
          </div>
        ) : (
          calls.map((c) => {
            const checked = selected.has(c.id);
            return (
              <div key={c.id} className={`app-table-row cols-calls-select ${checked ? "is-selected" : ""}`}>
                <label className="leads-checkbox leads-row-check" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => toggleOne(c.id, e.target.checked)}
                  />
                </label>
                <div className="app-row-customer">
                  <span className="app-row-avatar" style={{ fontSize: 14 }}>📞</span>
                  <div>
                    <div className="app-row-title">{c.from_number || "unknown"}</div>
                    <div className="app-row-sub">→ {c.to_number || "—"}</div>
                  </div>
                </div>
                <div>
                  <span className="tag" style={{ marginLeft: 0 }}>{c.provider}</span>
                  <div className="app-row-sub" style={{ marginTop: 4 }}>{c.persona_used || defaultPersona}</div>
                </div>
                <div>
                  <div className="app-row-title app-row-title-soft">
                    {c.summary || (c.transcript ? c.transcript.slice(0, 160) + "…" : "(no transcript)")}
                  </div>
                  <div className="app-row-sub">{fmtAge(c.started_at)} · {c.duration_seconds ? `${c.duration_seconds}s` : "—"}</div>
                </div>
                <div className="app-row-action">
                  <StatusPill status={c.status} />
                </div>
                <button
                  type="button"
                  className="leads-row-delete"
                  aria-label="Delete call"
                  title="Delete call"
                  onClick={() => deleteOne(c.id)}
                  disabled={busy}
                >
                  ✕
                </button>
              </div>
            );
          })
        )}
      </section>
    </>
  );
}
