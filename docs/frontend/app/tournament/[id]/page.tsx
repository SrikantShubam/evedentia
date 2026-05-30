"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "motion/react";
import { T } from "@/lib/tokens";
import { IdeaCard } from "@/components/IdeaCard";
import { SwimLanes } from "@/components/SwimLanes";
import { BudgetMeter } from "@/components/BudgetMeter";
import { Diagnosis } from "@/components/Diagnosis";
import { ReentryButton } from "@/components/ReentryButton";

const API = process.env.NEXT_PUBLIC_EVIDENTIA_API ?? "http://127.0.0.1:8000";

type GateEvent = {
  idea_id?: string;
  gate_name?: string;
  status?: string;
  outcome?: string | null;
  confidence?: number | null;
  llm_cost_usd?: number;
  quote?: string;
};

type Idea = {
  id: string;
  label: string;
  confidence?: number;
  kill_risk?: number;
  quote?: string;
  cost_usd?: number;
  status?: "PENDING" | "PASS" | "FAIL" | "HOLD" | "SKIPPED";
  current_gate?: string;
};

const GATES = ["willingness_to_pay", "distribution_channel", "data_feasibility", "final_score"];

export default function TournamentBoardPage() {
  const params = useParams<{ id: string }>();
  const tournamentId = decodeURIComponent(params.id);

  const [payload, setPayload] = useState<any>(null);
  const [events, setEvents] = useState<GateEvent[]>([]);
  const [status, setStatus] = useState("Loading...");
  const [ideasMap, setIdeasMap] = useState<Record<string, Idea>>({});
  const [eventCount, setEventCount] = useState(0);
  const [apiIdeas, setApiIdeas] = useState<any[]>([]);
  const [zeroWinnerDiagnosis, setZeroWinnerDiagnosis] = useState<string | null>(null);

  // Load initial tournament data
  useEffect(() => {
    const run = async () => {
      try {
        const res = await fetch(`${API}/tournament/${encodeURIComponent(tournamentId)}`);
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        setPayload(data);

        // Seed ideas from payload if present (IdeaState now has flat id/label at top level)
        if (data.ideas) {
          const map: Record<string, Idea> = {};
          data.ideas.forEach((i: any) => {
            // now works directly with .id (flattened in IdeaState.to_dict)
            map[i.id] = { ...i, status: "PENDING" };
          });
          setIdeasMap(map);
          setApiIdeas(data.ideas);
        }
        if (data.memo?.zero_winner_diagnosis) {
          setZeroWinnerDiagnosis(data.memo.zero_winner_diagnosis);
        }
        setStatus("Live");
      } catch (error) {
        setStatus(`Load failed: ${error instanceof Error ? error.message : String(error)}`);
      }
    };
    void run();
  }, [tournamentId]);

  // SSE connection with auto-reconnect (exponential backoff)
  useEffect(() => {
    let es: EventSource | null = null;
    let retryCount = 0;
    let reconnectTimer: any = null;

    const connect = () => {
      if (es) {
        try { es.close(); } catch {}
      }
      const url = `${API}/tournament/${encodeURIComponent(tournamentId)}/sse`;
      es = new EventSource(url);

      es.addEventListener("gate", (event) => {
        const msg = event as MessageEvent;
        try {
          const parsed = JSON.parse(msg.data) as GateEvent;
          setEvents((prev) => {
            const next = [...prev, parsed];
            // update spend live
            return next;
          });
          setEventCount((c) => c + 1);

          if (parsed.idea_id) {
            setIdeasMap((prev) => {
              const existing = prev[parsed.idea_id!] || { id: parsed.idea_id!, label: parsed.idea_id! };
              const newStatus = parsed.outcome === "PASS" ? "PASS" : parsed.outcome === "FAIL" ? "FAIL" : (existing.status || "PENDING");
              const updated: Idea = {
                ...existing,
                status: newStatus as any,
                confidence: parsed.confidence ?? existing.confidence,
                cost_usd: (existing.cost_usd || 0) + (parsed.llm_cost_usd || 0),
                quote: parsed.quote ?? existing.quote,
                current_gate: parsed.gate_name ?? existing.current_gate,
              };
              return { ...prev, [parsed.idea_id!]: updated };
            });
          }
        } catch {}
      });

      es.addEventListener("done", () => {
        if (es) es.close();
        setStatus("Complete");
        retryCount = 0;
      });

      es.onerror = () => {
        if (es) {
          try { es.close(); } catch {}
          es = null;
        }
        const delay = Math.min(1000 * Math.pow(2, retryCount), 30000);
        retryCount += 1;
        setStatus(`Reconnecting in ${Math.round(delay/1000)}s...`);
        reconnectTimer = setTimeout(connect, delay);
      };
    };

    connect();

    return () => {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (es) es.close();
    };
  }, [tournamentId]);

  // Derived state
  const spend = useMemo(
    () => events.reduce((sum, e) => sum + Number(e.llm_cost_usd || 0), 0),
    [events]
  );

  const ideasList = useMemo(() => Object.values(ideasMap), [ideasMap]);

  // Group ideas by current_gate so cards sit in their gate column.
  // Visual state (PASS/FAIL/SKIPPED/PENDING) is handled by IdeaCard (opacity, border, shimmer).
  // FAIL and SKIPPED remain visible (faded/shimmer) in the column where they were prosecuted.
  const swimlanes = useMemo(() => {
    const lanes: Record<string, Idea[]> = {
      willingness_to_pay: [],
      distribution_channel: [],
      data_feasibility: [],
      final_score: [],
    };

    ideasList.forEach((idea) => {
      const gate = (idea.current_gate || "willingness_to_pay") as keyof typeof lanes;
      if (lanes[gate]) {
        lanes[gate].push(idea);
      } else {
        lanes.willingness_to_pay.push(idea);
      }
    });

    return lanes;
  }, [ideasList]);

  // Error / empty state
  if (status.startsWith("Load failed") || !tournamentId) {
    return (
      <main className="min-h-screen flex items-center justify-center" style={{ background: T.bg, color: T.text }}>
        <div className="text-center p-8 rounded-2xl border" style={{ background: T.glassBg, border: `1px solid ${T.glassBorder}`, backdropFilter: "blur(16px)" }}>
          <div className="text-2xl mb-2">Tournament not found</div>
          <div className="text-sm text-[#888] mb-4">{status}</div>
          <a href="/" className="text-[#e2ff5d] hover:underline">← Back to homepage</a>
        </div>
      </main>
    );
  }

  const isComplete = status === "Complete";

  // Winner check: Diagnosis only renders for zero-winner (no PURSUE_SPIKE)
  const hasPursueWinner = useMemo(
    () => apiIdeas.some((i: any) => i?.terminal_verdict === "PURSUE_SPIKE"),
    [apiIdeas]
  );

  // Map terminal_verdict by idea id for ReentryButton show/hide
  const terminalVerdicts = useMemo(() => {
    const map: Record<string, string> = {};
    apiIdeas.forEach((i: any) => {
      const id = i?.id;
      if (id) map[id] = i?.terminal_verdict;
    });
    return map;
  }, [apiIdeas]);

  // Reentry context from tournament payload (for INSUFFICIENT_EVIDENCE re-seeding)
  const reentryDepth = payload?.reentry_depth ?? 0;
  const playerId = payload?.player_id ?? "";
  const gateProfile = payload?.gate_profile ?? "";
  const MAX_REENTRY_ROUNDS = 3;

  return (
    <main className="min-h-screen pb-24" style={{ background: T.bg, color: T.text }}>
      <div className="max-w-[1400px] mx-auto px-6 pt-8">
        {/* Header bar per spec: ID badge, event count, running spend, View Memo */}
        <div className="sticky top-0 z-50 -mx-6 px-6 py-3 mb-6" style={{ background: "rgba(10,10,10,0.92)", backdropFilter: "blur(12px)", borderBottom: `1px solid ${T.border}` }}>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] tracking-[2px] px-2 py-0.5 rounded border" style={{ borderColor: T.accent, color: T.accent }}>TOURNAMENT</span>
              <span className="font-mono text-lg font-semibold text-white">{tournamentId}</span>
            </div>

            <div className="flex items-center gap-4 text-sm font-mono">
              <span className="px-2 py-0.5 rounded" style={{ background: T.glassBg, border: `1px solid ${T.glassBorder}` }}>
                events: <span className="text-[#e2ff5d]">{eventCount}</span>
              </span>
              <span className="px-2 py-0.5 rounded" style={{ background: T.glassBg, border: `1px solid ${T.glassBorder}` }}>
                spend: <span className="text-[#e2ff5d]">${spend.toFixed(2)}</span>
              </span>
            </div>

            <div className="ml-auto flex items-center gap-3">
              <span className="text-xs text-[#666] font-mono">{status} • SSE {status === "Complete" ? "closed" : "live"}</span>
              <a
                href={`/tournament/${encodeURIComponent(tournamentId)}/memo`}
                className="px-4 py-1.5 rounded-xl text-sm font-medium border transition-all hover:bg-white/5"
                style={{ borderColor: T.border }}
              >
                View Memo →
              </a>
            </div>
          </div>

          {/* BudgetMeter kept for detail (glass already in component) */}
          <div className="mt-3">
            <BudgetMeter
              llmUsed={Math.floor(eventCount * 1.6)}
              llmMax={600}
              searchUsed={Math.floor(eventCount * 0.8)}
              searchMax={400}
              spend={spend}
              spendMax={85}
            />
          </div>
        </div>

        {/* Poker Board title */}
        <div className="flex items-end justify-between mb-4 px-1">
          <h2 className="text-2xl font-semibold tracking-tight">Poker Board</h2>
          <div className="text-xs font-mono text-[#666]">Real-time gate prosecution via SSE</div>
        </div>

        {/* SwimLanes (horizontal scrollable glass columns) */}
        <div className="mb-8">
          <SwimLanes
            gates={GATES}
            lanes={swimlanes}
            onIdeaTrail={(id) => {
              window.location.href = `/ideas/${encodeURIComponent(id)}`;
            }}
          />
        </div>

        {/* Final snapshot grid when complete */}
        {isComplete && apiIdeas.length > 0 && (
          <div className="mt-10">
            <div className="font-mono text-xs tracking-[1px] text-[#e2ff5d] mb-3 px-1">FINAL SNAPSHOT</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-3">
              {apiIdeas.map((raw: any) => {
                // Final Snapshot: direct flat id/label (IdeaState.to_dict now promotes them)
                const ideaId = raw.id;
                const ideaLabel = raw.label ?? ideaId;
                const tVerdict = terminalVerdicts[ideaId] ?? raw?.terminal_verdict;

                const cardIdea = {
                  id: raw.id,
                  label: raw.label,
                  confidence: raw.confidence_score_so_far ?? 0,
                  kill_risk: raw.kill_risk,
                  quote: raw.quote,
                  cost_usd: raw.cost_usd,
                  status: (tVerdict === "PURSUE_SPIKE" ? "PASS" : tVerdict === "KILL" ? "FAIL" : tVerdict === "INSUFFICIENT_EVIDENCE" ? "SKIPPED" : "PENDING") as any,
                };

                return (
                  <div key={ideaId} className="space-y-2">
                    <IdeaCard
                      idea={cardIdea}
                      onTrail={(id) =>
                        (window.location.href = `/ideas/${encodeURIComponent(id)}?tournament_id=${encodeURIComponent(tournamentId)}`)
                      }
                    />
                    {tVerdict === "INSUFFICIENT_EVIDENCE" && playerId && (
                      <ReentryButton
                        ideaId={ideaId}
                        ideaLabel={ideaLabel}
                        tournamentId={tournamentId}
                        playerId={playerId}
                        reentryDepth={reentryDepth}
                        maxReentryRounds={MAX_REENTRY_ROUNDS}
                        gateProfile={gateProfile}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Diagnosis: only when no PURSUE_SPIKE winner (zero-winner case) */}
        {!hasPursueWinner && apiIdeas.length > 0 && (
          <Diagnosis
            ideas={apiIdeas}
            zeroWinnerDiagnosis={zeroWinnerDiagnosis}
            totalSpend={spend}
          />
        )}
      </div>
    </main>
  );
}
