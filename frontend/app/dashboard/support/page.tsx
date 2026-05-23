import Link from "next/link";

import { fetchJson, fmtAge, type Page, type Ticket } from "../lib";

const STATUSES: { key: string; label: string }[] = [
  { key: "all", label: "All" },
  { key: "open", label: "Open" },
  { key: "waiting", label: "Waiting" },
  { key: "escalated", label: "Escalated" },
  { key: "resolved", label: "Resolved" },
];

const CHANNEL_GLYPH: Record<string, string> = {
  whatsapp: "🟢",
  sms: "💬",
  email: "✉",
  webchat: "◔",
};

export default async function SupportPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string; channel?: string }>;
}) {
  const params = await searchParams;
  const status = params.status && params.status !== "all" ? params.status : "";
  const channel = params.channel ?? "";

  const qs = new URLSearchParams();
  if (status) qs.set("status", status);
  if (channel) qs.set("channel", channel);
  const path = `/support/tickets/${qs.toString() ? `?${qs}` : ""}`;
  const data = await fetchJson<Page<Ticket>>(path);
  const tickets = data?.results ?? [];

  return (
    <>
      <div className="app-pagebar">
        <div>
          <h1>Support</h1>
          <p>Inbound support conversations from WhatsApp, SMS, email, and web chat.</p>
        </div>
        <div className="app-pagebar-actions">
          <Link href="/dashboard/settings?tab=ai" className="btn btn-ghost">
            Configure WhatsApp
          </Link>
        </div>
      </div>

      <div className="app-content">
        <form className="app-toolbar" method="get">
          <div className="tag-row" style={{ display: "flex" }}>
            {STATUSES.map((s) => {
              const active = (params.status ?? "all") === s.key;
              const href = s.key === "all"
                ? "/dashboard/support"
                : `/dashboard/support?status=${s.key}`;
              return (
                <Link key={s.key} href={href} className={`tag-chip ${active ? "active" : ""}`}>
                  {s.label}
                </Link>
              );
            })}
          </div>
        </form>

        {tickets.length === 0 ? (
          <div className="empty-card">
            <h3>No tickets yet</h3>
            <p>
              Once a customer messages your WhatsApp number (or another wired support channel),
              their conversation will land here. Configure your WhatsApp credentials in{" "}
              <Link href="/dashboard/settings?tab=ai">Settings → AI &amp; Keys</Link> and point
              Meta&apos;s webhook at <code>/api/support/webhooks/whatsapp/</code>.
            </p>
          </div>
        ) : (
          <article className="dash-card">
            <table className="dash-table">
              <thead>
                <tr>
                  <th></th>
                  <th>Customer</th>
                  <th>Last message</th>
                  <th>Status</th>
                  <th>Messages</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((t) => (
                  <tr key={t.id}>
                    <td title={t.channel}>{CHANNEL_GLYPH[t.channel] ?? "•"}</td>
                    <td>
                      <Link href={`/dashboard/support/${t.id}`} className="link">
                        {t.sender_name || t.sender_id}
                      </Link>
                      <div className="dim">{t.sender_id}</div>
                    </td>
                    <td>
                      <div className="ticket-preview">{t.last_message_preview}</div>
                    </td>
                    <td>
                      <span className={`pill pill-${t.status === "resolved" ? "disabled" : "active"}`}>
                        {t.status}
                      </span>
                      {t.human_only && <span className="pill pill-warn" style={{ marginLeft: 6 }}>human-only</span>}
                    </td>
                    <td>{t.message_count}</td>
                    <td>{fmtAge(t.last_message_at ?? t.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </article>
        )}
      </div>
    </>
  );
}
