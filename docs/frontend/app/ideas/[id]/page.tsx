"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";

const API = process.env.NEXT_PUBLIC_EVIDENTIA_API ?? "http://127.0.0.1:8000";

export default function IdeaTrailPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const ideaId = decodeURIComponent(params.id);
  const initialTournament = searchParams.get("tournament_id") ?? "";
  const [tournamentId, setTournamentId] = useState(initialTournament);
  const [state, setState] = useState<any>(null);
  const [status, setStatus] = useState(initialTournament ? "Loading..." : "Enter tournament id");

  const canLoad = useMemo(() => tournamentId.trim().length > 0, [tournamentId]);

  const load = async () => {
    if (!canLoad) return;
    setStatus("Loading...");
    try {
      const res = await fetch(
        `${API}/tournament/${encodeURIComponent(tournamentId)}/idea/${encodeURIComponent(ideaId)}`,
      );
      if (!res.ok) throw new Error(await res.text());
      setState(await res.json());
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

  return (
    <main style={{ padding: "24px", maxWidth: "1000px", margin: "0 auto" }}>
      <h1 style={{ fontSize: "28px", marginBottom: "8px" }}>Idea Evidence Trail</h1>
      <div style={{ display: "flex", gap: "8px", marginBottom: "12px", flexWrap: "wrap" }}>
        <input
          value={tournamentId}
          onChange={(event) => setTournamentId(event.target.value)}
          placeholder="tournament_id"
          style={{ padding: "8px", minWidth: "260px" }}
        />
        <button onClick={load} style={{ padding: "8px 14px" }} disabled={!canLoad}>
          Load
        </button>
      </div>
      <p style={{ color: "#888", marginBottom: "10px" }}>{status}</p>
      {!state ? null : (
        <section style={{ display: "grid", gap: "10px" }}>
          <article style={{ border: "1px solid #333", borderRadius: "8px", padding: "12px" }}>
            <h2 style={{ marginBottom: "8px" }}>{state.idea.label}</h2>
            <div style={{ color: "#888", fontSize: "13px" }}>{state.idea.cohort}</div>
            <div style={{ marginTop: "6px" }}>Terminal Verdict: {state.terminal_verdict}</div>
            <div>Confidence: {Number(state.confidence_score_so_far || 0).toFixed(3)}</div>
          </article>
          <article style={{ border: "1px solid #333", borderRadius: "8px", padding: "12px" }}>
            <h2 style={{ marginBottom: "8px" }}>Gate Trail</h2>
            <div style={{ display: "grid", gap: "6px" }}>
              {(state.gate_results || []).map((gate: any, idx: number) => (
                <div key={idx} style={{ border: "1px solid #222", borderRadius: "6px", padding: "8px" }}>
                  <div style={{ fontSize: "12px", color: "#9b9b9b" }}>{gate.gate_name}</div>
                  <div style={{ fontSize: "12px" }}>
                    {gate.status} {gate.outcome ? `| ${gate.outcome}` : ""}
                    {typeof gate.confidence === "number" ? ` | conf ${gate.confidence.toFixed(2)}` : ""}
                    {gate.evidence_ids?.length ? ` | evidence ${gate.evidence_ids.join(",")}` : ""}
                  </div>
                </div>
              ))}
            </div>
          </article>
        </section>
      )}
    </main>
  );
}
