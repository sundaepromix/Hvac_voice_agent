"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

import { useI18n } from "./lib/i18n";

type Scene = 0 | 1 | 2 | 3;

const SCENE_COUNT = 4;

export default function MissedCallStory() {
  const { t } = useI18n();
  const [active, setActive] = useState<Scene>(0);
  const beatRefs = useRef<Array<HTMLDivElement | null>>([]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (!visible) return;
        const idx = Number(visible.target.getAttribute("data-scene"));
        if (!Number.isNaN(idx)) setActive(idx as Scene);
      },
      { rootMargin: "-40% 0px -40% 0px", threshold: [0, 0.25, 0.5, 0.75, 1] }
    );
    beatRefs.current.forEach((el) => el && observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <section className="story-wrap" id="story">
      <div className="shell story-head">
        <span className="section-flourish">{t("story.eyebrow")}</span>
        <h2 className="section-title">
          {t("story.title1")} <em className="hero-title-em">{t("story.title2")}</em>
        </h2>
        <p className="section-sub">{t("story.sub")}</p>
      </div>

      <div className="story-stage-wrap">
        <div className="shell story-stage-grid">
          <div className="story-beats">
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                ref={(el) => { beatRefs.current[i] = el; }}
                data-scene={i}
                className={`story-beat ${active === i ? "is-active" : ""}`}
              >
                <span className="story-beat-num">0{i + 1}</span>
                <h3 className="story-beat-title">{t(`story.s${i + 1}.beat`)}</h3>
                <p className="story-beat-body">{t(`story.s${i + 1}.body`)}</p>
              </div>
            ))}
          </div>

          <div className="story-stage">
            <div className="story-stage-inner">
              <div className="story-rail" aria-hidden>
                {Array.from({ length: SCENE_COUNT }).map((_, i) => (
                  <span key={i} className={`story-rail-dot ${active >= i ? "is-on" : ""}`} />
                ))}
              </div>
              <div className="story-scenes">
                <Scene index={0} active={active === 0}>
                  <PhoneFrame tone="dark" clock="11:47">
                    <SceneIncoming t={t} />
                  </PhoneFrame>
                </Scene>
                <Scene index={1} active={active === 1}>
                  <PhoneFrame tone="dark" clock="11:48">
                    <ScenePickup t={t} />
                  </PhoneFrame>
                </Scene>
                <Scene index={2} active={active === 2}>
                  <PhoneFrame tone="light" clock="11:53">
                    <SceneSms t={t} />
                  </PhoneFrame>
                </Scene>
                <Scene index={3} active={active === 3}>
                  <div className="scene-owner-tag" aria-hidden>Owner's phone · morning</div>
                  <PhoneFrame tone="light" clock="7:02">
                    <SceneCalendar t={t} />
                  </PhoneFrame>
                </Scene>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Scene({ index, active, children }: { index: number; active: boolean; children: ReactNode }) {
  return (
    <div className={`scene scene-${index} ${active ? "is-active" : ""}`}>{children}</div>
  );
}

function PhoneFrame({
  tone,
  clock,
  children,
}: {
  tone: "dark" | "light";
  clock: string;
  children: ReactNode;
}) {
  return (
    <div className={`phone-frame phone-${tone}`}>
      <div className="phone-bezel">
        <span className="phone-notch" />
        <div className="phone-screen">
          <div className="phone-statusbar">
            <span className="phone-statusbar-time">{clock}</span>
            <span className="phone-statusbar-icons" aria-hidden>
              <i className="phone-icon phone-icon-signal" />
              <i className="phone-icon phone-icon-wifi" />
              <i className="phone-icon phone-icon-battery" />
            </span>
          </div>
          <div className="phone-content">{children}</div>
        </div>
      </div>
    </div>
  );
}

function SceneIncoming({ t }: { t: (k: string) => string }) {
  return (
    <div className="phone-outcall">
      <div className="phone-outcall-status">
        <span className="phone-outcall-dot" />
        <span>{t("story.scene.calling")} · 00:04</span>
      </div>
      <div className="phone-outcall-name">ABC Solar Co.</div>
      <div className="phone-outcall-number">+1 (415) 555-0142</div>
      <div className="phone-outcall-avatar">
        <span className="scene-ring-pulse" />
        <span className="scene-ring-pulse delay" />
        <span className="phone-outcall-avatar-mark">A</span>
      </div>
      <div className="phone-outcall-bars" aria-hidden>
        <span /><span /><span /><span /><span /><span />
      </div>
      <div className="phone-outcall-grid" aria-hidden>
        <PhoneCallTile icon="mute" label="mute" />
        <PhoneCallTile icon="keypad" label="keypad" />
        <PhoneCallTile icon="speaker" label="speaker" />
        <PhoneCallTile icon="add" label="add call" />
        <PhoneCallTile icon="facetime" label="FaceTime" />
        <PhoneCallTile icon="contacts" label="contacts" />
      </div>
      <div className="phone-outcall-actions">
        <button type="button" className="phone-action end" aria-label="End">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 4h4l2 5-3 2a12 12 0 005 5l2-3 5 2v4a2 2 0 01-2 2A17 17 0 013 6a2 2 0 012-2z" transform="rotate(135 12 12)" />
          </svg>
        </button>
      </div>
    </div>
  );
}

