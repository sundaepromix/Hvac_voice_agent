import { getT } from "../lib/i18n-server";
import { MarketingFooter, MarketingTopbar } from "../MarketingShell";

import { FAQS } from "./data";
import FaqList from "./FaqList";

export const metadata = {
  title: "FAQ",
  description: "Common questions about Workflow Auth — pricing, setup, integrations, security, and more.",
  alternates: { canonical: "/faq" },
  openGraph: {
    title: "Workflow Auth · FAQ",
    description: "Common questions about Workflow Auth — pricing, setup, integrations, security, and more.",
    url: "/faq",
  },
};

const FAQ_JSONLD = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: FAQS.map((f) => ({
    "@type": "Question",
    name: f.q,
    acceptedAnswer: { "@type": "Answer", text: f.aText },
  })),
};

export default async function FaqPage() {
  const { t } = await getT();
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(FAQ_JSONLD) }}
      />
      <MarketingTopbar />
      <main>
        <section className="shell hero hero-tight">
          <span className="hero-meet">
            <span className="hero-meet-avatar">?</span>
            <span>{t("faq.heroEyebrow")}</span>
          </span>
          <h1 className="hero-title">
            {t("faq.heroT1")}<br />
            <span className="hero-title-em">{t("faq.heroT2")}</span>
          </h1>
          <p className="hero-sub">{t("faq.heroSub")}</p>
        </section>

        <section className="shell section-tight">
          <FaqList items={FAQS} />
        </section>

        <section className="shell section-tight">
          <div className="final-cta">
            <h2 className="final-cta-title">{t("faq.finalT")}</h2>
            <p className="final-cta-sub">{t("faq.finalSub")}</p>
            <div className="final-cta-actions">
              <a
                href="/contact"
                target="_blank"
                rel="noreferrer"
                className="btn btn-onDark btn-lg"
              >
                {t("btn.bookDemo")} <span aria-hidden>→</span>
              </a>
            </div>
          </div>
        </section>

        <MarketingFooter />
      </main>
    </>
  );
}
