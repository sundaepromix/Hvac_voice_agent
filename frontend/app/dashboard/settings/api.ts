export async function patchBusiness(
  id: number,
  patch: Record<string, unknown>,
): Promise<{ ok: boolean; error?: string; id?: number }> {
  const isCreate = !id;
  const url = isCreate ? `/api/proxy/businesses/` : `/api/proxy/businesses/${id}/`;
  const method = isCreate ? "POST" : "PATCH";
  try {
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    });
    if (!res.ok) {
      const text = await res.text();
      return { ok: false, error: text || `HTTP ${res.status}` };
    }
    if (isCreate) {
      const body = (await res.json().catch(() => null)) as { id?: number } | null;
      return { ok: true, id: body?.id };
    }
    return { ok: true, id };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}
