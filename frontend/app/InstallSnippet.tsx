"use client";

import { useState } from "react";

const CMD = "git clone github.com/yourname/dropline && docker compose up";

export default function InstallSnippet() {
  const [copied, setCopied] = useState(false);

  function copy() {
    navigator.clipboard.writeText(CMD).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  }

  return (
    <button type="button" className="install-snippet" onClick={copy} aria-label="Copy install command">
      <span className="install-snippet-prompt" aria-hidden>$</span>
      <code className="install-snippet-cmd">{CMD}</code>
      <span className={`install-snippet-copy ${copied ? "is-copied" : ""}`} aria-hidden>
        {copied ? "Copied" : "Copy"}
      </span>
    </button>
  );
}
