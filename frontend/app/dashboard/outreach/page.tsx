import { getPersonaName } from "@/app/lib/persona";

import { fetchJson } from "../lib";
import OutreachActions from "./OutreachActions";

type OutboundTask = {
  id: number;
  kind: string;
  to_number: string;
  contact_name: string;
  campaign: string;
  status: string;
  scheduled_for: string;
  attempts: number;
  max_attempts: number;
  last_error: string;
  call_status: string;
};

const KIND_LABEL: Record<string, string> = {
  speed_to_lead: "Speed-to-lead",
  follow_up: "Follow-up",
  reactivation: "Reactivation",
  reminder: "Reminder",
};

function fmtWhen(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default async function OutreachPage() {
  const [tasks, persona] = await Promise.all([
    fetchJson<OutboundTask[]>("/calls/outbound/"),
    getPersonaName(),
  ]);
  const list = tasks ?? [];
  const pending = list.filter((t) => t.status === "pending").length;
  const placed = list.filter((t) => t.status === "completed").length;
  const failed = list.filter((t) => t.status === "failed").length;

  return (
    <>
      <div className="app-pagebar">
        <div>
          <h1>Outreach</h1>
          <p>
            Outbound calls {persona} places — speed-to-lead, follow-ups, reactivation, and reminders.
          </p>
        </div>
        <OutreachActions />
      </div>

      <div className="app-content">
        <div className="detail-grid">
          <div className="detail-card">
            <div className="detail-card-label">Queued</div>
            <div className="detail-card-value">{pending}</div>
          </div>
          <div className="detail-card">
            <div className="detail-card-label">Placed</div>
            <div className="detail-card-value">{placed}</div>
          </div>
          <div className="detail-card">
            <div className="detail-card-label">Failed</div>
            <div className="detail-card-value">{failed}</div>
          </div>
        </div>

        {list.length === 0 ? (
          <p style={{ color: "var(--muted, #667)", marginTop: 16 }}>
            No outbound calls yet. New non-voice leads trigger speed-to-lead callbacks, drafted
            quotes schedule follow-ups, and the button above starts a reactivation campaign over
            cold leads.
          </p>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Contact</th>
                  <th>Number</th>
                  <th>Status</th>
                  <th>Scheduled</th>
                  <th>Attempts</th>
                </tr>
              </thead>
              <tbody>
                {list.map((t) => (
                  <tr key={t.id}>
                    <td>{KIND_LABEL[t.kind] ?? t.kind}</td>
                    <td>{t.contact_name || "—"}</td>
                    <td>{t.to_number}</td>
                    <td>
                      <span className="tag-chip">{t.status}</span>
                      {t.call_status ? <span className="dash-card-meta"> · {t.call_status}</span> : null}
                    </td>
                    <td>{fmtWhen(t.scheduled_for)}</td>
                    <td>
                      {t.attempts}/{t.max_attempts}
                      {t.last_error ? <span className="dash-card-meta"> · {t.last_error}</span> : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
