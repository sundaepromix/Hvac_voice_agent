import type { Lang } from "./langs";
import { en as enFromShared, type Dict as SharedDict } from "./strings-en";
import { es } from "./locales/es";
import { de } from "./locales/de";
import { fr } from "./locales/fr";
import { it } from "./locales/it";
import { pt } from "./locales/pt";
import { nl } from "./locales/nl";
import { zh } from "./locales/zh";
import { ja } from "./locales/ja";
import { ar } from "./locales/ar";
import { landingExtra } from "./locales/_landing";

type Dict = SharedDict;

export const en: Dict = enFromShared;

// Landing-rebuild + live-voice + booking copy is merged over each base locale
// so the new sections render translated instead of falling back to English.
export const DICTS: Record<Lang, Dict> = {
  en,
  es: { ...es, ...landingExtra.es },
  de: { ...de, ...landingExtra.de },
  fr: { ...fr, ...landingExtra.fr },
  it: { ...it, ...landingExtra.it },
  pt: { ...pt, ...landingExtra.pt },
  nl: { ...nl, ...landingExtra.nl },
  zh: { ...zh, ...landingExtra.zh },
  ja: { ...ja, ...landingExtra.ja },
  ar: { ...ar, ...landingExtra.ar },
};

export function tFor(lang: Lang, key: string): string {
  const dict = DICTS[lang] || en;
  return dict[key] ?? en[key] ?? key;
}
