import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { apiFetch, apiJson, getCurrentUser } from "@/app/lib/api";

import AutoRefresh from "./AutoRefresh";
import Sidebar from "./Sidebar";
import { DashGlobalTopbar } from "./Topbar";

type BusinessLite = { name: string; voice_persona?: string };
type BusinessPage = { results: BusinessLite[] };

export const metadata: Metadata = {
  title: "Dashboard",
  robots: { index: false, follow: false, nocache: true },
};

async function fetchCount(path: string): Promise<number> {
  try {
    const res = await apiFetch(path);
    if (!res.ok) return 0;
    const data = await res.json();
    return data?.count ?? 0;
  } catch {
    return 0;
  }
}

// In local dev we don't gate the dashboard behind login so the pages can be
// browsed freely. Production (NODE_ENV=production) still requires a session.
function devFallbackUser() {
  if (process.env.NODE_ENV === "production") return null;
  return { id: 0, username: "demo", email: "", first_name: "Demo", is_staff: true };
}

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const user = (await getCurrentUser()) ?? devFallbackUser();
  if (!user) redirect("/login?next=/dashboard");

  const [leads, calls, quotes, businesses, tickets, bizPage] = await Promise.all([
    fetchCount("/leads/"),
    fetchCount("/calls/"),
    fetchCount("/quotes/"),
    fetchCount("/businesses/"),
    fetchCount("/support/tickets/?status=open"),
    apiJson<BusinessPage>("/businesses/"),
  ]);
  const sidebarName =
    [user.first_name, ""].filter(Boolean).join(" ").trim() ||
    user.username ||
    user.email ||
    "Signed in";
  const sidebarBusiness = bizPage?.results?.[0]?.name ?? "";
  const personaName = (bizPage?.results?.[0]?.voice_persona || "").trim() || "Mary";
  return (
    <div className="app-shell">
      <AutoRefresh />
      <Sidebar
        counts={{ leads, calls, quotes, businesses, tickets }}
        user={{ name: sidebarName, business: sidebarBusiness }}
        personaName={personaName}
      />
      <div className="app-main">
        <DashGlobalTopbar user={user} />
        {children}
      </div>
    </div>
  );
}
