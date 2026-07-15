"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

// Keeps the server-rendered dashboard fresh without SSE: re-fetch the current
// route's server components on an interval while the tab is visible, and
// immediately when the user returns to the tab. router.refresh() preserves
// client state (scroll, inputs) — no visible reload.
export default function AutoRefresh({ intervalMs = 20000 }: { intervalMs?: number }) {
  const router = useRouter();

  useEffect(() => {
    const tick = () => {
      if (document.visibilityState === "visible") router.refresh();
    };
    const id = setInterval(tick, intervalMs);
    document.addEventListener("visibilitychange", tick);
    return () => {
      clearInterval(id);
      document.removeEventListener("visibilitychange", tick);
    };
  }, [router, intervalMs]);

  return null;
}
