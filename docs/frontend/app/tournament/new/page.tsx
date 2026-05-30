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

const ANCHORS = ["onboarding-tools", "invoice-reconciliation", "dev-tooling", "crm-for-agencies", "expense-tracking"];
const GATE_PROFILES = ["consumer_app", "b2b_workflow", "browser_extension", "agency_service"];

const glass = {
  card: {
    background: T.glassBg,
    border: `1px solid ${T.glassBorder}`,
    backdropFilter: "blur(16px)",
    borderRadius: "14px",
  } as React.CSSProperties,
  cardAccent: {
    background: T.glassBg,
    border: `1px solid ${T.glassAccentBorder}`,
    backdropFilter: "blur(16px)",
    borderRadius: "14px",
  } as React.CSSProperties,
  input: {
    background: "rgba(255,255,255,0.04)",
    border: `1px solid ${T.glassBorder}`,
    borderRadius: "10px",
    color: T.text,
    outline: "none",
    fontFamily: "var(--font-mono)",
  } as React.CSSProperties,
};

function NewTournamentContent() {
  const [playerId, setPlayerId] = useState("agency-a");
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
    if (prefill && ANCHORS.includes(prefill)) {
      setAnchorSlug(prefill);
    }
    const player = searchParams.get("player");
    if (player) {
      setPlayerId(player);
    }
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

  return (
    <main className="min-h-screen" style={{ background: T.bg, color: T.text }}>
      <div className="max-w-[1200px] mx-auto px-6 py-10">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="mb-10">
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "8px" }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.accent, letterSpacing: "0.12em", textTransform: "uppercase" }}>
              Tournament
            </span>
            <div style={{ flex: 1, height: "1px", background: T.border }} />
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.muted }}>
              New
            </span>
          </div>
          <h1 style={{ fontSize: "36px", fontWeight: 700, letterSpacing: "-0.025em", marginBottom: "8px" }}>
            New Tournament
          </h1>
          <p style={{ color: T.muted, fontSize: "14px", maxWidth: "540px", lineHeight: 1.5 }}>
            Seed ideas from an anchor, preview harvest signals, and run the full gate prosecution pipeline.
          </p>
        </motion.div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: "24px", alignItems: "start" }}>
          {/* Left Column - Main Controls */}
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>

            {/* Player & Profile Card */}
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.05 }} style={glass.card}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "20px" }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.accent, letterSpacing: "0.08em", textTransform: "uppercase" }}>
                  Configuration
                </span>
                <div style={{ flex: 1, height: "1px", background: T.border }} />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
                <div>
                  <label style={{ display: "block", fontFamily: "var(--font-mono)", fontSize: "10px", color: T.mutedLight, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: "6px" }}>
                    PLAYER ID
                  </label>
                  <input
                    value={playerId}
                    onChange={(e) => setPlayerId(e.target.value)}
                    style={{ ...glass.input, width: "100%", padding: "10px 14px", fontSize: "13px" }}
                  />
                </div>
                <div>
                  <label style={{ display: "block", fontFamily: "var(--font-mono)", fontSize: "10px", color: T.mutedLight, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: "6px" }}>
                    ANCHOR
                  </label>
                  <select
                    value={anchorSlug}
                    onChange={(e) => setAnchorSlug(e.target.value)}
                    style={{ ...glass.input, width: "100%", padding: "10px 14px", fontSize: "13px", cursor: "pointer" }}
                  >
                    {ANCHORS.map((a) => (
                      <option key={a} value={a} style={{ background: "#0a0a0a" }}>{a}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div style={{ marginTop: "14px" }}>
                <label style={{ display: "block", fontFamily: "var(--font-mono)", fontSize: "10px", color: T.mutedLight, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: "6px" }}>
                  GATE PROFILE OVERRIDE
                </label>
                <select
                  value={profileOverride}
                  onChange={(e) => setProfileOverride(e.target.value)}
                  style={{ ...glass.input, width: "100%", padding: "10px 14px", fontSize: "13px", cursor: "pointer" }}
                >
                  <option value="" style={{ background: "#0a0a0a" }}> (inferred) </option>
                  {GATE_PROFILES.map((p) => (
                    <option key={p} value={p} style={{ background: "#0a0a0a" }}>{p}</option>
                  ))}
                </select>
              </div>
              <div style={{ marginTop: "16px", paddingTop: "14px", borderTop: `1px solid ${T.border}`, display: "flex", alignItems: "center", gap: "8px", fontSize: "13px" }}>
                <span style={{ color: T.muted, fontFamily: "var(--font-mono)", fontSize: "11px" }}>Inferred:</span>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.accent }}>{inferredProfile}</span>
              </div>
            </motion.div>

            {/* Harvest & Generate Card */}
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.1 }} style={glass.card}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "20px" }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.accent, letterSpacing: "0.08em", textTransform: "uppercase" }}>
                  Signal Pipeline
                </span>
                <div style={{ flex: 1, height: "1px", background: T.border }} />
              </div>

              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
                <div style={{ fontSize: "13px", fontWeight: 500, color: T.mutedLight }}>Harvest Preview</div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted }}>
                  Anchor: <span style={{ color: T.text }}>{anchorSlug}</span>
                </div>
              </div>
              <div style={{ fontSize: "32px", fontWeight: 700, letterSpacing: "-0.02em", marginBottom: "18px" }}>
                {signalCount !== null ? (
                  <span>{signalCount} <span style={{ fontSize: "16px", fontWeight: 400, color: T.muted }}>signals</span></span>
                ) : (
                  <span style={{ color: T.muted }}>—</span>
                )}
              </div>

              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  onClick={previewHarvest}
                  disabled={isHarvesting}
                  style={{
                    flex: 1,
                    padding: "11px 0",
                    borderRadius: "10px",
                    fontFamily: "var(--font-mono)",
                    fontSize: "13px",
                    fontWeight: 600,
                    background: T.accent,
                    color: "#000",
                    border: "none",
                    cursor: isHarvesting ? "not-allowed" : "pointer",
                    opacity: isHarvesting ? 0.5 : 1,
                    transition: "opacity 0.2s",
                  }}
                >
                  {isHarvesting ? "Harvesting..." : "Preview Harvest"}
                </button>
                <button
                  onClick={generateIdeas}
                  disabled={isGenerating}
                  style={{
                    flex: 1,
                    padding: "11px 0",
                    borderRadius: "10px",
                    fontFamily: "var(--font-mono)",
                    fontSize: "13px",
                    fontWeight: 600,
                    background: "transparent",
                    color: T.accent,
                    border: `1px solid ${T.accent}`,
                    cursor: isGenerating ? "not-allowed" : "pointer",
                    opacity: isGenerating ? 0.5 : 1,
                    transition: "opacity 0.2s",
                  }}
                >
                  {isGenerating ? "Generating..." : "Generate Ideas"}
                </button>
              </div>
            </motion.div>

            {/* Seed Ideas Editor */}
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.15 }} style={glass.cardAccent}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.accent, letterSpacing: "0.08em", textTransform: "uppercase" }}>
                    Seed Ideas
                  </span>
                  <span style={{
                    fontFamily: "var(--font-mono)", fontSize: "9px", padding: "2px 6px",
                    borderRadius: "4px", background: T.accentDim, color: T.accent, border: `1px solid ${T.glassAccentBorder}`,
                  }}>
                    JSON
                  </span>
                </div>
                <button
                  onClick={() => setIdeasText(JSON.stringify([SAMPLE_IDEA], null, 2))}
                  style={{
                    fontFamily: "var(--font-mono)", fontSize: "11px", color: T.accent,
                    background: "none", border: "none", cursor: "pointer",
                    textDecoration: "underline", textUnderlineOffset: "2px",
                  }}
                >
                  Load sample
                </button>
              </div>
              <textarea
                value={ideasText}
                onChange={(e) => setIdeasText(e.target.value)}
                style={{
                  width: "100%", minHeight: "380px", resize: "vertical",
                  fontFamily: "var(--font-mono)", fontSize: "12px", lineHeight: 1.55,
                  padding: "16px", borderRadius: "10px",
                  background: "rgba(0,0,0,0.3)",
                  border: isValidJson ? `1px solid ${T.glassBorder}` : "1px solid rgba(239,68,68,0.5)",
                  color: T.text,
                }}
              />
              {!isValidJson && (
                <div style={{ marginTop: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
                  <span style={{ color: T.danger, fontSize: "12px", fontFamily: "var(--font-mono)" }}>✕</span>
                  <span style={{ color: T.danger, fontSize: "12px", fontFamily: "var(--font-mono)" }}>Invalid JSON array</span>
                </div>
              )}
            </motion.div>
          </div>

          {/* Right Sidebar - Controls */}
          <div style={{ display: "flex", flexDirection: "column", gap: "16px", position: "sticky", top: "24px" }}>
            <motion.div initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4, delay: 0.2 }} style={glass.card}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "18px" }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.accent, letterSpacing: "0.08em", textTransform: "uppercase" }}>
                  Launch
                </span>
                <div style={{ flex: 1, height: "1px", background: T.border }} />
              </div>

              <button
                onClick={runTournament}
                disabled={!isValidJson || isLoading}
                style={{
                  width: "100%", padding: "14px 0",
                  borderRadius: "10px", border: "none",
                  fontFamily: "var(--font-mono)", fontSize: "14px", fontWeight: 700,
                  background: isValidJson ? T.accent : T.border,
                  color: isValidJson ? "#000" : T.muted,
                  cursor: isValidJson && !isLoading ? "pointer" : "not-allowed",
                  transition: "all 0.2s",
                  letterSpacing: "0.02em",
                }}
              >
                {isLoading ? "RUNNING TOURNAMENT..." : "RUN TOURNAMENT"}
              </button>

              <div style={{ marginTop: "14px", fontSize: "12px", lineHeight: 1.55, color: T.muted }}>
                Creates a tournament, runs all gates against the seeded ideas, and streams results via SSE.
              </div>

              <div style={{ marginTop: "18px", paddingTop: "16px", borderTop: `1px solid ${T.border}`, display: "flex", flexDirection: "column", gap: "10px" }}>
                <a
                  href="/player"
                  style={{
                    fontFamily: "var(--font-mono)", fontSize: "12px", color: T.mutedLight,
                    textDecoration: "none", display: "flex", alignItems: "center", gap: "8px",
                  }}
                >
                  <span style={{ color: T.accent }}>→</span> Edit Player Profiles
                </a>
                <a
                  href="/"
                  style={{
                    fontFamily: "var(--font-mono)", fontSize: "12px", color: T.mutedLight,
                    textDecoration: "none", display: "flex", alignItems: "center", gap: "8px",
                  }}
                >
                  <span style={{ color: T.accent }}>→</span> Back to Homepage
                </a>
              </div>
            </motion.div>

            {/* Status */}
            {status && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                style={{
                  ...glass.card,
                  padding: "16px",
                  fontFamily: "var(--font-mono)",
                  fontSize: "12px",
                  lineHeight: 1.5,
                  borderLeft: `3px solid ${status.includes("failed") ? T.danger : T.accent}`,
                }}
              >
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
