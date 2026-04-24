"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";

const API = process.env.NEXT_PUBLIC_EVIDENTIA_API ?? "http://127.0.0.1:8000";

type GateEvent = {
  idea_id?: string;
  gate_name?: string;
  status?: string;
  outcome?: string | null;
  confidence?: number | null;
  llm_cost_usd?: number;
};

export default function TournamentBoardPage() {
  const params = useParams<{ id: string }>();
  const tournamentId = decodeURIComponent(params.id);
  const [payload, setPayload] = useState<any>(null);
  const [events, setEvents] = useState<GateEvent[]>([]);
  const [status, setStatus] = useState("Loading...");

  useEffect(() => {
    const run = async () => {
      try {
        const res = await fetch(`${API}/tournament/${encodeURIComponent(tournamentId)}`);
        if (!res.ok) throw new Error(await res.text());
        setPayload(await res.json());
        setStatus("Loaded");
      } catch (error) {
        setStatus(`Load failed: ${error instanceof Error ? error.message : String(error)}`);
      }
    };
    void run();
  }, [tournamentId]);

  useEffect(() => {
    const source = new EventSource(`${API}/tournament/${encodeURIComponent(tournamentId)}/sse`);
    source.addEventListener("gate", (event) => {
      const msg = event as MessageEvent;
      try {
        const parsed = JSON.parse(msg.data) as GateEvent;
        setEvents((prev) => [...prev, parsed]);
      } catch {}
    });
    source.addEventListener("done", () => {
      source.close();
    });
    source.onerror = () => {
      source.close();
    };
    return () => source.close();
  }, [tournamentId]);

  const spend = useMemo(() => events.reduce((sum, event) => sum + Number(event.llm_cost_usd || 0), 0), [events]);
  const grouped = useMemo(() => {
    const byIdea = new Map<string, GateEvent[]>();
    for (const event of events) {
      const key = event.idea_id || "unknown";
      const current = byIdea.get(key) || [];
      current.push(event);
      byIdea.set(key, current);
    }
    return Array.from(byIdea.entries());
  }, [events]);

  return (
    <main style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
      <h1 style={{ fontSize: "28px", marginBottom: "8px" }}>Tournament Board</h1>
      <p style={{ color: "#888", marginBottom: "12px" }}>
        Tournament: <code>{tournamentId}</code> | Status: {status}
      </p>
      <div style={{ display: "flex", gap: "10px", marginBottom: "14px", flexWrap: "wrap" }}>
        <span style={{ border: "1px solid #333", padding: "6px 10px" }}>SSE Events: {events.length}</span>
        <span style={{ border: "1px solid #333", padding: "6px 10px" }}>Running Spend: ${spend.toFixed(2)}</span>
        <a href={`/tournament/${encodeURIComponent(tournamentId)}/memo`} style={{ border: "1px solid #333", padding: "6px 10px", textDecoration: "none" }}>
          Open Memo
        </a>
      </div>

      <div style={{ display: "grid", gap: "12px", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
        {grouped.map(([ideaId, ideaEvents]) => (
          <article key={ideaId} style={{ border: "1px solid #333", borderRadius: "8px", padding: "12px", background: "#101010" }}>
            <header style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
              <strong>{ideaId}</strong>
              <a href={`/ideas/${encodeURIComponent(ideaId)}?tournament_id=${encodeURIComponent(tournamentId)}`} style={{ color: "#d8ff64", textDecoration: "none", fontSize: "12px" }}>
                trail
              </a>
            </header>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              {ideaEvents.map((event, idx) => (
                <div key={`${ideaId}-${idx}`} style={{ border: "1px solid #222", borderRadius: "6px", padding: "8px" }}>
                  <div style={{ fontSize: "12px", color: "#9b9b9b" }}>{event.gate_name}</div>
                  <div style={{ fontSize: "12px" }}>
                    {event.status} {event.outcome ? `| ${event.outcome}` : ""}
                    {typeof event.confidence === "number" ? ` | conf ${event.confidence.toFixed(2)}` : ""}
                  </div>
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>

      {payload && payload.ideas && payload.ideas.length > 0 ? (
        <section style={{ marginTop: "18px" }}>
          <h2 style={{ fontSize: "20px", marginBottom: "8px" }}>Final Snapshot</h2>
          <div style={{ display: "grid", gap: "10px", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))" }}>
            {payload.ideas.map((state: any) => (
              <article key={state.idea.id} style={{ border: "1px solid #2a2a2a", padding: "10px", borderRadius: "8px" }}>
                <strong>{state.idea.label}</strong>
                <div style={{ color: "#9b9b9b", fontSize: "13px" }}>{state.idea.cohort}</div>
                <div style={{ marginTop: "6px" }}>Verdict: {state.terminal_verdict}</div>
                <div>Confidence: {Number(state.confidence_score_so_far || 0).toFixed(3)}</div>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </main>
  );
}
