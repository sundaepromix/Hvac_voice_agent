import Link from "next/link";

import { fetchJson, type TicketDetail } from "../../lib";
import TicketThread from "./TicketThread";

export default async function TicketDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const ticket = await fetchJson<TicketDetail>(`/support/tickets/${id}/`);

  if (!ticket) {
    return (
      <>
        <div className="app-pagebar">
          <div>
            <h1>Ticket not found</h1>
          </div>
        </div>
        <div className="app-content">
          <div className="empty-card">
            <p>
              <Link href="/dashboard/support">← Back to Support</Link>
            </p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="app-pagebar">
        <div>
          <h1>
            {ticket.sender_name || ticket.sender_id}
            <span className="dim" style={{ marginLeft: 10, fontSize: 13, fontWeight: 400 }}>
              · {ticket.channel}
            </span>
          </h1>
          <p>{ticket.sender_id}</p>
        </div>
        <div className="app-pagebar-actions">
          <Link href="/dashboard/support" className="btn btn-ghost">← Back</Link>
        </div>
      </div>

      <div className="app-content">
        <TicketThread ticket={ticket} />
      </div>
    </>
  );
}
