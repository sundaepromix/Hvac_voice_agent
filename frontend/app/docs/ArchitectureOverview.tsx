"use client";

import { motion, useReducedMotion, type Variants } from "motion/react";

const STAGES = [
  {
    num: "01",
    title: "Caller",
    body: "Phone · SMS · WhatsApp · web chat · email",
    icon: <PhoneIcon />,
    accent: "var(--ink)",
  },
  {
    num: "02",
    title: "Vapi / Twilio",
    body: "Voice handling, transcript per turn",
    icon: <WaveIcon />,
    accent: "#2563eb",
  },
  {
    num: "03",
    title: "Django + Mary",
    body: "Claude tool loop, persists to Postgres",
    icon: <BrainIcon />,
    accent: "var(--brand)",
  },
  {
    num: "04",
    title: "Next.js dashboard",
    body: "Server components, live KPIs, quote PDFs",
    icon: <DashIcon />,
    accent: "#16a34a",
  },
];

export default function ArchitectureOverview() {
  const reduce = useReducedMotion();

  const cellVariants: Variants = {
    hidden: { opacity: 0, y: reduce ? 0 : 18, scale: reduce ? 1 : 0.96 },
    show: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: { type: "spring", stiffness: 220, damping: 24, mass: 0.9 },
    },
  };

  const arrowVariants: Variants = {
    hidden: { opacity: 0, x: reduce ? 0 : -8 },
    show: { opacity: 1, x: 0, transition: { duration: 0.35, ease: "easeOut" } },
  };

  const containerVariants: Variants = {
    hidden: {},
    show: { transition: { staggerChildren: 0.12, delayChildren: 0.05 } },
  };

  return (
    <motion.div
      className="arch-flow"
      variants={containerVariants}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.35 }}
    >
      {STAGES.map((s, i) => (
        <ArchCell
          key={s.num}
          stage={s}
          isLast={i === STAGES.length - 1}
          variants={cellVariants}
          arrowVariants={arrowVariants}
          reduce={reduce ?? false}
        />
      ))}
    </motion.div>
  );
}

function ArchCell({
  stage,
  isLast,
  variants,
  arrowVariants,
  reduce,
}: {
  stage: (typeof STAGES)[number];
  isLast: boolean;
  variants: Variants;
  arrowVariants: Variants;
  reduce: boolean;
}) {
  return (
    <>
      <motion.div
        className="arch-cell"
        variants={variants}
        whileHover={reduce ? undefined : { y: -3, transition: { type: "spring", stiffness: 320, damping: 20 } }}
        style={{ ["--accent" as string]: stage.accent }}
      >
        <div className="arch-cell-glow" aria-hidden />
        <div className="arch-cell-head">
          <span className="arch-cell-num">{stage.num}</span>
          <motion.span
            className="arch-cell-icon"
            initial={false}
            whileHover={reduce ? undefined : { rotate: 6, scale: 1.05 }}
            transition={{ type: "spring", stiffness: 320, damping: 18 }}
            aria-hidden
          >
            {stage.icon}
          </motion.span>
        </div>
        <strong className="arch-cell-title">{stage.title}</strong>
        <span className="arch-cell-body">{stage.body}</span>
        <span className="arch-cell-pulse" aria-hidden />
      </motion.div>
      {!isLast && (
        <motion.div className="arch-arrow" aria-hidden variants={arrowVariants}>
          <ArrowFlow reduce={reduce} />
        </motion.div>
      )}
    </>
  );
}

function ArrowFlow({ reduce }: { reduce: boolean }) {
  return (
    <svg viewBox="0 0 64 24" width="64" height="24" fill="none" aria-hidden>
      <defs>
        <linearGradient id="arch-arrow-grad" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%" stopColor="var(--brand)" stopOpacity="0.15" />
          <stop offset="50%" stopColor="var(--brand)" stopOpacity="0.65" />
          <stop offset="100%" stopColor="var(--brand)" stopOpacity="0.15" />
        </linearGradient>
      </defs>
      <line x1="2" y1="12" x2="58" y2="12" stroke="url(#arch-arrow-grad)" strokeWidth="1.6" strokeLinecap="round" />
      <motion.circle
        cx="2"
        cy="12"
        r="2.5"
        fill="var(--brand)"
        initial={{ cx: 2, opacity: 0 }}
        animate={
          reduce
            ? { cx: 58, opacity: 1 }
            : { cx: [2, 58], opacity: [0, 1, 1, 0] }
        }
        transition={
          reduce
            ? { duration: 0 }
            : { duration: 1.6, repeat: Infinity, ease: "easeInOut", repeatDelay: 0.4 }
        }
      />
      <path d="M54 7 L62 12 L54 17" stroke="var(--brand)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" fill="none" opacity="0.85" />
    </svg>
  );
}

function PhoneIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
    </svg>
  );
}
function WaveIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round">
      <path d="M3 12h2M7 7v10M11 4v16M15 8v8M19 11v2M21 12h0" />
    </svg>
  );
}
function BrainIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 5a3 3 0 0 0-3 3v0a2.5 2.5 0 0 0-2 4 2.5 2.5 0 0 0 1.5 4.5A3 3 0 0 0 12 19V5z" />
      <path d="M12 5a3 3 0 0 1 3 3v0a2.5 2.5 0 0 1 2 4 2.5 2.5 0 0 1-1.5 4.5A3 3 0 0 1 12 19V5z" />
    </svg>
  );
}
function DashIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="9" />
      <rect x="14" y="3" width="7" height="5" />
      <rect x="14" y="12" width="7" height="9" />
      <rect x="3" y="16" width="7" height="5" />
    </svg>
  );
}
