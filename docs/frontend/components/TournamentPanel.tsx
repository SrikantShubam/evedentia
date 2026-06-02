"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "motion/react";
import { T } from "@/lib/tokens";
import { SwimLanes } from "./SwimLanes";
import { Diagnosis } from "./Diagnosis";
import { BudgetMeter } from "./BudgetMeter";
import { IdeaCard } from "./IdeaCard";
import { ReentryButton } from "./ReentryButton";

const API = process.env.NEXT_PUBLIC_EVIDENTIA_API ?? "http://127.0.0.1:8000";

const GATES = ["willingness_to_pay", "distribution_channel", "data_feasibility", "final_score"];

interface TournamentPanelProps {
  opportunity: ScanOpportunity;
  keyword: string;
  onClose: () => void;
}

interface ScanOpportunity {
  opportunity_id?: string;
  title?: string;
  label?: string;
  hypothesis?: {
    headline?: string;
    wedge_statement?: string;
    hypothesis_type?: string;
  };
  verified_signals?: Array<{ source_url?: string }>;
  verdict?: "PURSUE" | "REFINE" | "KILL";
  final_score?: number;
  score?: number;
  gate_failures?: string[];
  cohort?: string;
  pain_hypothesis?: string;
  [key: string]: unknown;
}

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

type PanelStatus = "IDLE" | "LOADING" | "LIVE" | "COMPLETE" | "ERROR";

