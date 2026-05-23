"use client";

import { useEffect, useRef, useState } from "react";

import { useI18n } from "./lib/i18n";

export default function StatsBand() {
  const { t } = useI18n();
  const ref = useRef<HTMLDivElement | null>(null);
  const [seen, setSeen] = useState(false);
  const [n1, setN1] = useState(0);
  const [n2, setN2] = useState(0);
  const [n3, setN3] = useState(0);

  useEffect(() => {
    if (!ref.current) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setSeen(true);
          obs.disconnect();
        }
      },
      { threshold: 0.35 },
    );
    obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    if (!seen) return;
    const start = performance.now();
    const dur = 1500;
    let raf = 0;
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / dur);
      const e = 1 - Math.pow(1 - p, 3);
      setN1(Math.round(100 * e));
      setN2(Math.round(43 * e));
      setN3(Math.round(38 * e));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [seen]);

  return (
    <section className="shell section" id="impact">
      <div className="stats-band" ref={ref}>
        <div>
          <span className="section-flourish" style={{ color: "rgba(255,255,255,0.55)" }}>
            {t("stats.eyebrow.short")}
          </span>
          <h2 className="stats-band-title">{t("stats.title.short")}</h2>
          <p className="stats-band-body">{t("stats.body.short")}</p>
          <ul>
            <li>{t("stats.li1.short")}</li>
            <li>{t("stats.li2.short")}</li>
            <li>{t("stats.li3.short")}</li>
          </ul>
        </div>
        <div className="stats-band-right">
          <div className="stats-card night">
            <div className="stats-card-num">
              {n1}
              <span className="stats-card-suffix">%</span>
            </div>
            <div className="stats-card-label">{t("stats.cardA.label")}</div>
          </div>
          <div className="stats-card ember">
            <div className="stats-card-num">
              {n2}
              <span className="stats-card-suffix">s</span>
            </div>
            <div className="stats-card-label">{t("stats.cardB.label")}</div>
          </div>
          <div className="stats-card">
            <div className="stats-card-num">
              {n3}
              <span className="stats-card-suffix">s</span>
            </div>
            <div className="stats-card-label">{t("stats.cardC.label")}</div>
          </div>
        </div>
      </div>
    </section>
  );
}
