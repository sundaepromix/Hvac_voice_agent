"use client";

import { useEffect } from "react";

// Lightweight inline Calendly embed. Loads the official widget script once and
// lets it hydrate the .calendly-inline-widget div via the data-url attribute.
export default function CalendlyInline({ url }: { url: string }) {
  useEffect(() => {
    const id = "calendly-widget-script";
    if (document.getElementById(id)) return;
    const s = document.createElement("script");
    s.id = id;
    s.src = "https://assets.calendly.com/assets/external/widget.js";
    s.async = true;
    document.body.appendChild(s);
  }, []);

  return (
    <div
      className="calendly-inline-widget"
      data-url={`${url}?hide_gdpr_banner=1`}
      style={{ minWidth: "320px", height: "640px" }}
    />
  );
}
