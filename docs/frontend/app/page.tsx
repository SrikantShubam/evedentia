"use client";

import { useRef, useState } from "react";
import { motion } from "motion/react";
import Link from "next/link";
import { T } from "@/lib/tokens";
import { TournamentPanel } from "@/components/TournamentPanel";

const API = process.env.NEXT_PUBLIC_EVIDENTIA_API ?? "http://127.0.0.1:8000";

// --- Types -------------------------------------------------------------
interface Idea {
  opportunity_id?: string;
  title?: string;
  label?: string;
  cohort?: string;
  pain_hypothesis?: string;
  hypothesis?: {
    headline?: string;
    wedge_statement?: string;
    hypothesis_type?: string;
  };
  verdict?: "PURSUE" | "REFINE" | "KILL";
  final_score?: number;
  score?: number;
  gate_failures?: string[];
  verified_signals?: Array<{ source_url?: string; verbatim_quote?: string }>;
  [key: string]: unknown;
}

// --- Validation Engine stages (6) --------------------------------------
const STAGES = [
  { icon: "🔍", name: "Scan", desc: "Harvest demand signals from HN, Reddit, GitHub" },
  { icon: "✓", name: "Verify", desc: "Confirm quotes exist at source URLs" },
  { icon: "📊", name: "Score", desc: "Apply hard gates then rank survivors" },
  { icon: "📝", name: "Spec", desc: "Generate traceable product spec" },
  { icon: "🛠", name: "Build", desc: "Scaffold approved wedge application" },
  { icon: "🚀", name: "Ship", desc: "Produce deployment metadata + proof level" },
];

// --- Sidebar nav items -------------------------------------------------
const NAV_ITEMS = [
  { label: "Dashboard", icon: "📈", href: "/", active: true },
  { label: "Tournaments", icon: "🏆", href: "/tournament/new" },
  { label: "Insights", icon: "📊", href: "#", soon: true },
  { label: "Archive", icon: "🗄", href: "#", soon: true },
  { label: "Settings", icon: "⚙", href: "#", soon: true },
];

