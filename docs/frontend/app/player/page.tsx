"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_EVIDENTIA_API ?? "http://127.0.0.1:8000";

const DEFAULT_PROFILE = {
  id: "agency-a",
  team: "Edge Agency",
  skills: ["python", "sales"],
  budget_validate_usd: 2500,
  budget_build_usd: 10000,
  budget_reach_usd: 1500,
  weeks_to_ship: 8,
  risk: "med",
  max_llm_calls_per_tournament: 200,
  max_paid_queries_per_tournament: 50,
  max_reentry_rounds: 1,
};

export default function PlayerPage() {
  const [playerJson, setPlayerJson] = useState(JSON.stringify(DEFAULT_PROFILE, null, 2));
  const [lookupId, setLookupId] = useState(DEFAULT_PROFILE.id);
  const [status, setStatus] = useState<string>("");

  const save = async () => {
    setStatus("Saving...");
    try {
      const payload = JSON.parse(playerJson);
      const res = await fetch(`${API}/player`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(await res.text());
      const body = await res.json();
      setLookupId(body.id);
      setStatus(`Saved player ${body.id}`);
    } catch (error) {
      setStatus(`Save failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const load = async () => {
    setStatus("Loading...");
    try {
      const res = await fetch(`${API}/player/${encodeURIComponent(lookupId)}`);
      if (!res.ok) throw new Error(await res.text());
      const body = await res.json();
      setPlayerJson(JSON.stringify(body, null, 2));
      setStatus(`Loaded player ${lookupId}`);
    } catch (error) {
      setStatus(`Load failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  return (
    <main style={{ padding: "24px", maxWidth: "1000px", margin: "0 auto" }}>
      <h1 style={{ fontSize: "28px", marginBottom: "12px" }}>Player Profile</h1>
      <p style={{ marginBottom: "18px", color: "#888" }}>
        Save and retrieve tournament player profiles used for scoring and budget caps.
      </p>
      <div style={{ display: "flex", gap: "8px", marginBottom: "12px", flexWrap: "wrap" }}>
        <button onClick={save} style={{ padding: "8px 14px" }}>Save</button>
        <input
          value={lookupId}
          onChange={(event) => setLookupId(event.target.value)}
          placeholder="player id"
          style={{ padding: "8px", minWidth: "220px" }}
        />
        <button onClick={load} style={{ padding: "8px 14px" }}>Load</button>
      </div>
      <pre style={{ marginBottom: "12px", color: "#a6ffa6" }}>{status}</pre>
      <textarea
        value={playerJson}
        onChange={(event) => setPlayerJson(event.target.value)}
        style={{ width: "100%", minHeight: "500px", padding: "12px", fontFamily: "var(--font-mono)" }}
      />
    </main>
  );
}
