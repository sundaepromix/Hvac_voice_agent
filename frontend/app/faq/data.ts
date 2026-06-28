export type FaqCategory = "Setup" | "Product" | "Pricing" | "Security";

export type FaqItem = {
  q: string;
  category: FaqCategory;
  aText: string;
  aHtml?: string;
};

export const FAQS: FaqItem[] = [
  {
    q: "Can I have my own version of Mary for my business?",
    category: "Product",
    aText:
      "Yes. Mary is just the demo voice — your WorkflowAuth agent runs on your own script, voice, hours, and pricing. You choose what it captures, how it answers, and when it calls leads back. It works for any business that lives on the phone.",
  },
  {
    q: "How long does it take to deploy?",
    category: "Setup",
    aText:
      "About 30 minutes for the basics — your hours, intake questions, knowledge base, and a phone number to forward. Tuning the voice and follow-up rules to your exact business is a few hours of iteration after that.",
  },
  {
    q: "Does it actually write to my CRM during calls?",
    category: "Product",
    aText:
      "Yes. As the agent talks, it captures the lead, scores it, books the appointment, and pushes a clean record to your CRM in real time — not after the call. Every fact it learns is persisted as it goes.",
  },
  {
    q: "What platforms does it integrate with?",
    category: "Setup",
    aText:
      "Phone via Retell or Vapi, with SMS and WhatsApp through Twilio. CRMs: HubSpot, Pipedrive, Salesforce, Zoho. Anything else connects through n8n or a Python integration against our REST API — every interaction is just a Lead row we can route anywhere.",
  },
  {
    q: "Do I need technical skills or developers?",
    category: "Setup",
    aText:
      "No. Everything is configured from the dashboard — your questions, voice, hours, transfer rules, and follow-up timing. If you'd rather not touch it at all, we'll set the whole thing up for you.",
  },
  {
    q: "Does it handle outbound calls too?",
    category: "Product",
    aText:
      "Yes — that's half the point. It calls new leads back within seconds (speed-to-lead), runs scheduled follow-ups, reactivates cold leads, and places appointment reminders — automatically or with one tap from the dashboard.",
  },
  {
    q: "What happens if it can't answer something?",
    category: "Product",
    aText:
      "It can warm-transfer to a teammate on conditions you set, or politely take a detailed message, file it as a scored lead, and notify whoever's on call. No caller is left hanging.",
  },
  {
    q: "Does it sound like a robot?",
    category: "Product",
    aText:
      "No — it runs on the latest neural voices (configurable). You pick the voice; most callers can't tell it's AI in a short call. You can even clone your owner's voice.",
  },
  {
    q: "Is my data secure?",
    category: "Security",
    aText:
      "All data is encrypted in transit (TLS 1.3) and at rest (AES-256). We do not train on your customer data, and your call records and leads are never shared or sold.",
  },
  {
    q: "How is pricing structured?",
    category: "Pricing",
    aText:
      "It's a done-for-you service: we build, deploy, and run your AI front desk for a simple monthly fee. Book a 15-minute call and we'll scope it to your business and share exact pricing.",
  },
  {
    q: "Can I try it before paying?",
    category: "Pricing",
    aText:
      "Yes. We run a short pilot on your real calls so you can hear Mary in action before any invoice. Book a demo to get started.",
  },
];
