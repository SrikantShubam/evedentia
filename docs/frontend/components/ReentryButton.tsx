"use client";

import { useState } from "react";
import { T } from "@/lib/tokens";

const API = process.env.NEXT_PUBLIC_EVIDENTIA_API ?? "http://127.0.0.1:8000";

interface ReentryButtonProps {
  ideaId: string;
  ideaLabel: string;
  tournamentId: string;
  playerId: string;
  reentryDepth: number;
  maxReentryRounds: number;
  gateProfile: string;
}

export function ReentryButton({
  ideaId,
  ideaLabel,
  tournamentId,
  playerId,
  reentryDepth,
  maxReentryRounds,
  gateProfile,
}: ReentryButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isDisabled = reentryDepth >= maxReentryRounds;

  const handleClick = async () => {
    if (isDisabled || loading) return;
    setLoading(true);
    setError(null);

    const newId = crypto.randomUUID();
    const idea = {
      id: `${ideaId}-reentry`,
      label: `narrower: ${ideaLabel}`,
      anchor_slug: "unknown",
      incumbent: "",
      cohort: `narrower: ${ideaLabel}`,
      pain_hypothesis: "",
      kill_condition: { description: "", gate_name: "willingness_to_pay" },
      evidence_ids: [],
      search_queries: [],
      origin: "reentry",
      gate_profile: gateProfile,
      gate_profile_source: "player",
      parent_idea_id: ideaId,
      evidence_provenance: {},
    };

    try {
      const res = await fetch(`${API}/tournament`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tournament_id: newId,
          player_id: playerId,
          ideas: [idea],
          gate_profile: gateProfile,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      window.location.href = `/tournament/${encodeURIComponent(newId)}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button
        onClick={handleClick}
        disabled={isDisabled || loading}
        className="text-xs font-mono tracking-wider px-3 py-1.5 rounded-xl transition-all"
        style={{
          background: isDisabled ? "transparent" : T.glassAccentBg,
          border: `1px solid ${isDisabled ? T.border : T.glassAccentBorder}`,
          color: isDisabled ? T.muted : T.accent,
          cursor: isDisabled ? "not-allowed" : "pointer",
          opacity: loading ? 0.6 : 1,
        }}
        title={
          isDisabled
            ? "Max reentry rounds reached"
            : "Seed a narrower tournament from this idea"
        }
      >
        {loading ? "Seeding..." : "Seed narrower tournament →"}
      </button>
      {error && (
        <div className="text-[10px] mt-1 font-mono" style={{ color: T.danger }}>{error}</div>
      )}
    </div>
  );
}
