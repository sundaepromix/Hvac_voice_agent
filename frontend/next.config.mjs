import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// When running `next dev`/`next build` directly from frontend/ (i.e. not via
// docker-compose, which injects the root .env through env_file), Next only reads
// env files inside frontend/. Pull the repo-root .env's NEXT_PUBLIC_* values in
// so the browser bundle gets the booking URL + Vapi keys without duplicating
// them. Platform/compose env always wins (we never overwrite an existing value).
try {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const rootEnv = path.join(here, "..", ".env");
  const txt = fs.readFileSync(rootEnv, "utf8");
  for (const line of txt.split("\n")) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
    if (!m) continue;
    const [, key, rawVal] = m;
    if (!key.startsWith("NEXT_PUBLIC_") || process.env[key]) continue;
    let val = rawVal.trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    process.env[key] = val;
  }
} catch {
  // No root .env (e.g. Vercel) — rely on platform-provided env vars.
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: "http://backend:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