export function TournamentPanel({ opportunity, keyword, onClose }: TournamentPanelProps) {
  const [status, setStatus] = useState<PanelStatus>("IDLE");
  const [tournamentId, setTournamentId] = useState<string | null>(null);
  const [events, setEvents] = useState<GateEvent[]>([]);
  const [ideasMap, setIdeasMap] = useState<Record<string, Idea>>({});
  const [eventCount, setEventCount] = useState(0);
  const [apiIdeas, setApiIdeas] = useState<any[]>([]);
  const [zeroWinnerDiagnosis, setZeroWinnerDiagnosis] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [payload, setPayload] = useState<any>(null);
  const [retryNonce, setRetryNonce] = useState(0);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    let cancelled = false;
    let es: EventSource | null = null;

    const run = async () => {
      setStatus("LOADING");
      setErrorMessage(null);
      setEvents([]);
      setIdeasMap({});
      setEventCount(0);
      setApiIdeas([]);
      setZeroWinnerDiagnosis(null);
      setPayload(null);
      setTournamentId(null);

      try {
        const res = await fetch(`${API}/validate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            keyword,
            opportunity,
            player_id: "default",
          }),
        });

        if (!res.ok) {
          const txt = await res.text().catch(() => "");
          throw new Error(txt || "Validation failed");
        }

        const data = await res.json();
        const id: string = data.tournament_id;
        if (!id) throw new Error("No tournament_id in response");

        if (cancelled) return;
        setTournamentId(id);

        const tRes = await fetch(`${API}/tournament/${encodeURIComponent(id)}`);
        if (tRes.ok) {
          const tData = await tRes.json();
          if (cancelled) return;
          setPayload(tData);

          if (tData.ideas) {
            const map: Record<string, Idea> = {};
            tData.ideas.forEach((i: any) => {
              map[i.id] = { ...i, status: "PENDING" as const };
            });
            setIdeasMap(map);
            setApiIdeas(tData.ideas);
          }
          if (tData.memo?.zero_winner_diagnosis) {
            setZeroWinnerDiagnosis(tData.memo.zero_winner_diagnosis);
          }
        }

        if (cancelled) return;
        setStatus("LIVE");

        const url = `${API}/tournament/${encodeURIComponent(id)}/sse`;
        es = new EventSource(url);
        esRef.current = es;

        es.addEventListener("gate", (event) => {
          const msg = event as MessageEvent;
          try {
            const parsed = JSON.parse(msg.data) as GateEvent;
            setEvents((prev) => {
              const next = [...prev, parsed];
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
          setStatus("COMPLETE");
        });

        es.onerror = () => {
          if (es) {
            es.close();
            es = null;
            esRef.current = null;
          }
          setStatus("ERROR");
          setErrorMessage("SSE connection lost");
        };
      } catch (err) {
        if (!cancelled) {
          setStatus("ERROR");
          setErrorMessage(err instanceof Error ? err.message : String(err));
        }
      }
    };

    void run();

    return () => {
      cancelled = true;
      if (es) {
        es.close();
        esRef.current = null;
      }
    };
  }, [keyword, opportunity, retryNonce]);

  const spend = useMemo(
    () => events.reduce((sum, e) => sum + Number(e.llm_cost_usd || 0), 0),
    [events]
  );

  const ideasList = useMemo(() => Object.values(ideasMap), [ideasMap]);

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

  const hasPursueWinner = useMemo(
    () => apiIdeas.some((i: any) => i?.terminal_verdict === "PURSUE_SPIKE"),
    [apiIdeas]
  );

  const terminalVerdicts = useMemo(() => {
    const map: Record<string, string> = {};
    apiIdeas.forEach((i: any) => {
      const id = i?.id;
      if (id) map[id] = i?.terminal_verdict;
    });
    return map;
  }, [apiIdeas]);

  const snapshotIdeas = useMemo(
    () => apiIdeas.filter((raw: any) => {
      const tv = terminalVerdicts[raw.id] ?? raw?.terminal_verdict;
      return tv !== "KILL";
    }),
    [apiIdeas, terminalVerdicts]
  );

  const reentryDepth = payload?.reentry_depth ?? 0;
  const playerId = payload?.player_id ?? "";
  const gateProfile = payload?.gate_profile ?? "";
  const MAX_REENTRY_ROUNDS = 3;

  const isLive = status === "LIVE";
  const isComplete = status === "COMPLETE";
  const isLoading = status === "LOADING";
  const isError = status === "ERROR";

  const statusColor = status === "COMPLETE" ? T.success : status === "ERROR" ? T.danger : status === "LIVE" ? T.accent : T.warning;

  const handleRetry = () => {
    setRetryNonce((n) => n + 1);
  };

  if (status === "IDLE") return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ marginBottom: "46px" }}
    >
      <div style={{ background: T.glassBg, border: `1px solid ${T.glassBorder}`, backdropFilter: "blur(14px)", borderRadius: "12px", padding: "16px" }}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px", flexWrap: "wrap" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "2px", padding: "2px 8px", borderRadius: "4px", border: `1px solid ${statusColor}`, color: statusColor }}>
            TOURNAMENT
          </span>
          {tournamentId && (
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "14px", fontWeight: 600, color: T.text, maxWidth: "240px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {tournamentId}
            </span>
          )}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontFamily: "var(--font-mono)", fontSize: "12px" }}>
            <span style={{ padding: "2px 8px", borderRadius: "4px", background: T.glassBg, border: `1px solid ${T.glassBorder}` }}>
              events: <span style={{ color: T.accent }}>{eventCount}</span>
            </span>
            <span style={{ padding: "2px 8px", borderRadius: "4px", background: T.glassBg, border: `1px solid ${T.glassBorder}` }}>
              spend: <span style={{ color: T.accent }}>${spend.toFixed(2)}</span>
            </span>
          </div>
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted }}>
              {status}{isLive ? " \u2022 SSE live" : ""}
            </span>
            <button
              onClick={onClose}
              style={{
                background: T.glassBg,
                border: `1px solid ${T.glassBorder}`,
                borderRadius: "6px",
                color: T.mutedLight,
                cursor: "pointer",
                fontSize: "14px",
                padding: "4px 8px",
                fontFamily: "var(--font-mono)",
              }}
              title="Close tournament panel"
            >
              \u2715
            </button>
          </div>
        </div>

        {/* BudgetMeter */}
        {(isLive || isComplete) && (
          <div style={{ marginBottom: "16px" }}>
            <BudgetMeter
              llmUsed={Math.floor(eventCount * 1.6)}
              llmMax={600}
              searchUsed={Math.floor(eventCount * 0.8)}
              searchMax={400}
              spend={spend}
              spendMax={85}
            />
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", padding: "24px" }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: T.muted }}>Creating tournament...</span>
          </div>
        )}

        {/* Error */}
        {isError && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "12px", padding: "24px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.danger, textAlign: "center" }}>
              {errorMessage || "An error occurred"}
            </div>
            <button
              onClick={handleRetry}
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "12px",
                padding: "8px 16px",
                borderRadius: "8px",
                border: `1px solid ${T.glassAccentBorder}`,
                background: T.glassAccentBg,
                color: T.accent,
                cursor: "pointer",
              }}
            >
              Retry
            </button>
          </div>
        )}

        {/* SwimLanes during LIVE */}
        {isLive && (
          <div style={{ marginBottom: "12px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted, marginBottom: "8px", letterSpacing: "1px" }}>
              POKER BOARD
            </div>
            <SwimLanes gates={GATES} lanes={swimlanes} />
          </div>
        )}

        {/* Complete state: Final Snapshot + Diagnosis */}
        {isComplete && (
          <>
            {snapshotIdeas.length > 0 && (
              <div style={{ marginBottom: !hasPursueWinner && apiIdeas.length > 0 ? "16px" : 0 }}>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.accent, marginBottom: "12px", letterSpacing: "1px" }}>
                  FINAL SNAPSHOT
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "12px" }}>
                  {snapshotIdeas.map((raw: any) => {
                    const ideaId = raw.id;
                    const ideaLabel = raw.label ?? ideaId;
                    const tVerdict = terminalVerdicts[ideaId] ?? raw?.terminal_verdict;

                    const cardIdea: Idea = {
                      id: raw.id,
                      label: raw.label,
                      confidence: raw.confidence_score_so_far ?? 0,
                      kill_risk: raw.kill_risk,
                      quote: raw.quote,
                      cost_usd: raw.cost_usd,
                      status: (tVerdict === "PURSUE_SPIKE" ? "PASS" : tVerdict === "KILL" ? "FAIL" : tVerdict === "INSUFFICIENT_EVIDENCE" ? "SKIPPED" : "PENDING") as any,
                    };

                    return (
                      <div key={ideaId} style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                        <IdeaCard idea={cardIdea} />
                        {tVerdict === "INSUFFICIENT_EVIDENCE" && playerId && (
                          <ReentryButton
                            ideaId={ideaId}
                            ideaLabel={ideaLabel}
                            tournamentId={tournamentId || ""}
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

            {!hasPursueWinner && apiIdeas.length > 0 && (
              <Diagnosis
                ideas={apiIdeas}
                zeroWinnerDiagnosis={zeroWinnerDiagnosis}
                totalSpend={spend}
              />
            )}
          </>
        )}
      </div>
    </motion.div>
  );
}
