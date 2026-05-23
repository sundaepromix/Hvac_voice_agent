export type Lang = "en" | "es" | "de" | "fr" | "it" | "pt" | "nl" | "zh" | "ja" | "ar";

export const LANGS: { code: Lang; label: string; native: string; flag: string; rtl?: boolean }[] = [
  { code: "en", label: "English", native: "English", flag: "🇬🇧" },
  { code: "es", label: "Spanish", native: "Español", flag: "🇪🇸" },
  { code: "de", label: "German", native: "Deutsch", flag: "🇩🇪" },
  { code: "fr", label: "French", native: "Français", flag: "🇫🇷" },
  { code: "it", label: "Italian", native: "Italiano", flag: "🇮🇹" },
  { code: "pt", label: "Portuguese", native: "Português", flag: "🇵🇹" },
  { code: "nl", label: "Dutch", native: "Nederlands", flag: "🇳🇱" },
  { code: "zh", label: "Chinese", native: "中文", flag: "🇨🇳" },
  { code: "ja", label: "Japanese", native: "日本語", flag: "🇯🇵" },
  { code: "ar", label: "Arabic", native: "العربية", flag: "🇸🇦", rtl: true },
];

export const LANG_COOKIE = "hl-lang";

export function isLang(s: string | undefined | null): s is Lang {
  return !!s && LANGS.some((l) => l.code === s);
}
