"use client";

const API_URL = process.env.NEXT_PUBLIC_SUPPORT_API_URL ?? "http://localhost:9000";
const WS_URL = process.env.NEXT_PUBLIC_SUPPORT_WS_URL ?? "ws://localhost:9000";
const API_KEY = process.env.NEXT_PUBLIC_SUPPORT_API_KEY ?? "";

const STORAGE_KEY = "dropline.support";

type Stored = {
  visitor_token?: string;
  conversation_id?: string;
  name?: string;
  email?: string;
};

function load(): Stored {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "{}");
  } catch {
    return {};
  }
}

function save(s: Stored) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
}

function headers(extra: Record<string, string> = {}): HeadersInit {
  const state = load();
  const h: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Portal-Key": API_KEY,
    ...extra,
  };
  if (state.visitor_token) h["X-Visitor-Token"] = state.visitor_token;
  return h;
}

export type SupportMessage = {
  id: string;
  author_type: "visitor" | "staff" | "system";
  body: string;
  created_at: string;
  staff_username?: string;
};

export async function startConversation(opts: {
  body: string;
  name?: string;
  email?: string;
  subject?: string;
}): Promise<{ conversation_id: string; message: SupportMessage }> {
  const state = load();
  const res = await fetch(`${API_URL}/api/widget/start/`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({
      body: opts.body,
      name: opts.name ?? "",
      email: opts.email ?? "",
      subject: opts.subject ?? "",
      visitor_token: state.visitor_token,
    }),
  });
  if (!res.ok) throw new Error(await res.text());
  const data = (await res.json()) as {
    visitor_token: string;
    conversation_id: string;
    message: SupportMessage;
  };
  save({ visitor_token: data.visitor_token, conversation_id: data.conversation_id });
  return { conversation_id: data.conversation_id, message: data.message };
}

export async function sendMessage(body: string): Promise<SupportMessage> {
  const state = load();
  if (!state.conversation_id) {
    const r = await startConversation({ body });
    return r.message;
  }
  const res = await fetch(
    `${API_URL}/api/widget/conversations/${state.conversation_id}/messages/`,
    { method: "POST", headers: headers(), body: JSON.stringify({ body }) },
  );
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as SupportMessage;
}

/** Visitor closes their conversation. Backend broadcasts to staff. */
export async function closeConversation(): Promise<void> {
  const state = load();
  if (!state.conversation_id) return;
  try {
    await fetch(
      `${API_URL}/api/widget/conversations/${state.conversation_id}/close/`,
      { method: "POST", headers: headers() },
    );
  } catch {
    // best-effort
  }
}

export async function loadHistory(): Promise<SupportMessage[]> {
  const state = load();
  if (!state.conversation_id || !state.visitor_token) return [];
  const res = await fetch(
    `${API_URL}/api/widget/conversations/${state.conversation_id}/`,
    { headers: headers() },
  );
  if (!res.ok) {
    // stale state — clear and let next message restart
    save({});
    return [];
  }
  const data = (await res.json()) as { messages: SupportMessage[] };
  return data.messages || [];
}

export type LiveSocket = {
  close: () => void;
  isOpen: () => boolean;
};

/** Poll-based fallback for environments without WebSockets (e.g. Vercel).
 * Calls `loadHistory` every `intervalMs` and emits any new messages by id.
 */
export function pollLiveMessages(
  onMessage: (m: SupportMessage) => void,
  intervalMs = 4000,
): { stop: () => void } {
  let stopped = false;
  const seen = new Set<string>();
  let timer: ReturnType<typeof setTimeout> | null = null;

  async function tick() {
    if (stopped) return;
    try {
      const history = await loadHistory();
      for (const m of history) {
        if (seen.has(m.id)) continue;
        seen.add(m.id);
        onMessage(m);
      }
    } catch {
      // ignore — try again next interval
    }
    if (!stopped) {
      timer = setTimeout(tick, intervalMs);
    }
  }

  // Fire first poll immediately (catches a fast staff reply right after open)
  void tick();

  return {
    stop: () => {
      stopped = true;
      if (timer) clearTimeout(timer);
    },
  };
}

/**
 * Connect to the widget WebSocket. Auto-reconnects with exponential backoff
 * on unexpected close (network blips, server restart). Call `close()` to
 * stop reconnecting.
 */
export function connectLiveSocket(
  onMessage: (m: SupportMessage) => void,
  onStatusChange?: (status: "connecting" | "connected" | "closed") => void,
): LiveSocket {
  let ws: WebSocket | null = null;
  let stopped = false;
  let attempt = 0;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  function open() {
    const state = load();
    if (!state.conversation_id || !state.visitor_token || !API_KEY) return;
    const url = `${WS_URL}/ws/widget/${state.conversation_id}/?api_key=${encodeURIComponent(
      API_KEY,
    )}&visitor_token=${encodeURIComponent(state.visitor_token)}`;
    onStatusChange?.("connecting");
    console.log("[support] widget WS connecting", url);
    ws = new WebSocket(url);
    ws.onopen = () => {
      attempt = 0;
      console.log("[support] widget WS open");
      onStatusChange?.("connected");
    };
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === "message" && data.message) {
          onMessage(data.message);
        }
      } catch (err) {
        console.warn("[support] WS parse error", err);
      }
    };
    ws.onerror = (err) => {
      console.warn("[support] widget WS error", err);
    };
    ws.onclose = (ev) => {
      console.log("[support] widget WS closed", ev.code, ev.reason);
      onStatusChange?.("closed");
      ws = null;
      if (stopped) return;
      // Don't reconnect on auth failures (4401, 4403)
      if (ev.code === 4401 || ev.code === 4403) return;
      attempt = Math.min(attempt + 1, 6);
      const delay = Math.min(1000 * 2 ** attempt, 15000);
      reconnectTimer = setTimeout(open, delay);
    };
  }

  open();

  return {
    close: () => {
      stopped = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      ws?.close();
      ws = null;
    },
    isOpen: () => ws?.readyState === WebSocket.OPEN,
  };
}

export function hasLiveSession(): boolean {
  const s = load();
  return Boolean(s.conversation_id && s.visitor_token);
}

export function resetLiveSession() {
  // Keep name + email so a returning visitor doesn't get re-prompted.
  const { name, email } = load();
  save({ name, email });
}

export function getStoredIdentity(): { name: string; email: string } {
  const s = load();
  return { name: s.name ?? "", email: s.email ?? "" };
}

export function setStoredIdentity(name: string, email: string) {
  const s = load();
  save({ ...s, name, email });
}
