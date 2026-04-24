"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

const API = process.env.NEXT_PUBLIC_EVIDENTIA_API ?? "http://127.0.0.1:8000";

export default function TournamentMemoPage() {
  const params = useParams<{ id: string }>();
  const tournamentId = decodeURIComponent(params.id);
  const [memo, setMemo] = useState<any>(null);
  const [status, setStatus] = useState("Loading...");

  useEffect(() => {
    const run = async () => {
      try {
        const res = await fetch(`${API}/tournament/${encodeURIComponent(tournamentId)}/memo`);
        if (!res.ok) throw new Error(await res.text());
        setMemo(await res.json());
        setStatus("Loaded");
      } catch (error) {
        setStatus(`Load failed: ${error instanceof Error ? error.message : String(error)}`);
      }
    };
    void run();
  }, [tournamentId]);

  return (
    <main style={{ padding: "24px", maxWidth: "1000px", margin: "0 auto" }}>
      <h1 style={{ fontSize: "28px", marginBottom: "8px" }}>Decision Memo</h1>
      <p style={{ color: "#888", marginBottom: "12px" }}>{status} | Tournament: <code>{tournamentId}</code></p>
      {!memo ? null : (
        <section style={{ display: "grid", gap: "10px" }}>
          <article style={{ border: "1px solid #333", padding: "12px", borderRadius: "8px" }}>
            <h2 style={{ marginBottom: "8px" }}>Winner</h2>
            <div>{memo.winner?.idea?.label ?? "none"}</div>
            <div style={{ color: "#888", fontSize: "13px" }}>{memo.why_winner_beat_alternatives}</div>
          </article>
          <article style={{ border: "1px solid #333", padding: "12px", borderRadius: "8px" }}>
            <h2 style={{ marginBottom: "8px" }}>Arguments</h2>
            <div>For: {memo.strongest_argument_for}</div>
            <div>Against: {memo.strongest_argument_against}</div>
          </article>
          <article style={{ border: "1px solid #333", padding: "12px", borderRadius: "8px" }}>
            <h2 style={{ marginBottom: "8px" }}>Missing Evidence Checklist</h2>
            <ul style={{ marginLeft: "20px" }}>
              {(memo.missing_evidence_checklist || []).map((item: string, idx: number) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </article>
          <article style={{ border: "1px solid #333", padding: "12px", borderRadius: "8px" }}>
            <h2 style={{ marginBottom: "8px" }}>Reality Spike</h2>
            <div>Provenance: {memo.reality_spike?.provenance ?? "none"}</div>
            <div>Headline: {memo.reality_spike?.landing_page_headline ?? "-"}</div>
          </article>
          {memo.zero_winner_diagnosis ? (
            <article style={{ border: "1px solid #333", padding: "12px", borderRadius: "8px" }}>
              <h2 style={{ marginBottom: "8px" }}>Zero Winner Diagnosis</h2>
              <div>{memo.zero_winner_diagnosis}</div>
            </article>
          ) : null}
        </section>
      )}
    </main>
  );
}
