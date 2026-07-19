"use client";

import { useState } from "react";
import { T } from "@/lib/tokens";

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
    <main className="min-h-screen" style={{ background: T.bg, color: T.text }}>
      <div className="max-w-[900px] mx-auto px-6 py-12">
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="text-[#e2ff5d] font-mono text-xs tracking-[2px] uppercase">EVIDENTIA</div>
            <div className="h-px flex-1 bg-[#1f1f1f]" />
          </div>
          <h1 className="text-4xl font-semibold tracking-tight">Player Profiles</h1>
          <p className="mt-2 text-[#888] max-w-md">
            Save and retrieve tournament player profiles used for scoring and budget caps.
          </p>
        </div>

        <div
          className="rounded-2xl border p-6"
          style={{
            background: T.glassBg,
            border: `1px solid ${T.glassBorder}`,
            backdropFilter: "blur(16px)",
          }}
        >
          <div className="font-mono text-[10px] tracking-[1.5px] uppercase mb-4" style={{ color: T.accent }}>
            PLAYER CONFIG
          </div>

          <div className="flex flex-wrap items-center gap-3 mb-4">
            <button
              onClick={save}
              className="px-5 py-2.5 rounded-xl text-sm font-semibold font-mono transition-all active:scale-[0.985]"
              style={{ background: T.accent, color: "#111", border: `1px solid ${T.accent}` }}
            >
              Save
            </button>
            <input
              value={lookupId}
              onChange={(event) => setLookupId(event.target.value)}
              placeholder="player id"
              className="flex-1 min-w-[220px] border px-4 py-2.5 font-mono text-sm focus:outline-none focus:border-[#e2ff5d]/60"
              style={{ background: T.surface, borderColor: T.border, color: T.text, borderRadius: "10px" }}
            />
            <button
              onClick={load}
              className="px-5 py-2.5 rounded-xl text-sm font-semibold font-mono border transition-all active:scale-[0.985]"
              style={{ borderColor: T.accent, color: T.accent }}
            >
              Load
            </button>
          </div>

          <pre className="mb-3 text-xs" style={{ color: T.accent, fontFamily: "var(--font-mono)" }}>{status}</pre>

          <div className="font-mono text-[10px] tracking-[1.5px] uppercase mb-2" style={{ color: "#888" }}>
            JSON PAYLOAD
          </div>
          <textarea
            value={playerJson}
            onChange={(event) => setPlayerJson(event.target.value)}
            className="w-full min-h-[520px] font-mono text-sm p-5 border resize-y focus:outline-none focus:border-[#e2ff5d]/60"
            style={{ background: T.surface, color: T.text, border: `1px solid ${T.border}`, borderRadius: "10px" }}
          />
        </div>

        <div className="mt-4 text-[11px] text-[#666] font-mono">
          Profiles control per-player LLM budgets, reentry limits, and gate scoring behavior.
        </div>
      </div>
    </main>
  );
}
