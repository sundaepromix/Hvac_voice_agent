"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { getAdminUrl } from "../lib/adminUrl";

type Counts = { leads: number; calls: number; quotes: number; businesses: number; tickets: number };

const buildNavOps = (personaName: string): { href: string; label: string; key: keyof Counts | null; icon: React.ReactNode }[] => [
  {
    href: "/dashboard",
    label: "Overview",
    key: null,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="9" /><rect x="14" y="3" width="7" height="5" /><rect x="14" y="12" width="7" height="9" /><rect x="3" y="16" width="7" height="5" /></svg>
    ),
  },
  {
    href: "/dashboard/leads",
    label: "Leads",
    key: "leads",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-6l-2 3h-4l-2-3H2" /><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" /></svg>
    ),
  },
  {
    href: "/dashboard/calls",
    label: "Calls",
    key: "calls",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" /></svg>
    ),
  },
  {
    href: "/dashboard/test-call",
    label: `Test ${personaName}`,
    key: null,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3" /></svg>
    ),
  },
  {
    href: "/dashboard/quotes",
    label: "Quotes",
    key: "quotes",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></svg>
    ),
  },
  {
    href: "/dashboard/customers",
    label: "Customers",
    key: null,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>
    ),
  },
];

const NAV_ADMIN: { href: string; label: string; key: keyof Counts | null; icon: React.ReactNode }[] = [
  {
    href: "/dashboard/support",
    label: "Support",
    key: "tickets",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" /></svg>
    ),
  },
  {
    href: "/dashboard/settings",
    label: "Settings",
    key: null,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg>
    ),
  },
];

type SidebarUser = { name: string; business: string };

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export default function Sidebar({
  counts,
  user,
  personaName = "Mary",
}: {
  counts: Counts;
  user?: SidebarUser;
  personaName?: string;
}) {
  const pathname = usePathname();
  const isActive = (href: string) =>
    href === "/dashboard" ? pathname === href : pathname.startsWith(href);
  const displayName = user?.name?.trim() || "Signed in";
  const displayBusiness = user?.business?.trim() || "No business yet";
  const navOps = buildNavOps(personaName);

  return (
    <aside className="app-sidebar">
      <Link href="/" className="brand" title="Back to landing">
        <span className="brand-mark">H</span>
        <span>Workflow Auth</span>
      </Link>

      <p className="sidebar-section">Operations</p>
      {navOps.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={`sidebar-link ${isActive(item.href) ? "active" : ""}`}
        >
          {item.icon}
          <span>{item.label}</span>
          {item.key && counts[item.key] > 0 && (
            <span className="badge">{counts[item.key]}</span>
          )}
        </Link>
      ))}

      <p className="sidebar-section">Admin</p>
      {NAV_ADMIN.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={`sidebar-link ${isActive(item.href) ? "active" : ""}`}
        >
          {item.icon}
          <span>{item.label}</span>
          {item.key && counts[item.key] > 0 && (
            <span className="badge">{counts[item.key]}</span>
          )}
        </Link>
      ))}
      <a
        href={getAdminUrl()}
        target="_blank"
        rel="noreferrer"
        className="sidebar-link"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" /></svg>
        <span>Django admin</span>
      </a>

      <div className="sidebar-bottom">
        <div className="sidebar-user">
          <span className="avatar">{initials(displayName)}</span>
          <div className="sidebar-user-meta">
            <div className="sidebar-user-name">{displayName}</div>
            <div className="sidebar-user-role">{displayBusiness}</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
