import Link from "next/link";

import { getPersonaName } from "@/app/lib/persona";

import { fetchJson, type Call, type Page } from "../lib";
import CallsTable from "./CallsTable";

export default async function CallsPage({ searchParams }: { searchParams: Promise<{ provider?: string; q?: string }> }) {
  const params = await searchParams;
  const [data, persona] = await Promise.all([
    fetchJson<Page<Call>>("/calls/"),
    getPersonaName(),
  ]);
  let calls = data?.results ?? [];

  if (params.provider) calls = calls.filter((c) => c.provider === params.provider);
  if (params.q) {
    const q = params.q.toLowerCase();
    calls = calls.filter(
      (c) =>
        (c.from_number ?? "").toLowerCase().includes(q) ||
        (c.transcript ?? "").toLowerCase().includes(q) ||
        (c.summary ?? "").toLowerCase().includes(q),
    );
  }

  const totalDuration = calls.reduce((s, c) => s + (c.duration_seconds ?? 0), 0);
  const completed = calls.filter((c) => c.status === "completed").length;

  return (
    <>
      <div className="app-pagebar">
        <div>
          <h1>Calls</h1>
          <p>Voice and SMS interactions captured by {persona}.</p>
        </div>
        <div className="app-pagebar-actions">
          <Link href="/dashboard/test-call" className="btn btn-primary">▶ Test {persona}</Link>
        </div>
      </div>

      <div className="app-content">
        <div className="detail-grid">
          <div className="detail-card">
            <div className="detail-card-label">Total Calls</div>
            <div className="detail-card-value">{calls.length}</div>
          </div>
          <div className="detail-card">
            <div className="detail-card-label">Completed</div>
            <div className="detail-card-value">{completed}</div>
          </div>
          <div className="detail-card">
            <div className="detail-card-label">Total Duration</div>
            <div className="detail-card-value">{Math.round(totalDuration / 60)}m</div>
          </div>
        </div>

        <form className="app-toolbar" method="get">
          <input
            type="search"
            name="q"
            defaultValue={params.q ?? ""}
            placeholder="Search transcripts, numbers, summaries…"
            className="search-input"
          />
          <div className="tag-row" style={{ display: "flex" }}>
            {["all", "vapi", "twilio"].map((p) => {
              const active = (params.provider ?? "all") === p;
              const href = p === "all" ? "/dashboard/calls" : `/dashboard/calls?provider=${p}`;
              return (
                <Link key={p} href={href} className={`tag-chip ${active ? "active" : ""}`}>
                  {p}
                </Link>
              );
            })}
          </div>
        </form>

        <CallsTable calls={calls} defaultPersona={persona} />
      </div>
    </>
  );
}