function PhoneCallTile({ icon, label }: { icon: string; label: string }) {
  return (
    <span className="phone-outcall-tile">
      <span className={`phone-outcall-tile-icon icon-${icon}`} aria-hidden />
      <span className="phone-outcall-tile-label">{label}</span>
    </span>
  );
}

function ScenePickup({ t }: { t: (k: string) => string }) {
  return (
    <div className="phone-call">
      <div className="phone-call-label">
        <span className="scene-mary-dot" /> {t("story.scene.onLine")} · 00:08
      </div>
      <div className="phone-call-name">Mary</div>
      <div className="phone-call-number">WorkflowAuth</div>
      <div className="phone-call-avatar">
        <span>V</span>
      </div>
      <div className="scene-wave" aria-hidden>
        {Array.from({ length: 28 }).map((_, i) => (
          <span key={i} className="scene-wave-bar" style={{ animationDelay: `${i * 0.05}s` }} />
        ))}
      </div>
      <div className="scene-transcript">{t("story.scene.transcript")}</div>
    </div>
  );
}

function SceneSms({ t }: { t: (k: string) => string }) {
  return (
    <div className="phone-sms">
      <div className="phone-sms-header">
        <span className="phone-sms-back" aria-hidden>‹</span>
        <span className="phone-sms-avatar">V</span>
        <div className="phone-sms-titles">
          <strong>Mary</strong>
          <span>WorkflowAuth</span>
        </div>
      </div>
      <div className="scene-sms-thread">
        <div className="scene-sms-msg in">
          <div className="scene-sms-bubble">{t("convo.msg1")}</div>
        </div>
        <div className="scene-sms-msg out">
          <div className="scene-sms-bubble">{t("convo.msg2")}</div>
        </div>
        <div className="scene-sms-msg in">
          <div className="scene-sms-bubble">{t("convo.msg3")}</div>
        </div>
        <div className="scene-sms-msg out">
          <div className="scene-sms-bubble">
            {t("convo.msg4Pre")}<strong>$3,540</strong>{t("convo.msg4Mid")}
          </div>
        </div>
      </div>
    </div>
  );
}

function SceneCalendar({ t }: { t: (k: string) => string }) {
  return (
    <div className="phone-cal">
      <div className="phone-cal-header">
        <span className="phone-cal-eyebrow">{t("story.scene.calHead")}</span>
        <strong className="phone-cal-title">{t("story.scene.calNew")}</strong>
      </div>
      <div className="phone-cal-list">
        <div className="phone-cal-row is-new">
          <div className="phone-cal-when">
            <span className="phone-cal-day">Tue</span>
            <span className="phone-cal-time">9:30 AM</span>
          </div>
          <div className="phone-cal-body">
            <span className="phone-cal-job">{t("story.scene.cal.survey")}</span>
            <span className="phone-cal-tag">{t("story.scene.cal.tagNew")}</span>
          </div>
        </div>
        <div className="phone-cal-row">
          <div className="phone-cal-when">
            <span className="phone-cal-day">Wed</span>
            <span className="phone-cal-time">2:00 PM</span>
          </div>
          <div className="phone-cal-body">
            <span className="phone-cal-job">{t("story.scene.cal.hvac")}</span>
          </div>
        </div>
        <div className="phone-cal-row is-new">
          <div className="phone-cal-when">
            <span className="phone-cal-day">Fri</span>
            <span className="phone-cal-time">11:00 AM</span>
          </div>
          <div className="phone-cal-body">
            <span className="phone-cal-job">{t("story.scene.cal.roof")}</span>
            <span className="phone-cal-tag">{t("story.scene.cal.tagNew")}</span>
          </div>
        </div>
      </div>
      <div className="phone-cal-foot">{t("story.s4.foot")}</div>
    </div>
  );
}
