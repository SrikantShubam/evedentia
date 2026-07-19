"use client";
import Link from "next/link";
import { T } from "@/lib/tokens";

export default function TopNav() {
  return (
    <header
      style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "12px 32px", position: "sticky", top: 0, zIndex: 50,
        background: "rgba(15,14,15,0.6)", backdropFilter: "blur(12px)",
        borderBottom: "1px solid rgba(255,255,255,0.1)",
        fontFamily: "'Inter', sans-serif",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
        <div style={{ position: "relative" }}>
          <input
            type="text"
            placeholder="Search ideas..."
            style={{
              background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 9999, padding: "6px 16px 6px 40px", fontSize: 13,
              color: "white", outline: "none", width: 256, fontFamily: "inherit",
            }}
          />
          <span className="material-symbols-outlined" style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: T.textMuted, fontSize: 18 }}>
            search
          </span>
        </div>
        <nav style={{ display: "flex", gap: 24 }}>
          <Link href="/" style={{ textDecoration: "none", color: T.primary, borderBottom: `2px solid ${T.primary}`, paddingBottom: 4, fontSize: 14, fontWeight: 500 }}>
            Dashboard
          </Link>
          <Link href="/tournament-live" style={{ textDecoration: "none", color: T.textSecondary, fontSize: 14, fontWeight: 500 }}>
            Tournaments
          </Link>
          <Link href="/scan-validation" style={{ textDecoration: "none", color: T.textSecondary, fontSize: 14, fontWeight: 500 }}>
            Ventures
          </Link>
          <Link href="/full-stack-validation" style={{ textDecoration: "none", color: T.textSecondary, fontSize: 14, fontWeight: 500 }}>
            Analytics
          </Link>
        </nav>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <button
          style={{
            background: "rgba(124,92,252,0.1)", border: "1px solid rgba(124,92,252,0.2)",
            color: T.primary, padding: "6px 16px", borderRadius: 9999,
            fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em",
            cursor: "pointer", fontFamily: "inherit",
          }}
        >
          Get Started
        </button>
        <div style={{ display: "flex", alignItems: "center", gap: 12, paddingLeft: 16, borderLeft: "1px solid rgba(255,255,255,0.1)" }}>
          <button style={{ background: "none", border: "none", color: T.textSecondary, cursor: "pointer" }}>
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <button style={{ background: "none", border: "none", color: T.textSecondary, cursor: "pointer" }}>
            <span className="material-symbols-outlined">settings</span>
          </button>
          <div style={{ width: 32, height: 32, borderRadius: "50%", background: `linear-gradient(135deg, ${T.primary}, #a888ff)`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, color: "white" }}>
            U
          </div>
        </div>
      </div>
    </header>
  );
}