// --- Main Dashboard Homepage -------------------------------------------
export default function DashboardHomepage() {
  const keywordInputRef = useRef<HTMLInputElement>(null);

  // Scan state
  const [keyword, setKeyword] = useState("");
  const [sources, setSources] = useState({ hn: true, reddit: true, github: true, web_search: true });
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [hasScanned, setHasScanned] = useState(false);

  // Validation panel state
  const [activeValidation, setActiveValidation] = useState<{ opp: Idea; keyword: string } | null>(null);

  // Top bar search (light wiring)
  const [topSearch, setTopSearch] = useState("");

  const activeSources = Object.entries(sources).filter(([, v]) => v).map(([k]) => k);

  const runScan = async (overrideKeyword?: string) => {
    const q = (overrideKeyword || keyword).trim();
    if (!q) return;

    if (overrideKeyword) setKeyword(overrideKeyword);

    setScanning(true);
    setScanError(null);
    setIdeas([]);
    setHasScanned(true);

    try {
      const scanRes = await fetch(`${API}/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          keyword: q,
          sources: activeSources,
          max_results: 5,
        }),
      });
      if (!scanRes.ok) {
        const errText = await scanRes.text().catch(() => "scan failed");
        throw new Error(`Scan: ${errText}`);
      }
      const data = await scanRes.json();
      const opps = (data.opportunities || []) as Array<Record<string, unknown>>;
      if (opps.length === 0 && data.discard_log?.length > 0) {
        setScanError(`Scan complete but all ${data.discard_log.length} signals were discarded. Try a different keyword.`);
      }
      setIdeas(opps as Idea[]);
    } catch (e: unknown) {
      setScanError(e instanceof Error ? e.message : "Scan failed");
    } finally {
      setScanning(false);
    }
  };

  const handleTopSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (topSearch.trim()) {
      await runScan(topSearch.trim());
    }
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", minWidth: "800px", background: T.bg, color: T.text }}>
      {/* LEFT SIDEBAR - fixed glass */}
      <aside
        style={{
          width: "240px",
          flexShrink: 0,
          height: "100vh",
          position: "fixed",
          left: 0,
          top: 0,
          background: T.glassBg,
          borderRight: `1px solid ${T.glassBorder}`,
          backdropFilter: "blur(16px)",
          padding: "24px 18px",
          display: "flex",
          flexDirection: "column",
          zIndex: 40,
        }}
      >
        {/* Logo */}
        <Link href="/" style={{ textDecoration: "none" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "18px", fontWeight: 600, letterSpacing: "-0.02em", color: T.text, marginBottom: "28px" }}>
            evidentia
          </div>
        </Link>

        {/* Nav */}
        <nav style={{ display: "flex", flexDirection: "column", gap: "4px", marginBottom: "auto" }}>
          {NAV_ITEMS.map((item) => {
            const isActive = item.active;
            const content = (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  padding: "9px 12px",
                  borderRadius: "8px",
                  fontSize: "14px",
                  color: isActive ? T.accent : T.mutedLight,
                  background: isActive ? T.accentDim : "transparent",
                  border: isActive ? `1px solid ${T.glassAccentBorder}` : "1px solid transparent",
                  cursor: item.soon ? "default" : "pointer",
                  opacity: item.soon ? 0.6 : 1,
                }}
                title={item.soon ? "Coming soon" : undefined}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </div>
            );
            if (item.soon) return <div key={item.label}>{content}</div>;
            return (
              <Link key={item.label} href={item.href} style={{ textDecoration: "none" }}>
                {content}
              </Link>
            );
          })}
        </nav>

        {/* Create New Idea - accent button */}
        <Link href="/tournament/new" style={{ textDecoration: "none" }}>
          <div
            style={{
              marginTop: "auto",
              padding: "10px 14px",
              borderRadius: "8px",
              background: T.accent,
              color: "#000",
              fontWeight: 600,
              fontSize: "13px",
              fontFamily: "var(--font-mono)",
              textAlign: "center" as const,
              letterSpacing: "0.02em",
              border: `1px solid ${T.accent}`,
              cursor: "pointer",
            }}
          >
            + Create New Idea
          </div>
        </Link>
      </aside>

      {/* MAIN AREA */}
      <div style={{ marginLeft: "240px", flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
        {/* TOP BAR */}
        <div
          style={{
            height: "56px",
            borderBottom: `1px solid ${T.border}`,
            background: "rgba(10,10,10,0.7)",
            backdropFilter: "blur(10px)",
            padding: "0 24px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            position: "sticky",
            top: 0,
            zIndex: 30,
          }}
        >
          {/* Search */}
          <form onSubmit={handleTopSearchSubmit} style={{ flex: 1, maxWidth: "360px" }}>
            <input
              type="text"
              value={topSearch}
              onChange={(e) => setTopSearch(e.target.value)}
              placeholder="Search signals or ideas..."
              style={{
                width: "100%",
                fontSize: "13px",
                padding: "8px 12px",
                borderRadius: "999px",
                border: `1px solid ${T.glassBorder}`,
                background: T.glassBg,
                color: T.text,
                outline: "none",
                fontFamily: "var(--font-mono)",
              }}
            />
          </form>

          <div style={{ flex: 1 }} />

          {/* Notifications */}
          <button
            title="Notifications"
            style={{ background: "none", border: "none", fontSize: "16px", cursor: "pointer", color: T.mutedLight, padding: "4px" }}
          >
            🔔
          </button>

          {/* Avatar */}
          <div
            title="Account"
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "50%",
              background: T.glassBg,
              border: `1px solid ${T.glassBorder}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "13px",
              cursor: "pointer",
            }}
          >
            👤
          </div>

          {/* Get Started pill */}
          <Link href="/about" style={{ textDecoration: "none" }}>
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "12px",
                padding: "6px 14px",
                borderRadius: "999px",
                border: `1px solid ${T.glassAccentBorder}`,
                background: T.glassAccentBg,
                color: T.accent,
                cursor: "pointer",
                whiteSpace: "nowrap" as const,
              }}
            >
              Get Started
            </div>
          </Link>

          {/* Pro Plan badge */}
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "11px",
              padding: "4px 10px",
              borderRadius: "999px",
              border: `1px solid ${T.border}`,
              color: T.mutedLight,
              background: T.glassBg,
            }}
          >
            Pro Plan
          </div>
        </div>

        {/* SCROLLABLE CONTENT */}
        <div style={{ flex: 1, overflow: "auto", padding: "32px 28px 60px" }}>
          {/* HERO BANNER */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            style={{ marginBottom: "36px" }}
          >
            <div style={{ fontSize: "13px", color: T.muted, fontFamily: "var(--font-mono)", letterSpacing: "0.06em", marginBottom: "8px" }}>
              EVIDENTIA
            </div>
            <h1 style={{ fontSize: "42px", fontWeight: 700, letterSpacing: "-0.025em", marginBottom: "10px" }}>
              Evidentia ✨
            </h1>
            <p style={{ fontSize: "15px", color: T.muted, maxWidth: "620px", lineHeight: 1.55, marginBottom: "18px" }}>
              Find ideas worth building by scanning signals across the digital landscape with AI-driven validation.
            </p>
            <Link href="#scan-section" style={{ textDecoration: "none" }}>
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "10px 18px",
                  borderRadius: "8px",
                  background: T.glassAccentBg,
                  border: `1px solid ${T.glassAccentBorder}`,
                  color: T.accent,
                  fontSize: "14px",
                  fontWeight: 600,
                  fontFamily: "var(--font-mono)",
                  boxShadow: `0 0 0 1px ${T.accent}15`,
                }}
              >
                Get Started →
              </div>
            </Link>
          </motion.div>

          {/* SCAN / TRY IT SECTION */}
          <div id="scan-section" style={{ marginBottom: "42px" }}>
            <div style={{ marginBottom: "14px" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.accent, letterSpacing: "0.1em" }}>SCAN / TRY IT</span>
            </div>

            {/* Keyword + sources + button */}
            <div style={{ display: "flex", gap: "12px", alignItems: "flex-end", flexWrap: "wrap" as const }}>
              <div style={{ flex: "1 1 320px", minWidth: "260px" }}>
                <input
                  ref={keywordInputRef}
                  type="text"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && runScan()}
                  placeholder="Enter keyword or domain (e.g. invoice reconciliation)"
                  style={{
                    width: "100%",
                    fontSize: "15px",
                    padding: "12px 16px",
                    borderRadius: "10px",
                    border: `1px solid ${T.glassBorder}`,
                    background: T.glassBg,
                    color: T.text,
                    outline: "none",
                    fontFamily: "var(--font-mono)",
                    backdropFilter: "blur(8px)",
                  }}
                />
              </div>

              {/* Source toggles */}
              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" as const }}>
                {[
                  { id: "hn", label: "HN" },
                  { id: "reddit", label: "Reddit" },
                  { id: "github", label: "GitHub" },
                  { id: "web_search", label: "Web" },
                ].map((s) => {
                  const on = (sources as any)[s.id];
                  return (
                    <button
                      key={s.id}
                      onClick={() => setSources((prev) => ({ ...prev, [s.id]: !on }))}
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "12px",
                        padding: "7px 13px",
                        borderRadius: "999px",
                        border: `1px solid ${on ? T.glassAccentBorder : T.glassBorder}`,
                        background: on ? T.glassAccentBg : T.glassBg,
                        color: on ? T.accent : T.mutedLight,
                        cursor: "pointer",
                        backdropFilter: "blur(6px)",
                      }}
                    >
                      {s.label}
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => runScan()}
                disabled={scanning || !keyword.trim()}
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "14px",
                  fontWeight: 600,
                  padding: "11px 22px",
                  borderRadius: "9px",
                  border: `1px solid ${T.accent}`,
                  background: scanning ? T.border : T.accent,
                  color: scanning ? T.muted : "#000",
                  cursor: scanning || !keyword.trim() ? "not-allowed" : "pointer",
                  whiteSpace: "nowrap" as const,
                  minWidth: "108px",
                }}
              >
                {scanning ? "Scanning..." : "Scan →"}
              </button>
            </div>

            {activeSources.length === 0 && (
              <div style={{ fontSize: "11px", color: T.warning, marginTop: "6px", fontFamily: "var(--font-mono)" }}>
                Select at least one source
              </div>
            )}

            {/* Scan error */}
            {scanError && (
              <div style={{ marginTop: "12px", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(248,113,113,0.25)", background: "rgba(248,113,113,0.06)", fontSize: "13px", color: T.danger }}>
                {scanError}
              </div>
            )}
          </div>

          {/* RESULTS GRID - bento 2-col */}
          {(hasScanned || ideas.length > 0) && (
            <div style={{ marginBottom: "46px" }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.accent, letterSpacing: "0.08em", marginBottom: "12px" }}>
                RESULTS {ideas.length > 0 ? `(${ideas.length})` : ""}
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "12px" }}>
                {ideas.length > 0 ? (
                  ideas.map((idea, idx) => {
                    const label = idea.label || idea.title || idea.hypothesis?.headline || "Untitled opportunity";
                    const pain = idea.pain_hypothesis || idea.hypothesis?.wedge_statement || "";
                    const cohort = idea.cohort || idea.hypothesis?.hypothesis_type || "";
                    const score = typeof idea.final_score === "number" ? idea.final_score : (typeof idea.score === "number" ? idea.score : 0);
                    const verdictRaw = (idea.verdict || "REFINE").toString().toUpperCase();
                    const verdict = (verdictRaw === "PURSUE" || verdictRaw === "KILL" || verdictRaw === "REFINE") ? verdictRaw : "REFINE";
                    const gateFailures: string[] = Array.isArray(idea.gate_failures) ? idea.gate_failures : [];
                    const signalsCount = Array.isArray(idea.verified_signals) ? idea.verified_signals.length : 0;
                    const vColor = verdict === "PURSUE" ? T.success : (verdict === "KILL" ? T.danger : T.warning);
                    const vBg = verdict === "PURSUE" ? "rgba(34,197,94,0.1)" : (verdict === "KILL" ? "rgba(239,68,68,0.1)" : "rgba(245,158,11,0.1)");
                    const vBorder = verdict === "PURSUE" ? "rgba(34,197,94,0.25)" : (verdict === "KILL" ? "rgba(239,68,68,0.25)" : "rgba(245,158,11,0.25)");
                    return (
                      <motion.div
                        key={`${idea.opportunity_id || idea.id || idx}`}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: Math.min(idx * 0.03, 0.3) }}
                        style={{
                          border: `1px solid ${T.glassBorder}`,
                          background: T.glassBg,
                          borderRadius: "10px",
                          padding: "16px",
                          backdropFilter: "blur(14px)",
                          display: "flex",
                          flexDirection: "column",
                          gap: "10px",
                        }}
                      >
                        <div style={{ fontSize: "15px", fontWeight: 600, color: T.text, lineHeight: 1.3 }}>{label}</div>
                        {cohort && <div style={{ fontSize: "12px", color: T.muted, fontFamily: "var(--font-mono)" }}>{cohort}</div>}
                        {pain && (
                          <div style={{ fontSize: "13px", color: T.mutedLight, lineHeight: 1.45 }}>{pain}</div>
                        )}
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" as const, marginTop: "2px" }}>
                          <div
                            style={{
                              fontSize: "11px",
                              padding: "3px 8px",
                              borderRadius: "6px",
                              background: vBg,
                              border: `1px solid ${vBorder}`,
                              color: vColor,
                              fontFamily: "var(--font-mono)",
                              fontWeight: 600,
                            }}
                          >
                            {verdict} {Math.round(score * 100)}%
                          </div>
                          {gateFailures.length > 0 && gateFailures.slice(0, 3).map((g, gi) => (
                            <div key={gi} style={{
                              fontSize: "10px",
                              padding: "2px 6px",
                              borderRadius: "4px",
                              background: "rgba(239,68,68,0.08)",
                              border: "1px solid rgba(239,68,68,0.2)",
                              color: T.danger,
                              fontFamily: "var(--font-mono)",
                            }}>{g}</div>
                          ))}
                          {signalsCount > 0 && (
                            <div style={{ fontSize: "10px", color: T.mutedLight, fontFamily: "var(--font-mono)" }}>{signalsCount} signals</div>
                          )}
                        </div>
                        <div style={{ marginTop: "auto", paddingTop: "6px" }}>
                          <button
                            onClick={() => setActiveValidation({ opp: idea, keyword })}
                            style={{
                              width: "100%",
                              padding: "8px 12px",
                              borderRadius: "7px",
                              background: T.glassAccentBg,
                              border: `1px solid ${T.glassAccentBorder}`,
                              color: T.accent,
                              fontSize: "13px",
                              fontWeight: 600,
                              fontFamily: "var(--font-mono)",
                              cursor: "pointer",
                            }}
                          >
                            Validate ▼
                          </button>
                        </div>
                      </motion.div>
                    );
                  })
                ) : null}

                {/* More Signals Needed placeholder (always last or only) */}
                <div
                  style={{
                    border: `1px solid ${T.glassBorder}`,
                    background: T.glassBg,
                    borderRadius: "10px",
                    padding: "18px",
                    backdropFilter: "blur(14px)",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "center",
                    color: T.muted,
                    fontSize: "13px",
                    minHeight: "138px",
                  }}
                >
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.mutedLight, marginBottom: "6px" }}>MORE SIGNALS NEEDED</div>
                  <div>Try a broader keyword or different sources. Real demand hides in the long tail.</div>
                </div>
              </div>
            </div>
          )}

          {/* INLINE TOURNAMENT PANEL */}
          {activeValidation && (
            <div style={{ marginBottom: "46px" }}>
              <TournamentPanel
                opportunity={activeValidation.opp}
                keyword={activeValidation.keyword}
                onClose={() => setActiveValidation(null)}
              />
            </div>
          )}

          {/* THE VALIDATION ENGINE */}
          <div style={{ marginBottom: "52px" }}>
            <div style={{ marginBottom: "12px" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.accent, letterSpacing: "0.1em" }}>THE VALIDATION ENGINE</span>
            </div>
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" as const }}>
              {STAGES.map((stage, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 * i }}
                  whileHover={{ borderColor: T.glassAccentBorder }}
                  style={{
                    flex: "1 1 148px",
                    minWidth: "148px",
                    border: `1px solid ${T.glassBorder}`,
                    background: T.glassBg,
                    borderRadius: "10px",
                    padding: "14px 14px 13px",
                    backdropFilter: "blur(12px)",
                    cursor: "default",
                  }}
                >
                  <div style={{ fontSize: "18px", marginBottom: "6px" }}>{stage.icon}</div>
                  <div style={{ fontWeight: 600, fontSize: "14px", marginBottom: "4px" }}>{stage.name}</div>
                  <div style={{ fontSize: "12px", color: T.muted, lineHeight: 1.35 }}>{stage.desc}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>

        {/* FOOTER */}
        <footer
          style={{
            borderTop: `1px solid ${T.border}`,
            padding: "18px 28px",
            fontSize: "12px",
            color: T.muted,
            fontFamily: "var(--font-mono)",
            display: "flex",
            alignItems: "center",
            gap: "18px",
            flexWrap: "wrap" as const,
          }}
        >
          <span>Evidentia</span>
          <div style={{ display: "flex", gap: "14px", color: T.mutedLight }}>
            <a href="#scan-section" style={{ color: "inherit", textDecoration: "none" }}>Methodology</a>
            <a href="/about" style={{ color: "inherit", textDecoration: "none" }}>Pricing</a>
            <a href="/about" style={{ color: "inherit", textDecoration: "none" }}>Privacy</a>
            <a href="https://github.com" target="_blank" rel="noreferrer" style={{ color: "inherit", textDecoration: "none" }}>API</a>
          </div>
          <span style={{ marginLeft: "auto", opacity: 0.6 }}>© Evidentia</span>
        </footer>
      </div>
    </div>
  );
}
