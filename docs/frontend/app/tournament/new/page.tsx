"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
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

  // Prefill support: ?prefill=anchor_slug (e.g. onboarding-tools) and ?player=playerId
  // Guard with ref ensures prefill happens only once on initial load (does not fight controlled state or override later user input)
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
      <div className="max-w-[1100px] mx-auto px-6 py-12">
        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="text-[#e2ff5d] font-mono text-xs tracking-[2px] uppercase">EVIDENTIA</div>
            <div className="h-px flex-1 bg-[#1f1f1f]" />
          </div>
          <h1 className="text-4xl font-semibold tracking-tight">New Tournament</h1>
          <p className="mt-2 text-[#888] max-w-md">
            Seed ideas, choose a gate profile, and run the full prosecution pipeline.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column - Main Controls */}
          <div className="lg:col-span-7 space-y-6">
            {/* Player & Profile */}
            <div className="rounded-2xl border p-6" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", backdropFilter: "blur(16px)" }}>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-widest text-[#888] mb-2">
                    PLAYER ID
                  </label>
                  <input
                    value={playerId}
                    onChange={(e) => setPlayerId(e.target.value)}
                    className="w-full bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg px-4 py-2.5 font-mono text-sm focus:outline-none focus:border-[#e2ff5d]/60"
                    style={{ color: T.text }}
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono uppercase tracking-widest text-[#888] mb-2">
                    ANCHOR
                  </label>
                  <select
                    value={anchorSlug}
                    onChange={(e) => setAnchorSlug(e.target.value)}
                    className="w-full bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg px-4 py-2.5 font-mono text-sm focus:outline-none focus:border-[#e2ff5d]/60"
                    style={{ color: T.text }}
                  >
                    {ANCHORS.map((a) => (
                      <option key={a} value={a}>{a}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-widest text-[#888] mb-2">
                    GATE PROFILE OVERRIDE
                  </label>
                  <select
                    value={profileOverride}
                    onChange={(e) => setProfileOverride(e.target.value)}
                    className="w-full bg-[#0a0a0a] border border-[#1f1f1f] rounded-lg px-4 py-2.5 font-mono text-sm focus:outline-none focus:border-[#e2ff5d]/60"
                    style={{ color: T.text }}
                  >
                    <option value=""> (inferred) </option>
                    {GATE_PROFILES.map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-[#1f1f1f] flex items-center gap-2 text-sm">
                <span className="text-[#666]">Inferred from ideas:</span>
                <span className="font-mono text-[#e2ff5d]">{inferredProfile}</span>
              </div>
            </div>

            {/* Harvest Preview */}
            <div className="rounded-2xl border p-6" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", backdropFilter: "blur(16px)" }}>
              <div className="flex items-center justify-between mb-3">
                <div>
                  <div className="text-xs font-mono uppercase tracking-[1px] text-[#888]">HARVEST PREVIEW</div>
                  <div className="text-2xl font-semibold mt-1">
                    {signalCount !== null ? `${signalCount} signals` : "—"}
                  </div>
                </div>
                <div className="text-right text-xs font-mono text-[#666]">
                  Anchor: {anchorSlug}
                </div>
              </div>

              <div className="flex gap-3 mt-4">
                <button
                  onClick={previewHarvest}
                  disabled={isHarvesting}
                  className="flex-1 py-3 rounded-xl text-sm font-medium transition-all active:scale-[0.985] disabled:opacity-60"
                  style={{ background: T.accent, color: "#111" }}
                >
                  {isHarvesting ? "Harvesting..." : "Preview Harvest"}
                </button>
                <button
                  onClick={generateIdeas}
                  disabled={isGenerating}
                  className="flex-1 py-3 rounded-xl text-sm font-medium border transition-all active:scale-[0.985] disabled:opacity-60"
                  style={{ borderColor: T.accent, color: T.accent }}
                >
                  {isGenerating ? "Generating..." : "Generate Ideas"}
                </button>
              </div>
            </div>

            {/* Ideas JSON Editor */}
            <div>
              <div className="flex items-center justify-between mb-2 px-1">
                <div className="text-xs font-mono uppercase tracking-widest text-[#888]">SEED IDEAS (JSON)</div>
                <button
                  onClick={() => setIdeasText(JSON.stringify([SAMPLE_IDEA], null, 2))}
                  className="text-xs text-[#e2ff5d] hover:underline"
                >
                  Load sample
                </button>
              </div>

              <textarea
                value={ideasText}
                onChange={(e) => setIdeasText(e.target.value)}
                className={`w-full min-h-[420px] font-mono text-sm p-5 rounded-2xl border resize-y focus:outline-none ${
                  isValidJson ? "border-[#1f1f1f]" : "border-red-500/60"
                }`}
                style={{ background: "#0a0a0a", color: T.text }}
              />

              {!isValidJson && (
                <p className="text-red-400 text-xs mt-2 ml-1">Invalid JSON array</p>
              )}
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="lg:col-span-5 space-y-6">
            <div className="rounded-2xl border p-6 sticky top-8" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", backdropFilter: "blur(16px)" }}>
              <div className="text-xs font-mono uppercase tracking-[1px] text-[#888] mb-4">TOURNAMENT CONTROLS</div>

              <button
                onClick={runTournament}
                disabled={!isValidJson || isLoading}
                className="w-full py-3.5 rounded-2xl text-base font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.985]"
                style={{
                  background: isValidJson ? T.accent : "#222",
                  color: isValidJson ? "#111" : "#666",
                }}
              >
                {isLoading ? "RUNNING TOURNAMENT..." : "RUN TOURNAMENT"}
              </button>

              <div className="mt-4 text-[12px] leading-relaxed text-[#666]">
                This will create a new tournament, run all gates against the seeded ideas, and stream results via SSE.
              </div>

              <div className="mt-6 pt-6 border-t border-[#1f1f1f] flex flex-col gap-3">
                <a
                  href="/player"
                  className="text-sm text-[#888] hover:text-white transition-colors flex items-center gap-2"
                >
                  → Edit Player Profiles
                </a>
                <a
                  href="/"
                  className="text-sm text-[#888] hover:text-white transition-colors flex items-center gap-2"
                >
                  → Back to Homepage
                </a>
              </div>
            </div>

            {/* Status */}
            {status && (
              <div className="rounded-2xl border p-4 text-sm font-mono" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", backdropFilter: "blur(16px)" }}>
                {status}
              </div>
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
        <div className="font-mono text-sm text-[#666]">Loading tournament form...</div>
      </main>
    }>
      <NewTournamentContent />
    </Suspense>
  );
}
