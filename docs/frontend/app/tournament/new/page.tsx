"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "motion/react";
import { T } from "@/lib/tokens";

const API = process.env.NEXT_PUBLIC_EVIDENTIA_API ?? "http://127.0.0.1:8000";

const SAMPLE_IDEA = {
  id: "idea-1",
  label: "Agency onboarding assistant",
  anchor_slug: "onboarding-tools",
  incumbent: "IncumbentX",
  cohort: "small agencies",
  pain_hypothesis: "Teams are willing to pay monthly to reduce onboarding errors and manual work.",
  kill_condition: { description: "No market", gate_name: "parent_market_exists" },
  evidence_ids: ["sig-1", "sig-2", "sig-3", "sig-4"],
  search_queries: ["agency onboarding budget", "agency onboarding complaints"],
  origin: "manual",
  gate_profile: "consumer_app",
  gate_profile_source: "inferred:0.82",
  parent_idea_id: null,
};

const ANCHORS = [
  { slug: "onboarding-tools", label: "Onboarding Tools" },
  { slug: "invoice-reconciliation", label: "Invoice Reconciliation" },
  { slug: "dev-tooling", label: "Dev Tooling" },
  { slug: "crm-for-agencies", label: "CRM for Agencies" },
  { slug: "expense-tracking", label: "Expense Tracking" },
];

const GATE_PROFILES = ["consumer_app", "b2b_workflow", "browser_extension", "agency_service"];

