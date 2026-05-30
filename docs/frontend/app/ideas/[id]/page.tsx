"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { motion } from "motion/react";
import { T } from "@/lib/tokens";
import { ReentryButton } from "@/components/ReentryButton";

const API = process.env.NEXT_PUBLIC_EVIDENTIA_API ?? "http://127.0.0.1:8000";

function getVerdictColor(verdict: string | undefined): { bg: string; color: string; border: string } {
  switch (verdict) {
    case "PURSUE_SPIKE":
      return { bg: "rgba(34,197,94,0.1)", color: "#22c55e", border: "rgba(34,197,94,0.25)" };
    case "SHORTLIST":
      return { bg: "rgba(245,158,11,0.1)", color: "#f59e0b", border: "rgba(245,158,11,0.25)" };
    case "KILL":
      return { bg: "rgba(239,68,68,0.1)", color: "#ef4444", border: "rgba(239,68,68,0.25)" };
    case "INSUFFICIENT_EVIDENCE":
      return { bg: "rgba(245,158,11,0.1)", color: "#f59e0b", border: "rgba(245,158,11,0.25)" };
    default:
      return { bg: T.glassBg, color: T.mutedLight, border: T.glassBorder };
  }
}

function getGateType(gateName: string): "structural" | "evidence" {
  const structural = ["willingness_to_pay", "distribution_channel", "final_score"];
  return structural.includes(gateName) ? "structural" : "evidence";
}

