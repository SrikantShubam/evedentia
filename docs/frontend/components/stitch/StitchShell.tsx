"use client";

import { useEffect } from "react";

export default function StitchShell({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Inject CDN Tailwind only on client side to avoid hydration mismatch
    const existing = document.getElementById("stitch-tailwind");
    if (existing) return;

    const script = document.createElement("script");
    script.id = "stitch-tailwind";
    script.src = "https://cdn.tailwindcss.com?plugins=forms,container-queries";
    document.head.appendChild(script);

    // Inject Tailwind config
    const config = document.createElement("script");
    config.id = "stitch-config";
    config.textContent = `tailwind.config={darkMode:"class",theme:{extend:{colors:{primary:"#7c5cfc",surface:"#0f0e0f",glass:"rgba(255,255,255,0.03)","glass-border":"rgba(255,255,255,0.08)",success:"#34d399",warning:"#f59e0b",danger:"#ef4444"},borderRadius:{DEFAULT:"0.5rem",lg:"1rem",xl:"1.5rem",full:"9999px"},fontFamily:{headline:["Inter","sans-serif"],display:["Inter","sans-serif"],body:["Inter","sans-serif"],label:["Inter","sans-serif"],mono:["Roboto Mono","monospace"]}}}}`;
    document.head.appendChild(config);

    // Inject custom CSS
    const style = document.createElement("style");
    style.id = "stitch-style";
    style.textContent = `body{background:#0f0e0f;color:white;margin:0}.glass-card{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px)}.glow-accent{text-shadow:0 0 15px rgba(124,92,252,0.3)}.material-symbols-outlined{font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24}::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:#0f0e0f}::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.1);border-radius:3px}`;
    document.head.appendChild(style);
  }, []);

  return <>{children}</>;
}
