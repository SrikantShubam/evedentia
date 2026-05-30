"use client";

import { T } from "@/lib/tokens";
import { IdeaCard } from "@/components/IdeaCard";
import { motion } from "motion/react";

interface Idea {
  id: string;
  label: string;
  confidence?: number;
  kill_risk?: number;
  quote?: string;
  cost_usd?: number;
  status?: "PENDING" | "PASS" | "FAIL" | "HOLD" | "SKIPPED";
  current_gate?: string;
}

interface SwimLanesProps {
  gates: string[];
  lanes: Record<string, Idea[]>;
  onIdeaTrail?: (ideaId: string) => void;
}

const GATE_META: Record<string, { type: "structural" | "evidence"; color: string }> = {
  willingness_to_pay: { type: "structural", color: "#3b82f6" },
  distribution_channel: { type: "structural", color: "#3b82f6" },
  data_feasibility: { type: "evidence", color: "#a855f7" },
  final_score: { type: "structural", color: "#3b82f6" },
};

function humanizeGate(gate: string): string {
  return gate
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function SwimLanes({ gates, lanes, onIdeaTrail }: SwimLanesProps) {
  return (
    <div
      className="flex gap-3 overflow-x-auto pb-4 snap-x snap-mandatory"
      style={{ scrollbarWidth: "thin" }}
    >
      {gates.map((gate) => {
        const meta = GATE_META[gate] || { type: "structural" as const, color: "#3b82f6" };
        const items = lanes[gate] || [];
        const headerStyle = {
          background: T.glassBg,
          border: `1px solid ${T.glassBorder}`,
          backdropFilter: "blur(16px)",
          borderRadius: "8px 8px 0 0",
        };

        return (
          <div
            key={gate}
            className="flex-shrink-0 w-[210px] snap-start"
            style={{
              borderLeft: "1px dashed rgba(255,255,255,0.12)",
            }}
          >
            {/* Glass header: gate name + type tag (structural=blue, evidence=purple) */}
            <div
              style={headerStyle}
              className="px-3 py-2 flex items-center justify-between text-xs"
            >
              <div className="min-w-0">
                <div className="text-[13px] font-medium text-white truncate">
                  {humanizeGate(gate)}
                </div>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                <span
                  className="px-1.5 py-px rounded text-[9px] font-mono uppercase tracking-wider"
                  style={{
                    background: `${meta.color}15`,
                    color: meta.color,
                    border: `1px solid ${meta.color}30`,
                  }}
                >
                  {meta.type}
                </span>
                <span className="font-mono text-[#666] text-[10px]">{items.length}</span>
              </div>
            </div>

            {/* Lane body - glass */}
            <div
              className="min-h-[380px] p-2 space-y-2 rounded-b-lg"
              style={{
                background: T.glassBg,
                border: `1px solid ${T.glassBorder}`,
                borderTop: "none",
                backdropFilter: "blur(16px)",
              }}
            >
              {items.length === 0 ? (
                <div className="h-32 flex items-center justify-center text-[11px] text-[#555] border border-dashed border-white/10 rounded">
                  no ideas
                </div>
              ) : (
                items.map((idea) => (
                  <IdeaCard
                    key={idea.id}
                    idea={idea}
                    onTrail={onIdeaTrail}
                  />
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
