"use client";

// What the agent handles, shown as a continuously scrolling pill strip with
// ✦ dividers (vertical-agnostic — these are capabilities, not one industry).
const SERVICES = [
  "Answer inbound calls 24/7",
  "Speed-to-lead callbacks",
  "Book & reschedule appointments",
  "Qualify & score leads",
  "Scheduled follow-ups",
  "Lead reactivation",
  "Appointment reminders",
  "Answer FAQs from your knowledge base",
  "Warm-transfer to your team",
  "SMS & WhatsApp confirmations",
  "Capture custom intake fields",
  "Post-call summaries",
];

export default function ServicesStrip() {
  // Duplicate the list so the marquee loops seamlessly.
  const loop = [...SERVICES, ...SERVICES];
  return (
    <div className="services-strip" aria-label="What the agent handles">
      <div className="services-track">
        {loop.map((s, i) => (
          <span className="services-item" key={i}>
            <span className="services-pill">{s}</span>
            <span className="services-div" aria-hidden>✦</span>
          </span>
        ))}
      </div>
    </div>
  );
}
