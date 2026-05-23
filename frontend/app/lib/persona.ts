import { apiJson } from "./api";

type BusinessPersona = { name: string; voice_persona: string };
type BusinessPage = { results: BusinessPersona[] };

export async function getPersonaName(): Promise<string> {
  const page = await apiJson<BusinessPage>("/businesses/");
  const raw = page?.results?.[0]?.voice_persona?.trim();
  return raw || "Mary";
}
