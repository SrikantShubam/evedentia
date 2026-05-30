"use client";

import { useEffect, useState, useMemo } from "react";
import { useParams } from "next/navigation";
import { T } from "@/lib/tokens";
import { RealitySpikeCard } from "@/components/RealitySpikeCard";
import { ReentryButton } from "@/components/ReentryButton";

const API = process.env.NEXT_PUBLIC_EVIDENTIA_API ?? "http://127.0.0.1:8000";

export default function TournamentMemoPage() {
  const params = useParams<{ id: string }>();
  const tournamentId = decodeURIComponent(params.id);
  const [memo, setMemo] = useState<any>(null);
  const [tournament, setTournament] = useState<any>(null);
  const [status, setStatus] = useState("Loading...");

  useEffect(() => {
    const run = async () => {
      try {
        const [memoRes, tourneyRes] = await Promise.all([
          fetch(`${API}/tournament/${encodeURIComponent(tournamentId)}/memo`),
          fetch(`${API}/tournament/${encodeURIComponent(tournamentId)}`),
        ]);
        if (!memoRes.ok) throw new Error(await memoRes.text());
        if (!tourneyRes.ok) throw new Error(await tourneyRes.text());
        setMemo(await memoRes.json());
        setTournament(await tourneyRes.json());
        setStatus("Loaded");
      } catch (error) {
        setStatus(`Load failed: ${error instanceof Error ? error.message : String(error)}`);
      }
    };
    void run();
  }, [tournamentId]);

  const reentryDepth = tournament?.reentry_depth ?? 0;
  const playerId = tournament?.player_id ?? "";
  const gateProfile = tournament?.gate_profile ?? "";

  const insufficientIdeas = useMemo(() => {
    if (!memo?.insufficient_evidence) return [];
    return memo.insufficient_evidence
      .map((s: any) => s.idea)
      .filter(Boolean);
  }, [memo]);

  if (status === "Loading...") {
    return (
      <main className="min-h-screen flex items-center justify-center" style={{ background: T.bg, color: T.text }}>
        <div className="text-sm font-mono text-[#666]">Loading memo...</div>
      </main>
    );
  }

  if (!memo) {
    return (
      <main className="min-h-screen flex items-center justify-center" style={{ background: T.bg, color: T.text }}>
        <div className="text-center p-8 rounded-2xl border" style={{ background: T.glassBg, border: `1px solid ${T.glassBorder}`, backdropFilter: "blur(16px)" }}>
          <div className="text-2xl mb-2">Memo not found</div>
          <div className="text-sm text-[#888] mb-4">{status}</div>
          <a href={`/tournament/${encodeURIComponent(tournamentId)}`} className="text-[#e2ff5d] hover:underline">← Back to poker board</a>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen pb-24" style={{ background: T.bg, color: T.text }}>
      <div className="max-w-[1000px] mx-auto px-6 pt-8">
        <a
          href={`/tournament/${encodeURIComponent(tournamentId)}`}
          className="text-xs font-mono text-[#888] hover:text-[#e2ff5d] transition-colors"
        >
          ← Back to poker board
        </a>

        <div className="flex items-center gap-3 mt-4 mb-2">
          <h1 className="text-3xl font-semibold tracking-tight">Decision Memo</h1>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono" style={{ background: T.glassBg, border: `1px solid ${T.glassBorder}`, color: "#888" }}>
            {status}
          </span>
        </div>
        <p className="text-sm font-mono text-[#666] mb-8">
          Tournament: <span className="text-white">{tournamentId}</span>
        </p>

        <div className="space-y-6">
          {/* Winner section */}
          {memo.winner ? (
            <div
              className="rounded-2xl border p-6"
              style={{
                borderColor: "rgba(226,255,93,0.15)",
                background: "rgba(226,255,93,0.06)",
                backdropFilter: "blur(16px)",
              }}
            >
              <div className="font-mono text-xs tracking-[1px] text-[#e2ff5d] uppercase mb-3">
                Winner
              </div>
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-xl font-semibold">{memo.winner.idea?.label ?? "None"}</div>
                  {memo.winner.idea?.cohort && (
                    <div className="text-xs font-mono text-[#888] mt-1">{memo.winner.idea.cohort}</div>
                  )}
                  <div className="mt-2 flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider" style={{ background: "rgba(34,197,94,0.1)", color: "#22c55e", border: "1px solid rgba(34,197,94,0.2)" }}>
                      {memo.winner.terminal_verdict || "PURSUE_SPIKE"}
                    </span>
                    <span className="font-mono text-xs text-[#e2ff5d]">
                      conf {Number(memo.winner.confidence_score_so_far || 0).toFixed(3)}
                    </span>
                  </div>
                </div>
              </div>
              {memo.why_winner_beat_alternatives && (
                <div className="mt-4 text-sm leading-relaxed text-[#ccc]">
                  {memo.why_winner_beat_alternatives}
                </div>
              )}
            </div>
          ) : null}

          {/* RealitySpikeCard */}
          {memo.winner && memo.reality_spike ? (
            <RealitySpikeCard realitySpike={memo.reality_spike} />
          ) : null}

          {/* For / Against */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div
              className="rounded-xl border p-5"
              style={{ background: T.glassBg, borderColor: T.glassBorder, backdropFilter: "blur(16px)" }}
            >
              <div className="font-mono text-[10px] tracking-wider text-[#22c55e] uppercase mb-2">
                Strongest Argument For
              </div>
              <div className="text-sm leading-relaxed">{memo.strongest_argument_for}</div>
            </div>
            <div
              className="rounded-xl border p-5"
              style={{ background: T.glassBg, borderColor: T.glassBorder, backdropFilter: "blur(16px)" }}
            >
              <div className="font-mono text-[10px] tracking-wider text-[#ef4444] uppercase mb-2">
                Strongest Argument Against
              </div>
              <div className="text-sm leading-relaxed">{memo.strongest_argument_against}</div>
            </div>
          </div>

          {/* Missing Evidence Checklist */}
          {memo.missing_evidence_checklist?.length > 0 && (
            <div
              className="rounded-xl border p-5"
              style={{ background: T.glassBg, borderColor: T.glassBorder, backdropFilter: "blur(16px)" }}
            >
              <div className="font-mono text-[10px] tracking-wider text-[#f59e0b] uppercase mb-3">
                Missing Evidence Checklist
              </div>
              <ul className="space-y-1.5">
                {memo.missing_evidence_checklist.map((item: string, idx: number) => (
                  <li key={idx} className="flex gap-2 text-sm text-[#ccc]">
                    <span className="text-[#f59e0b] shrink-0">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Zero Winner Diagnosis */}
          {memo.zero_winner_diagnosis ? (
            <div
              className="rounded-xl border p-5"
              style={{
                borderColor: "rgba(245,158,11,0.25)",
                background: "rgba(245,158,11,0.06)",
                backdropFilter: "blur(8px)",
              }}
            >
              <div className="font-mono text-[10px] tracking-wider text-[#f59e0b] uppercase mb-2">
                Zero Winner Diagnosis
              </div>
              <div className="text-sm leading-relaxed text-[#ddd]">
                {memo.zero_winner_diagnosis}
              </div>
            </div>
          ) : null}

          {/* Shortlist / Insufficient / Killed summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div
              className="rounded-xl border p-4"
              style={{ background: T.glassBg, borderColor: T.glassBorder, backdropFilter: "blur(16px)" }}
            >
              <div className="font-mono text-[10px] tracking-wider text-[#3b82f6] uppercase">
                Shortlist
              </div>
              <div className="mt-1 text-2xl font-semibold tabular-nums">
                {memo.shortlist?.length ?? 0}
              </div>
            </div>
            <div
              className="rounded-xl border p-4"
              style={{ background: T.glassBg, borderColor: T.glassBorder, backdropFilter: "blur(16px)" }}
            >
              <div className="font-mono text-[10px] tracking-wider text-[#f59e0b] uppercase">
                Insufficient Evidence
              </div>
              <div className="mt-1 text-2xl font-semibold tabular-nums">
                {memo.insufficient_evidence?.length ?? 0}
              </div>
            </div>
            <div
              className="rounded-xl border p-4"
              style={{ background: T.glassBg, borderColor: T.glassBorder, backdropFilter: "blur(16px)" }}
            >
              <div className="font-mono text-[10px] tracking-wider text-[#ef4444] uppercase">
                Killed
              </div>
              <div className="mt-1 text-2xl font-semibold tabular-nums">
                {memo.killed?.length ?? 0}
              </div>
            </div>
          </div>

          {/* Reentry buttons for insufficient evidence ideas */}
          {insufficientIdeas.length > 0 && (
            <div
              className="rounded-xl border p-5"
              style={{ background: T.glassBg, borderColor: T.glassBorder, backdropFilter: "blur(16px)" }}
            >
              <div className="font-mono text-[10px] tracking-wider text-[#f59e0b] uppercase mb-3">
                Reentry Available
              </div>
              <div className="space-y-2">
                {insufficientIdeas.map((idea: any) => (
                  <div key={idea.id} className="flex items-center justify-between gap-4 p-3 rounded-lg" style={{ background: T.surface, border: `1px solid ${T.border}` }}>
                    <div className="min-w-0">
                      <div className="text-sm font-medium truncate">{idea.label}</div>
                      <div className="text-[10px] font-mono text-[#666]">{idea.id}</div>
                    </div>
                    <ReentryButton
                      ideaId={idea.id}
                      ideaLabel={idea.label}
                      tournamentId={tournamentId}
                      playerId={playerId}
                      reentryDepth={reentryDepth}
                      maxReentryRounds={3}
                      gateProfile={gateProfile}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
