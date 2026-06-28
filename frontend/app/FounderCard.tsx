"use client";

import { useState } from "react";

type Props = {
  name: string;
  role: string;
  note: string;
  variant?: "card" | "about";
  eyebrow?: string;
  title?: string;
};

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
}

export default function FounderCard({
  name,
  role,
  note,
  variant = "card",
  eyebrow,
  title,
}: Props) {
  const [imgOk, setImgOk] = useState(true);

  const photo = imgOk ? (
    // eslint-disable-next-line @next/next/no-img-element -- single static asset, no layout shift
    <img
      className={variant === "about" ? "about-photo" : "founder-photo"}
      src="/founder.jpg"
      alt={name}
      width={variant === "about" ? 168 : 84}
      height={variant === "about" ? 168 : 84}
      onError={() => setImgOk(false)}
    />
  ) : (
    <span
      className={variant === "about" ? "about-initials" : "founder-initials"}
      aria-hidden
    >
      {initials(name) || "PS"}
    </span>
  );

  if (variant === "about") {
    return (
      <div className="about-card">
        <div className="about-photo-wrap">{photo}</div>
        <div className="about-text">
          {eyebrow ? <span className="section-flourish">{eyebrow}</span> : null}
          {title ? <h2 className="about-title">{title}</h2> : null}
          <p className="about-body">{note}</p>
          <p className="about-byline">
            <strong>{name}</strong> · {role}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="founder-card">
      {photo}
      <div className="founder-text">
        <p className="founder-note-text">{note}</p>
        <p className="founder-byline">
          <strong>{name}</strong> · {role}
        </p>
      </div>
    </div>
  );
}
