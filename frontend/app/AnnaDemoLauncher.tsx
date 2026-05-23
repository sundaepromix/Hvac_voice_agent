"use client";

import { useState } from "react";

import AnnaDemoModal from "./AnnaDemoModal";
import { useI18n } from "./lib/i18n";

type Variant = "primary" | "onDark";

export default function AnnaDemoLauncher({
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
      ? "btn btn-anna btn-lg btn-anna-onDark"
      : "btn btn-anna btn-lg";

  return (
    <>
      <button type="button" className={className} onClick={() => setOpen(true)}>
        <span className="btn-anna-dot" aria-hidden /> {label ?? t("annaLaunch.cta")}
      </button>
      <AnnaDemoModal open={open} onClose={() => setOpen(false)} />
    </>
  );
}
