"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

const ChatWidget = dynamic(() => import("./ChatWidget"), { ssr: false });

export default function ChatWidgetLazy() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const reveal = () => setShow(true);
    type IdleCb = (cb: () => void) => number;
    const ric = (window as unknown as { requestIdleCallback?: IdleCb }).requestIdleCallback;
    const id = ric ? ric(reveal) : window.setTimeout(reveal, 1500);
    const onScroll = () => { reveal(); };
    window.addEventListener("scroll", onScroll, { once: true, passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      if (typeof id === "number") clearTimeout(id);
    };
  }, []);

  if (!show) return null;
  return <ChatWidget />;
}