function humanizeGate(gate: string): string {
  return gate
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export default function IdeaTrailPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const ideaId = decodeURIComponent(params.id);
  const initialTournament = searchParams.get("tournament_id") ?? "";
  const [tournamentId, setTournamentId] = useState(initialTournament);
  const [state, setState] = useState<any>(null);
  const [tournamentContext, setTournamentContext] = useState<any>(null);
  const [status, setStatus] = useState(initialTournament ? "Loading..." : "Enter tournament id");

  const canLoad = useMemo(() => tournamentId.trim().length > 0, [tournamentId]);

  const load = async () => {
    if (!canLoad) return;
    setStatus("Loading...");
    setState(null);
    setTournamentContext(null);

    try {
      const [ideaRes, tourneyRes] = await Promise.all([
        fetch(`${API}/tournament/${encodeURIComponent(tournamentId)}/idea/${encodeURIComponent(ideaId)}`),
        fetch(`${API}/tournament/${encodeURIComponent(tournamentId)}`),
      ]);

      if (!ideaRes.ok) throw new Error(await ideaRes.text());
      const ideaData = await ideaRes.json();
      setState(ideaData);

      if (tourneyRes.ok) {
        setTournamentContext(await tourneyRes.json());
      }

      setStatus("Loaded");
    } catch (error) {
      setStatus(`Load failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  useEffect(() => {
    if (initialTournament) {
      void load();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialTournament, ideaId]);

  const reentryDepth = tournamentContext?.reentry_depth ?? 0;
  const playerId = tournamentContext?.player_id ?? "";
  const gateProfile = tournamentContext?.gate_profile ?? "";
  const MAX_REENTRY = 3;

  const verdict = state?.terminal_verdict as string | undefined;
  const vColors = getVerdictColor(verdict);
  const idea = state?.idea || {};

  return (
    <main className="min-h-screen pb-24" style={{ background: T.bg, color: T.text }}>
      <div className="max-w-[1000px] mx-auto px-6 pt-8">
        {/* Back link */}
        {tournamentId ? (
          <a
            href={`/tournament/${encodeURIComponent(tournamentId)}`}
            className="text-xs font-mono text-[#888] hover:text-[#e2ff5d] transition-colors"
          >
            ← Back to poker board
          </a>
        ) : (
          <a href="/" className="text-xs font-mono text-[#888] hover:text-[#e2ff5d] transition-colors">
            ← Back to homepage
          </a>
        )}

        {/* Header */}
        <div className="mt-4 mb-6">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-3xl font-semibold tracking-tight">{idea.label || ideaId}</h1>
            {idea.cohort && (
              <span
                className="px-2 py-0.5 rounded text-[10px] font-mono"
                style={{ background: T.glassBg, border: `1px solid ${T.glassBorder}`, color: T.mutedLight }}
              >
                {idea.cohort}
              </span>
            )}
          </div>
          <div className="mt-2 text-sm text-[#888] font-mono">Evidence Trail • {ideaId}</div>
        </div>

        {/* Load controls (glass toolbar) */}
        <div
          className="mb-8 flex flex-wrap items-center gap-3 rounded-2xl border p-4"
          style={{ background: T.glassBg, borderColor: T.glassBorder, backdropFilter: "blur(16px)" }}
        >
          <div className="font-mono text-[10px] tracking-[1px] text-[#888] mr-1">TOURNAMENT</div>
          <input
            value={tournamentId}
            onChange={(e) => setTournamentId(e.target.value)}
            placeholder="tournament_id"
            className="flex-1 min-w-[240px] rounded-xl border px-3 py-2 text-sm font-mono"
            style={{ background: T.surface, borderColor: T.border, color: T.text }}
          />
          <button
            onClick={load}
            disabled={!canLoad}
            className="rounded-xl px-5 py-2 text-sm font-medium font-mono tracking-wider transition-all disabled:opacity-50"
            style={{
              background: canLoad ? T.accent : T.glassBg,
              color: canLoad ? "#000" : T.muted,
              border: canLoad ? "none" : `1px solid ${T.glassBorder}`,
            }}
          >
            Load Trail
          </button>
          <span
            className="px-2 py-0.5 rounded text-[10px] font-mono"
            style={{ background: T.glassBg, border: `1px solid ${T.glassBorder}`, color: status.startsWith("Load failed") ? T.danger : T.mutedLight }}
          >
            {status}
          </span>
        </div>

        {!state ? (
          <div className="text-center py-12 text-[#666] text-sm font-mono">Enter a tournament ID and load the evidence trail.</div>
        ) : (
          <div className="space-y-6">
            {/* Idea Info */}
            <div
              className="rounded-2xl border p-5"
              style={{ background: T.glassBg, borderColor: T.glassBorder, backdropFilter: "blur(16px)" }}
            >
              <div className="font-mono text-[10px] tracking-[1px] text-[#888] mb-3">IDEA</div>
              <div className="text-lg font-medium mb-1">{idea.label}</div>
              {idea.cohort && <div className="text-xs font-mono text-[#888] mb-4">{idea.cohort}</div>}

              {idea.pain_hypothesis && (
                <div className="mb-3">
                  <div className="text-[10px] font-mono tracking-wider text-[#888] mb-1">PAIN HYPOTHESIS</div>
                  <div className="text-sm leading-relaxed text-[#ddd]">{idea.pain_hypothesis}</div>
                </div>
              )}

              {idea.kill_condition && (
                <div>
                  <div className="text-[10px] font-mono tracking-wider text-[#888] mb-1">KILL CONDITION</div>
                  <div className="text-sm text-[#ccc]">
                    {typeof idea.kill_condition === "object"
                      ? `${idea.kill_condition.description || ""} ${idea.kill_condition.gate_name ? `(gate: ${idea.kill_condition.gate_name})` : ""}`
                      : String(idea.kill_condition)}
                  </div>
                </div>
              )}
            </div>

            {/* Verdict */}
            <div
              className="rounded-2xl border p-5"
              style={{ background: vColors.bg, borderColor: vColors.border, backdropFilter: "blur(16px)" }}
            >
              <div className="font-mono text-[10px] tracking-[1px] mb-2" style={{ color: T.mutedLight }}>
                TERMINAL VERDICT
              </div>
              <div
                className="inline-block px-3 py-1 rounded-lg text-sm font-mono tracking-[1px] uppercase"
                style={{ background: vColors.bg, color: vColors.color, border: `1px solid ${vColors.border}` }}
              >
                {verdict || "UNKNOWN"}
              </div>
              <div className="mt-2 text-xs font-mono text-[#888]">
                confidence: <span className="text-white">{Number(state.confidence_score_so_far || 0).toFixed(3)}</span>
              </div>
            </div>

            {/* Gate Trail */}
            <div>
              <div className="font-mono text-xs tracking-[1px] text-[#e2ff5d] mb-3 px-1">GATE TRAIL</div>

              <div className="space-y-3">
                {(state.gate_results || []).length === 0 && (
                  <div className="text-sm text-[#888] font-mono p-4 rounded-xl border" style={{ borderColor: T.glassBorder, background: T.glassBg }}>
                    No gate results recorded.
                  </div>
                )}

                {(state.gate_results || []).map((gate: any, idx: number) => {
                  const gName = gate.gate_name || "unknown";
                  const gType = getGateType(gName);
                  const gStatus = (gate.status || "UNKNOWN").toUpperCase();
                  const outcomeRaw = gate.outcome || "";
                  const outcomeLabel = outcomeRaw === "FAIL" ? "FAIL" : outcomeRaw || "—";
                  const conf = typeof gate.confidence === "number" ? gate.confidence : null;
                  const cost = gate.llm_cost_usd ?? 0;

                  const statusColor =
                    gStatus === "COMPLETED" ? T.success : gStatus === "SKIPPED" ? T.warning : gStatus === "ERROR" ? T.danger : T.mutedLight;
                  const outcomeColor = outcomeRaw === "PASS" ? T.success : outcomeRaw === "FAIL" ? T.danger : T.mutedLight;

                  return (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: Math.min(idx * 0.035, 0.4), duration: 0.2 }}
                      className="rounded-2xl border p-4"
                      style={{ background: T.glassBg, borderColor: T.glassBorder, backdropFilter: "blur(16px)" }}
                    >
                      <div className="flex items-start justify-between gap-3 flex-wrap">
                        <div>
                          <div className="font-medium text-[15px]">{humanizeGate(gName)}</div>
                          <div className="text-[10px] font-mono text-[#666] mt-0.5">{gName}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className="px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider"
                            style={{ background: "rgba(255,255,255,0.04)", color: T.mutedLight, border: `1px solid ${T.glassBorder}` }}
                          >
                            {gType}
                          </span>
                          <span
                            className="px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider"
                            style={{ background: `${statusColor}15`, color: statusColor, border: `1px solid ${statusColor}30` }}
                          >
                            {gStatus}
                          </span>
                          <span
                            className="px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider"
                            style={{ background: `${outcomeColor}15`, color: outcomeColor, border: `1px solid ${outcomeColor}30` }}
                          >
                            {outcomeLabel}
                          </span>
                        </div>
                      </div>

                      {/* Confidence bar */}
                      {conf !== null && (
                        <div className="mt-3">
                          <div className="flex items-center justify-between text-[10px] font-mono text-[#888] mb-1">
                            <span>CONFIDENCE</span>
                            <span className="tabular-nums" style={{ color: T.accent }}>{conf.toFixed(3)}</span>
                          </div>
                          <div className="h-1.5 rounded bg-[#1f1f1f] overflow-hidden">
                            <div
                              className="h-1.5 rounded"
                              style={{ width: `${Math.max(0, Math.min(100, Math.round(conf * 100)))}%`, background: T.accent }}
                            />
                          </div>
                        </div>
                      )}

                      {/* Evidence + Cost row */}
                      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs font-mono text-[#888]">
                        {gate.evidence_ids?.length ? (
                          <div>
                            evidence: <span className="text-[#ccc]">{gate.evidence_ids.join(", ")}</span>
                          </div>
                        ) : null}
                        {cost > 0 && (
                          <div className="px-2 py-0.5 rounded" style={{ background: T.glassBg, border: `1px solid ${T.glassBorder}` }}>
                            llm ${cost.toFixed(4)}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>

            {/* ReentryButton for INSUFFICIENT_EVIDENCE */}
            {verdict === "INSUFFICIENT_EVIDENCE" && playerId && (
              <div className="pt-2">
                <div className="font-mono text-[10px] tracking-[1px] text-[#f59e0b] mb-2 px-1">REENTRY</div>
                <ReentryButton
                  ideaId={ideaId}
                  ideaLabel={idea.label || ideaId}
                  tournamentId={tournamentId}
                  playerId={playerId}
                  reentryDepth={reentryDepth}
                  maxReentryRounds={MAX_REENTRY}
                  gateProfile={gateProfile}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
