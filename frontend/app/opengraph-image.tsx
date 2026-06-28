import { ImageResponse } from "next/og";

export const runtime = "nodejs";
export const alt = "WorkflowAuth — AI voice agent for inbound + outbound calls";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          background: "linear-gradient(135deg, #0b0b0f 0%, #1a1410 60%, #2a1810 100%)",
          color: "#fbf6ee",
          display: "flex",
          flexDirection: "column",
          padding: "72px 88px",
          fontFamily: "serif",
          position: "relative",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            fontSize: 28,
            color: "#f4a261",
            letterSpacing: 1,
          }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: "#f4a261",
              color: "#0b0b0f",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 22,
              fontWeight: 700,
            }}
          >
            W
          </div>
          <span style={{ fontWeight: 600 }}>WorkflowAuth</span>
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            marginTop: "auto",
            gap: 28,
          }}
        >
          <div
            style={{
              fontSize: 84,
              lineHeight: 1.05,
              fontWeight: 600,
              letterSpacing: -2,
              maxWidth: 980,
              display: "flex",
              flexWrap: "wrap",
            }}
          >
            Answer every call. Chase every lead.
          </div>
          <div
            style={{
              fontSize: 30,
              color: "#cdbfae",
              maxWidth: 920,
              lineHeight: 1.35,
              fontFamily: "sans-serif",
            }}
          >
            Speed-to-lead, follow-ups, and reactivation — around the clock, for any business on the phone.
          </div>
          <div
            style={{
              display: "flex",
              gap: 16,
              fontSize: 22,
              color: "#9c8b78",
              fontFamily: "sans-serif",
            }}
          >
            <span>Open-source · AGPL-3.0</span>
            <span>·</span>
            <span></span>
          </div>
        </div>
      </div>
    ),
    { ...size }
  );
}
