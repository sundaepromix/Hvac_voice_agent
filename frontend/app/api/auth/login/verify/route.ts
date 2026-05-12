import { NextResponse } from "next/server";

import { API_URL, SESSION_COOKIE, extractSessionId } from "@/app/lib/api";

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const login_token = (body.login_token ?? "").trim();
  const code = (body.code ?? "").trim();

  if (!login_token || !code) {
    return NextResponse.json({ detail: "Code is required." }, { status: 400 });
  }

  const upstream = await fetch(`${API_URL}/auth/login/verify/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ login_token, code }),
    cache: "no-store",
  });

  const data = await upstream.json().catch(() => ({}));
  if (!upstream.ok) {
    return NextResponse.json(data, { status: upstream.status });
  }

  const sessionid = extractSessionId(upstream.headers.get("set-cookie"));
  const res = NextResponse.json(data);
  if (sessionid) {
    res.cookies.set({
      name: SESSION_COOKIE,
      value: sessionid,
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: 60 * 60 * 24 * 14,
    });
  }
  return res;
}