function NewTournamentContent() {
  const [playerId, setPlayerId] = useState("default");
  const [profileOverride, setProfileOverride] = useState("");
  const [ideasText, setIdeasText] = useState(JSON.stringify([SAMPLE_IDEA], null, 2));
  const [status, setStatus] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const [anchorSlug, setAnchorSlug] = useState("onboarding-tools");
  const [signalCount, setSignalCount] = useState<number | null>(null);
  const [isHarvesting, setIsHarvesting] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const searchParams = useSearchParams();
  const hasPrefilledRef = useRef(false);

  useEffect(() => {
    if (hasPrefilledRef.current) return;
    const prefill = searchParams.get("prefill");
    if (prefill) {
      const found = ANCHORS.find((a) => a.slug === prefill);
      if (found) setAnchorSlug(found.slug);
    }
    const player = searchParams.get("player");
    if (player) setPlayerId(player);
    hasPrefilledRef.current = true;
  }, [searchParams]);

  const inferredProfile = useMemo(() => {
    try {
      const parsed = JSON.parse(ideasText);
      if (!Array.isArray(parsed) || parsed.length === 0) return "n/a";
      return `${parsed[0].gate_profile} (${parsed[0].gate_profile_source})`;
    } catch {
      return "n/a";
    }
  }, [ideasText]);

  const isValidJson = useMemo(() => {
    try {
      const parsed = JSON.parse(ideasText);
      return Array.isArray(parsed) && parsed.length > 0;
    } catch {
      return false;
    }
  }, [ideasText]);

  const previewHarvest = async () => {
    setIsHarvesting(true);
    setSignalCount(null);
    try {
      const res = await fetch(`${API}/harvest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ anchor_slug: anchorSlug, limit: 20 }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setSignalCount(data.signal_count ?? 0);
    } catch (e) {
      setStatus(`Harvest preview failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setIsHarvesting(false);
    }
  };

  const generateIdeas = async () => {
    setIsGenerating(true);
    try {
      const res = await fetch(`${API}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ anchor_slug: anchorSlug, count: 5 }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      if (data.ideas && Array.isArray(data.ideas)) {
        setIdeasText(JSON.stringify(data.ideas, null, 2));
      }
    } catch (e) {
      setStatus(`Generate ideas failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const runTournament = async () => {
    if (!isValidJson) return;
    setIsLoading(true);
    setStatus("Running...");
    try {
      const ideas = JSON.parse(ideasText);
      const tournamentId = `web-${new Date().toISOString().replace(/[:.]/g, "-")}`;
      const res = await fetch(`${API}/tournament`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tournament_id: tournamentId,
          player_id: playerId,
          ideas,
          gate_profile: profileOverride || null,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      setStatus(`Tournament created: ${tournamentId}`);
      window.location.href = `/tournament/${encodeURIComponent(tournamentId)}`;
    } catch (error) {
      setStatus(`Run failed: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(ideasText);
      setStatus("Copied to clipboard");
      setTimeout(() => setStatus(""), 2000);
    } catch {
      setStatus("Copy failed");
    }
  };

  const handleAnchorClick = (slug: string) => {
    setAnchorSlug(slug);
    setSignalCount(null);
  };

  return (
    <main className="min-h-screen pb-16" style={{ background: T.bg, color: T.text }}>
      {/* Top Bar */}
      <div style={{ borderBottom: `1px solid ${T.border}`, background: "rgba(10,10,10,0.8)", backdropFilter: "blur(12px)", padding: "0 28px", height: "56px", display: "flex", alignItems: "center", gap: "14px", position: "sticky", top: 0, zIndex: 40 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "14px", fontWeight: 600, color: T.text }}>Evidentia</span>
        <div style={{ flex: 1 }} />
        <a href="/" style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.mutedLight, textDecoration: "none" }}>Dashboard</a>
        <a href="/tournament/new" style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.accent, textDecoration: "none" }}>Tournaments</a>
        <a href="/about" style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.mutedLight, textDecoration: "none" }}>About</a>
      </div>

      <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "32px 24px" }}>
        {/* Header */}
        <div style={{ marginBottom: "32px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "8px" }}>
            <div style={{ width: "36px", height: "36px", borderRadius: "10px", background: "rgba(226,255,93,0.1)", border: `1px solid ${T.glassAccentBorder}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px" }}>
              +
            </div>
            <div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.accent, letterSpacing: "0.1em", textTransform: "uppercase" }}>
                Initiation Protocol
              </div>
              <h1 style={{ fontSize: "30px", fontWeight: 700, letterSpacing: "-0.02em" }}>New Tournament</h1>
            </div>
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "8px", padding: "6px 14px", borderRadius: "999px", border: `1px solid ${T.glassBorder}`, background: T.glassBg }}>
              <div style={{ width: "7px", height: "7px", borderRadius: "50%", background: T.warning }} />
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.mutedLight }}>Drafting</span>
            </div>
          </div>
          <p style={{ fontSize: "13px", color: T.muted, marginTop: "8px", maxWidth: "560px", lineHeight: 1.5 }}>
            Configure your orchestration layer and define tournament parameters to begin harvesting high-intent signals.
          </p>
        </div>

        {/* Layout: Left content + Right sidebar */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: "22px", alignItems: "start" }}>

          {/* LEFT COLUMN */}
          <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>

            {/* Anchor Picker — tag pills */}
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} style={{
              border: `1px solid ${T.glassBorder}`, borderRadius: "14px", background: T.glassBg, backdropFilter: "blur(14px)", padding: "18px 20px"
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                <span style={{ fontSize: "20px" }}>&#x1F4CA;</span>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.accent, letterSpacing: "0.08em", textTransform: "uppercase" }}>Anchor Picker</span>
              </div>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                {ANCHORS.map((a) => (
                  <button
                    key={a.slug}
                    onClick={() => handleAnchorClick(a.slug)}
                    style={{
                      fontFamily: "var(--font-mono)", fontSize: "12px", fontWeight: 500,
                      padding: "8px 16px", borderRadius: "999px", cursor: "pointer", border: "1px solid",
                      background: anchorSlug === a.slug ? T.glassAccentBg : "transparent",
                      borderColor: anchorSlug === a.slug ? T.glassAccentBorder : T.glassBorder,
                      color: anchorSlug === a.slug ? T.accent : T.mutedLight,
                      transition: "all 0.2s",
                    }}
                  >
                    {a.label}
                  </button>
                ))}
              </div>
            </motion.div>

            {/* Gate Profile + Player ID */}
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.04 }} style={{
              display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px"
            }}>
              <div style={{ border: `1px solid ${T.glassBorder}`, borderRadius: "14px", background: T.glassBg, backdropFilter: "blur(14px)", padding: "18px 20px" }}>
                <label style={{ display: "block", fontFamily: "var(--font-mono)", fontSize: "10px", color: T.mutedLight, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: "8px" }}>
                  Gate Profile
                </label>
                <select
                  value={profileOverride}
                  onChange={(e) => setProfileOverride(e.target.value)}
                  style={{
                    width: "100%", padding: "9px 12px", borderRadius: "10px", fontFamily: "var(--font-mono)", fontSize: "13px",
                    border: `1px solid ${T.glassBorder}`, background: "rgba(255,255,255,0.04)", color: T.text, outline: "none", cursor: "pointer",
                  }}
                >
                  <option value="" style={{ background: "#0a0a0a" }}> (inferred) </option>
                  {GATE_PROFILES.map((p) => (
                    <option key={p} value={p} style={{ background: "#0a0a0a" }}>{p}</option>
                  ))}
                </select>
              </div>

              <div style={{ border: `1px solid ${T.glassBorder}`, borderRadius: "14px", background: T.glassBg, backdropFilter: "blur(14px)", padding: "18px 20px" }}>
                <label style={{ display: "block", fontFamily: "var(--font-mono)", fontSize: "10px", color: T.mutedLight, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: "8px" }}>
                  Player ID
                </label>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "18px", color: T.muted }}>&#x1F464;</span>
                  <input
                    value={playerId}
                    onChange={(e) => setPlayerId(e.target.value)}
                    style={{
                      flex: 1, padding: "9px 12px", borderRadius: "10px", fontFamily: "var(--font-mono)", fontSize: "13px",
                      border: `1px solid ${T.glassBorder}`, background: "rgba(255,255,255,0.04)", color: T.text, outline: "none",
                    }}
                  />
                </div>
              </div>
            </motion.div>

            {/* Inferred profile line */}
            <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "0 4px" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted }}>Inferred:</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.accent }}>{inferredProfile}</span>
            </div>

            {/* Signal Intelligence */}
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.08 }} style={{
              border: `1px solid ${T.glassBorder}`, borderRadius: "14px", background: T.glassBg, backdropFilter: "blur(14px)", padding: "22px 20px"
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "18px" }}>
                <span style={{ fontSize: "22px" }}>&#x1F680;</span>
                <div>
                  <div style={{ fontSize: "15px", fontWeight: 600 }}>Signal Intelligence</div>
                  <div style={{ fontSize: "12px", color: T.muted, fontFamily: "var(--font-mono)" }}>
                    Initialize the harvest engine to detect market signals
                  </div>
                </div>
              </div>

              {/* Signal count */}
              {signalCount !== null && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  style={{
                    marginBottom: "16px", padding: "14px 18px",
                    borderRadius: "10px", border: `1px solid ${T.glassAccentBorder}`,
                    background: T.glassAccentBg,
                    display: "flex", alignItems: "baseline", gap: "8px",
                  }}
                >
                  <span style={{ fontSize: "28px", fontWeight: 700, color: T.accent, fontFamily: "var(--font-mono)" }}>
                    {signalCount.toLocaleString()}
                  </span>
                  <span style={{ fontSize: "13px", color: T.mutedLight, fontFamily: "var(--font-mono)" }}>SIGNALS FOUND</span>
                </motion.div>
              )}

              {/* Harvest + Generate buttons */}
              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  onClick={previewHarvest}
                  disabled={isHarvesting}
                  style={{
                    flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
                    padding: "12px 0", borderRadius: "10px", border: "none",
                    fontFamily: "var(--font-mono)", fontSize: "13px", fontWeight: 600,
                    background: T.accent, color: "#000",
                    cursor: isHarvesting ? "not-allowed" : "pointer",
                    opacity: isHarvesting ? 0.5 : 1,
                  }}
                >
                  <span style={{ fontSize: "16px" }}>&#x1F4E1;</span>
                  {isHarvesting ? "Harvesting..." : "Preview Harvest"}
                </button>
                <button
                  onClick={generateIdeas}
                  disabled={isGenerating}
                  style={{
                    flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
                    padding: "12px 0", borderRadius: "10px",
                    fontFamily: "var(--font-mono)", fontSize: "13px", fontWeight: 600,
                    background: "transparent", color: T.accent,
                    border: `1px solid ${T.accent}`,
                    cursor: isGenerating ? "not-allowed" : "pointer",
                    opacity: isGenerating ? 0.5 : 1,
                  }}
                >
                  <span style={{ fontSize: "16px" }}>&#x1F4A1;</span>
                  {isGenerating ? "Generating..." : "Generate Ideas"}
                </button>
              </div>
            </motion.div>

            {/* Configuration Manifest (JSON) */}
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.12 }} style={{
              border: `1px solid ${T.glassAccentBorder}`, borderRadius: "14px", background: T.glassBg, backdropFilter: "blur(14px)", overflow: "hidden"
            }}>
              <div style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "12px 18px",
                borderBottom: `1px solid ${T.glassBorder}`,
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", fontWeight: 600, color: T.text }}>
                    Configuration Manifest (JSON)
                  </div>
                  <span style={{
                    fontFamily: "var(--font-mono)", fontSize: "9px", padding: "2px 8px", borderRadius: "4px",
                    background: T.accentDim, color: T.accent, border: `1px solid ${T.glassAccentBorder}`,
                    textTransform: "uppercase",
                  }}>
                    PROTOCOL_V4.2
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <button
                    onClick={handleCopy}
                    style={{
                      fontFamily: "var(--font-mono)", fontSize: "11px", color: T.mutedLight,
                      background: "none", border: "none", cursor: "pointer",
                      display: "flex", alignItems: "center", gap: "4px",
                    }}
                  >
                    <span>&#x1F4CB;</span> Copy
                  </button>
                  <button
                    onClick={() => setIdeasText(JSON.stringify([SAMPLE_IDEA], null, 2))}
                    style={{
                      fontFamily: "var(--font-mono)", fontSize: "11px", color: T.accent,
                      background: "none", border: "none", cursor: "pointer",
                    }}
                  >
                    Load sample
                  </button>
                </div>
              </div>
              <textarea
                value={ideasText}
                onChange={(e) => setIdeasText(e.target.value)}
                style={{
                  width: "100%", minHeight: "340px", padding: "16px 18px", resize: "vertical",
                  fontFamily: "var(--font-mono)", fontSize: "12px", lineHeight: 1.55,
                  background: "rgba(0,0,0,0.35)", border: "none",
                  color: T.text, outline: "none",
                }}
              />
              {!isValidJson && (
                <div style={{ padding: "8px 18px 14px", display: "flex", alignItems: "center", gap: "6px" }}>
                  <span style={{ color: T.danger, fontSize: "12px", fontFamily: "var(--font-mono)" }}>&#x2715;</span>
                  <span style={{ color: T.danger, fontSize: "11px", fontFamily: "var(--font-mono)" }}>Invalid JSON array</span>
                </div>
              )}
              <div style={{ padding: "10px 18px", borderTop: `1px solid ${T.glassBorder}` }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.muted }}>UTF-8 &bull; JSON &bull; READ/WRITE</span>
              </div>
            </motion.div>
          </div>

          {/* RIGHT SIDEBAR */}
          <div style={{ display: "flex", flexDirection: "column", gap: "14px", position: "sticky", top: "76px" }}>

            {/* Run Tournament */}
            <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.35, delay: 0.16 }} style={{
              border: `1px solid ${T.glassBorder}`, borderRadius: "14px", background: T.glassBg, backdropFilter: "blur(14px)", padding: "20px"
            }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.accent, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "14px" }}>
                Launch
              </div>

              <button
                onClick={runTournament}
                disabled={!isValidJson || isLoading}
                style={{
                  width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
                  padding: "14px 0", borderRadius: "10px", border: "none",
                  fontFamily: "var(--font-mono)", fontSize: "14px", fontWeight: 700,
                  background: isValidJson ? T.accent : T.border,
                  color: isValidJson ? "#000" : T.muted,
                  cursor: isValidJson && !isLoading ? "pointer" : "not-allowed",
                  letterSpacing: "0.02em",
                  transition: "all 0.2s",
                }}
              >
                {isLoading ? (
                  "RUNNING..."
                ) : (
                  <>
                    <span style={{ fontSize: "16px" }}>&#x25B6;</span>
                    RUN TOURNAMENT
                  </>
                )}
              </button>

              <div style={{ marginTop: "12px", fontSize: "11px", lineHeight: 1.5, color: T.muted, fontFamily: "var(--font-mono)" }}>
                Executing tournament protocol will consume validation credits from infrastructure pool.
              </div>

              {/* Metrics */}

              <div style={{ marginTop: "16px", paddingTop: "14px", borderTop: `1px solid ${T.glassBorder}`, display: "flex", flexDirection: "column", gap: "10px" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: "11px" }}>
                  <span style={{ color: T.muted }}>Compute Latency</span>
                  <span style={{ color: T.text }}>124ms</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: "11px" }}>
                  <span style={{ color: T.muted }}>Available Clusters</span>
                  <span style={{ color: T.text }}>14/18</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: "11px" }}>
                  <span style={{ color: T.muted }}>Success Probability</span>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <span style={{ color: T.success, fontSize: "14px" }}>&#x2713;</span>
                    <span style={{ color: T.success, fontWeight: 600 }}>99.2%</span>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Quick links */}
            <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.35, delay: 0.2 }} style={{
              border: `1px solid ${T.glassBorder}`, borderRadius: "14px", background: T.glassBg, backdropFilter: "blur(14px)", padding: "16px"
            }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.accent, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "10px" }}>
                Quick Actions
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <a href="/player" style={{
                  fontFamily: "var(--font-mono)", fontSize: "12px", color: T.mutedLight, textDecoration: "none",
                  display: "flex", alignItems: "center", gap: "8px", padding: "6px 8px", borderRadius: "6px",
                }}>
                  <span>&#x1F465;</span> Edit Player Profiles
                </a>
                <a href="/" style={{
                  fontFamily: "var(--font-mono)", fontSize: "12px", color: T.mutedLight, textDecoration: "none",
                  display: "flex", alignItems: "center", gap: "8px", padding: "6px 8px", borderRadius: "6px",
                }}>
                  <span>&#x2190;</span> Back to Dashboard
                </a>
              </div>
            </motion.div>

            {/* Status */}
            {status && (
              <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} style={{
                border: `1px solid ${T.glassBorder}`, borderRadius: "14px", background: T.glassBg, backdropFilter: "blur(14px)",
                padding: "14px", fontFamily: "var(--font-mono)", fontSize: "11px", lineHeight: 1.5,
                borderLeft: `3px solid ${status.includes("failed") || status.includes("Failed") ? T.danger : T.accent}`,
              }}>
                {status}
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

export default function NewTournamentPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen flex items-center justify-center" style={{ background: T.bg, color: T.text }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.muted }}>Loading tournament form...</div>
      </main>
    }>
      <NewTournamentContent />
    </Suspense>
  );
}
