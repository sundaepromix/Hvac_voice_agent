import { cookies } from "next/headers";

import { DICTS, tFor } from "./dicts";
import { isLang, LANG_COOKIE, type Lang } from "./langs";

export async function getLang(): Promise<Lang> {
  const c = await cookies();
  const v = c.get(LANG_COOKIE)?.value;
  return isLang(v) ? v : "en";
}

export async function getT(): Promise<{ lang: Lang; t: (k: string) => string }> {
  const lang = await getLang();
  return {
    lang,
    t: (k: string) => tFor(lang, k),
  };
}

export { DICTS };
