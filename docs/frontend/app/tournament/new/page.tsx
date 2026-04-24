"use client";

import { useMemo, useState } from "react";

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

export default function NewTournamentPage() {
  const [playerId, setPlayerId] = useState("agency-a");
  const [profileOverride, setProfileOverride] = useState("");
  const [ideasText, setIdeasText] = useState(JSON.stringify([SAMPLE_IDEA], null, 2));
  const [status, setStatus] = useState("");
  const inferredProfile = useMemo(() => {
    try {
      const parsed = JSON.parse(ideasText);
      if (!Array.isArray(parsed) || parsed.length === 0) return "n/a";
      return `${parsed[0].gate_profile} (${parsed[0].gate_profile_source})`;
    } catch {
      return "n/a";
    }
  }, [ideasText]);

  const runTournament = async () => {
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
    }
  };

  return (
    <main style={{ padding: "24px", maxWidth: "1100px", margin: "0 auto" }}>
      <h1 style={{ fontSize: "28px", marginBottom: "12px" }}>New Tournament</h1>
      <p style={{ color: "#888", marginBottom: "16px" }}>
        Seed with manual ideas and optionally override the inferred gate profile.
      </p>
      <div style={{ display: "grid", gap: "10px", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", marginBottom: "10px" }}>
        <label style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <span>Player ID</span>
          <input value={playerId} onChange={(event) => setPlayerId(event.target.value)} style={{ padding: "8px" }} />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <span>Profile Override (optional)</span>
          <input
            value={profileOverride}
            onChange={(event) => setProfileOverride(event.target.value)}
            placeholder="consumer_app | b2b_workflow | browser_extension | agency_service"
            style={{ padding: "8px" }}
          />
        </label>
        <label style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <span>Inferred Profile</span>
          <input value={inferredProfile} readOnly style={{ padding: "8px", background: "#1a1a1a" }} />
        </label>
      </div>
      <textarea
        value={ideasText}
        onChange={(event) => setIdeasText(event.target.value)}
        style={{ width: "100%", minHeight: "450px", padding: "12px", fontFamily: "var(--font-mono)" }}
      />
      <div style={{ marginTop: "12px", display: "flex", gap: "8px", flexWrap: "wrap" }}>
        <button onClick={runTournament} style={{ padding: "9px 16px" }}>Run Tournament</button>
        <a href="/player" style={{ padding: "9px 16px", border: "1px solid #333", textDecoration: "none" }}>Edit Player</a>
      </div>
      <pre style={{ marginTop: "10px", color: "#a6ffa6" }}>{status}</pre>
    </main>
  );
}
