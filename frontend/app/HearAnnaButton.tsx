"use client";

import { useEffect, useRef, useState } from "react";

const SAMPLE_SRC = "/anna-sample.mp3";
const TRANSCRIPT =
  "“Hi, this is Mary with ABC Solar Co. I can help you tonight — what’s going on at home?”";

export default function HearAnnaButton() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let cancelled = false;
    fetch(SAMPLE_SRC, { method: "HEAD" })
      .then((r) => !cancelled && setAvailable(r.ok))
      .catch(() => !cancelled && setAvailable(false));
    return () => {
      cancelled = true;
    };
  }, []);

  function toggle() {
    const a = audioRef.current;
    if (!a) return;
    if (playing) {
      a.pause();
      setPlaying(false);
    } else {
      a.play().then(() => setPlaying(true)).catch(() => setPlaying(false));
    }
  }

  if (available === false) return null;

  return (
    <div className="hear-anna">
      <button type="button" className={`hear-anna-btn ${playing ? "is-playing" : ""}`} onClick={toggle} aria-label={playing ? "Pause sample" : "Play sample"}>
        <span className="hear-anna-icon" aria-hidden>
          {playing ? (
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1" /><rect x="14" y="5" width="4" height="14" rx="1" /></svg>
          ) : (
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M7 5l13 7-13 7V5z" /></svg>
          )}
        </span>
        <span>Hear Mary · 15s sample</span>
        <span className="hear-anna-progress" aria-hidden>
          <span className="hear-anna-progress-bar" style={{ width: `${progress}%` }} />
        </span>
      </button>
      <p className="hear-anna-transcript">{TRANSCRIPT}</p>
      <audio
        ref={audioRef}
        src={SAMPLE_SRC}
        preload="none"
        onEnded={() => { setPlaying(false); setProgress(0); }}
        onTimeUpdate={(e) => {
          const a = e.currentTarget;
          if (a.duration) setProgress((a.currentTime / a.duration) * 100);
        }}
      />
    </div>
  );
}
