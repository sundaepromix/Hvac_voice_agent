// Decorative layer for the hero — soft ember glow + very faint architectural line art.
// All elements are aria-hidden and pointer-events: none.

export default function HeroBackdrop() {
  return (
    <div className="hero-backdrop" aria-hidden>
      <div className="hero-glow" />
      <div className="hero-glow hero-glow-2" />
      <div className="hero-grid" />
      <div className="hero-house" aria-hidden>
        <House />
      </div>
    </div>
  );
}

function strokeProps(width = 2.2) {
  return {
    fill: "none" as const,
    stroke: "currentColor",
    strokeWidth: width,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
}

function House() {
  // Faint architectural cross-section behind the hero
  return (
    <svg viewBox="0 0 1200 600" width="100%" height="100%" preserveAspectRatio="xMidYMid meet">
      <g {...strokeProps(1.4)}>
        {/* roof */}
        <path d="M200 280 L600 80 L1000 280" />
        <path d="M260 280 L600 110 L940 280" />
        {/* main outline */}
        <path d="M250 280 L250 540 L950 540 L950 280" />
        {/* chimney */}
        <path d="M780 220 L780 160 L820 160 L820 240" />
        {/* windows */}
        <rect x="320" y="320" width="90" height="90" />
        <rect x="510" y="320" width="90" height="90" />
        <rect x="700" y="320" width="90" height="90" />
        <rect x="510" y="450" width="90" height="90" />
        {/* window crosses */}
        <path d="M320 365h90M365 320v90M510 365h90M555 320v90M700 365h90M745 320v90" />
        {/* door */}
        <rect x="320" y="440" width="80" height="100" />
        <circle cx="385" cy="495" r="2" />
        {/* HVAC unit */}
        <rect x="850" y="470" width="60" height="50" />
        <circle cx="880" cy="495" r="14" />
        <path d="M870 495 L880 480 L890 495 M870 495 L880 510 L890 495" />
        {/* solar panels */}
        <path d="M380 215 L530 140 L560 175 L410 250 Z" />
        <path d="M380 215 L410 250M395 207 L425 242M410 200 L440 235M425 192 L455 227M440 185 L470 220M455 178 L485 213M470 170 L500 205M485 163 L515 198M500 155 L530 190" />
        {/* foundation */}
        <path d="M230 540 L970 540" strokeWidth="2.4" />
        <path d="M250 555 L950 555" strokeDasharray="6 4" />
      </g>
    </svg>
  );
}
