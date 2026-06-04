"use client";

import { useEffect } from "react";

export default function StitchShell({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const id = "stitch-custom-css";
    if (document.getElementById(id)) return;
    const style = document.createElement("style");
    style.id = id;
    style.textContent = [
      ".glass-card{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px)}",
      ".glow-accent{text-shadow:0 0 15px rgba(124,92,252,0.3)}",
      ".material-symbols-outlined{font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24}",
    ].join("\n");
    document.head.appendChild(style);
  }, []);

  return <>{children}</>;
}
