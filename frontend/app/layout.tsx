import type { Metadata, Viewport } from "next";
import { Inter, Fraunces } from "next/font/google";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";
import { I18nProvider } from "./lib/i18n";

const inter = Inter({ subsets: ["latin"], display: "swap", variable: "--font-inter" });
const fraunces = Fraunces({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-fraunces",
  weight: "variable",
  style: ["normal", "italic"],
  axes: ["SOFT", "opsz"],
});

const SITE_URL = "https://workflowauth.com";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "WorkflowAuth — AI voice agent that answers every call and chases every lead",
    template: "%s · WorkflowAuth",
  },
  description:
    "WorkflowAuth answers your inbound calls and calls leads back — speed-to-lead, follow-ups, and reactivation. A 24/7 AI voice agent for any business that lives on the phone.",
  applicationName: "WorkflowAuth",
  generator: "Next.js",
  authors: [{ name: "Promise Sunday", url: "https://workflowauth.com" }],
  creator: "Promise Sunday",
  publisher: "WorkflowAuth",
  keywords: [
    "AI voice agent",
    "AI phone answering",
    "speed to lead",
    "lead reactivation",
    "outbound calling AI",
    "AI receptionist",
    "Vapi",
    "Twilio AI",
    "missed call automation",
    "open source AI voice agent",
  ],
  category: "business",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    siteName: "WorkflowAuth",
    title: "WorkflowAuth — AI voice agent for inbound + outbound calls",
    description:
      "Answer every call. Chase every lead. Speed-to-lead, follow-ups, and reactivation — around the clock.",
    url: SITE_URL,
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "WorkflowAuth — AI voice agent for inbound + outbound calls",
    description:
      "Answer every call. Chase every lead. Speed-to-lead, follow-ups, and reactivation — around the clock.",
    site: "@workflowauth",
    creator: "@workflowauth",
  },
  appleWebApp: {
    capable: true,
    title: "WorkflowAuth",
    statusBarStyle: "black-translucent",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  },
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" },
    ],
    apple: [{ url: "/icon.svg", type: "image/svg+xml" }],
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fbf6ee" },
    { media: "(prefers-color-scheme: dark)",  color: "#0b0b0f" },
  ],
};

const ORG_JSONLD = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "WorkflowAuth",
  url: SITE_URL,
  logo: `${SITE_URL}/icon.svg`,
  description:
    "Open-source 24/7 AI voice agent — answers inbound calls and places outbound calls for speed-to-lead, follow-ups, reactivation, and reminders.",
  founder: {
    "@type": "Person",
    name: "Promise Sunday",
    url: "https://workflowauth.com",
  },
  sameAs: [
    "https://github.com/yourname/dropline",
    "https://workflowauth.com",
  ],
};

const WEBSITE_JSONLD = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "WorkflowAuth",
  url: SITE_URL,
  inLanguage: "en",
  publisher: { "@type": "Organization", name: "WorkflowAuth" },
};

const THEME_INIT = `(function(){try{var s=localStorage.getItem('hl-theme');var m=window.matchMedia('(prefers-color-scheme: dark)').matches;var t=s||(m?'dark':'light');document.documentElement.setAttribute('data-theme',t);}catch(e){}})();`;

const LANG_INIT = `(function(){try{var RTL={ar:1};var s=localStorage.getItem('hl-lang');if(!s){var n=(navigator.language||'en').slice(0,2).toLowerCase();var supported={en:1,es:1,de:1,fr:1,it:1,pt:1,nl:1,zh:1,ja:1,ar:1};s=supported[n]?n:'en';}document.documentElement.setAttribute('lang',s);document.documentElement.setAttribute('dir',RTL[s]?'rtl':'ltr');if(s!=='en'){var v='/en/'+s;var host=location.hostname;var parts=host.split('.');var root=parts.length>1?'.'+parts.slice(-2).join('.'):host;var exp='expires=Fri, 31 Dec 9999 23:59:59 GMT';document.cookie='googtrans='+v+'; path=/; '+exp;document.cookie='googtrans='+v+'; domain='+host+'; path=/; '+exp;document.cookie='googtrans='+v+'; domain='+root+'; path=/; '+exp;window.__hlNeedsTranslate=true;}}catch(e){}})();`;

const GTRANSLATE_INIT = `function googleTranslateElementInit(){try{new google.translate.TranslateElement({pageLanguage:'en',includedLanguages:'en,es,de,fr,it,pt,nl,zh-CN,ja,ar',autoDisplay:false,layout:google.translate.TranslateElement.InlineLayout.SIMPLE},'google_translate_element');}catch(e){}}`;

const GTRANSLATE_LOAD = `(function(){if(window.__hlNeedsTranslate){var s=document.createElement('script');s.src='//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';s.async=true;document.body.appendChild(s);}})();`;

const SW_INIT = `if('serviceWorker' in navigator && location.pathname.startsWith('/dashboard')){window.addEventListener('load',function(){navigator.serviceWorker.register('/sw.js').catch(function(){});});}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${fraunces.variable}`} suppressHydrationWarning>
      <body>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT }} />
        <script dangerouslySetInnerHTML={{ __html: LANG_INIT }} />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(ORG_JSONLD) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(WEBSITE_JSONLD) }}
        />
        <I18nProvider>{children}</I18nProvider>
        <Analytics />
        <div id="google_translate_element" aria-hidden style={{ display: "none" }} />
        <script dangerouslySetInnerHTML={{ __html: GTRANSLATE_INIT }} />
        <script dangerouslySetInnerHTML={{ __html: GTRANSLATE_LOAD }} />
        <script dangerouslySetInnerHTML={{ __html: SW_INIT }} />
      </body>
    </html>
  );
}
