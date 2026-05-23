/**
 * Client-safe helper for building Django admin URLs. Lives outside api.ts so
 * client components can import it without pulling in next/headers.
 */
export function getAdminUrl(path: string = ""): string {
  const explicit = process.env.NEXT_PUBLIC_ADMIN_URL;
  let base: string;
  if (explicit) {
    base = explicit.replace(/\/+$/, "");
  } else {
    const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
    try {
      const u = new URL(api);
      base = `${u.origin}/admin`;
    } catch {
      base = "http://localhost:8000/admin";
    }
  }
  if (!path) return `${base}/`;
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${base}${suffix}`;
}
