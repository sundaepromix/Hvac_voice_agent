// Single source of truth for the booking link. Set NEXT_PUBLIC_BOOKING_URL to
// override; otherwise this default is used so every "Book a demo" button works.
export const BOOKING_URL =
  process.env.NEXT_PUBLIC_BOOKING_URL || "https://calendar.app.google/XcZqFGqbDfCtvsWdA";

// True when the booking link is an external scheduler rather than a fallback
// internal route — used to decide target="_blank".
export const BOOKING_IS_EXTERNAL = BOOKING_URL.startsWith("http");

// Calendly exposes an inline-embed widget; other schedulers (e.g. Google
// Calendar appointment links) don't iframe reliably, so we show a CTA instead.
export const BOOKING_IS_CALENDLY = BOOKING_URL.includes("calendly.com");
