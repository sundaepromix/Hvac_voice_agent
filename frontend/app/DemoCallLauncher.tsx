"use client";

import { useState } from "react";

import DemoCallModal from "./DemoCallModal";
import { useI18n } from "./lib/i18n";

type Variant = "primary" | "onDark";

export default function DemoCallLauncher({
  label,
  variant = "primary",
}: {
  label?: string;
  variant?: Variant;
}) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const className =
    variant === "onDark"
      ? "btn btn-mary btn-lg btn-mary-onDark"
      : "btn btn-mary btn-lg";

  return (
    <>
      <button type="button" className={className} onClick={() => setOpen(true)}>
        <span className="btn-mary-dot" aria-hidden /> {label ?? t("maryLaunch.cta")}
      </button>
      <DemoCallModal open={open} onClose={() => setOpen(false)} />
    </>
  );
}
