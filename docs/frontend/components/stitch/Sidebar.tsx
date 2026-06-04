"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { T } from "@/lib/tokens";

const NAV = [
  { label: "Overview", icon: "dashboard", href: "/" },
  { label: "Live Tournaments", icon: "emoji_events", href: "/tournament-live" },
  { label: "Idea Lab", icon: "psychology", href: "/scan-validation" },
  { label: "Network", icon: "hub", href: "/full-stack-validation" },
  { label: "Evidence Trail", icon: "account_tree", href: "/evidence-trail" },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside
      style={{
        position: "fixed", left: 0, top: 0, height: "100vh", width: 256,
        background: "rgba(15,14,15,0.4)", backdropFilter: "blur(24px)",
        borderRight: "1px solid rgba(255,255,255,0.1)", zIndex: 60,
        display: "flex", flexDirection: "column", padding: "32px 16px", gap: 32,
        fontFamily: "'Inter', sans-serif",
      }}
    >
      <div style={{ padding: "0 16px" }}>
        <div style={{ fontWeight: 800, color: T.primary, fontSize: 18, textTransform: "uppercase", letterSpacing: "-0.03em" }}>
          Evidentia
        </div>
        <div style={{ color: T.textMuted, fontSize: 10, textTransform: "uppercase", letterSpacing: "0.2em", marginTop: 4 }}>
          AI Idea Validator
        </div>
      </div>
      <nav style={{ display: "flex", flexDirection: "column", gap: 4, flex: 1 }}>
        {NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link key={item.href} href={item.href} style={{ textDecoration: "none" }}>
              <div
                style={{
                  display: "flex", alignItems: "center", gap: 12, padding: "12px 16px",
                  borderRadius: 12, fontSize: 12, fontWeight: 600, textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  color: active ? T.primary : "rgba(255,255,255,0.4)",
                  background: active ? "rgba(124,92,252,0.1)" : "transparent",
                  border: active ? "1px solid rgba(124,92,252,0.2)" : "1px solid transparent",
                  boxShadow: active ? "0 0 15px rgba(124,92,252,0.1)" : "none",
                  transition: "all 0.2s",
                }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: 20 }}>{item.icon}</span>
                <span>{item.label}</span>
              </div>
            </Link>
          );
        })}
      </nav>
      <div style={{ padding: "0 16px" }}>
        <button
          style={{
            width: "100%", padding: "12px 0", borderRadius: 12,
            background: T.primary, color: "white", border: "none",
            fontSize: 11, fontWeight: 700, textTransform: "uppercase",
            letterSpacing: "0.05em", cursor: "pointer",
          }}
        >
          New Venture
        </button>
        <div style={{ paddingTop: 16, borderTop: "1px solid rgba(255,255,255,0.05)", marginTop: 16 }}>
          <Link href="#" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 12, padding: "8px", color: T.textMuted, fontSize: 12 }}>
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>help</span> Help Center
          </Link>
          <Link href="#" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 12, padding: "8px", color: T.textMuted, fontSize: 12 }}>
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>logout</span> Log Out
          </Link>
        </div>
      </div>
    </aside>
  );
}
