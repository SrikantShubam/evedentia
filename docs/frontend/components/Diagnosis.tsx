"use client";

import { useMemo } from "react";
import { motion } from "motion/react";
import { T } from "@/lib/tokens";

interface DiagnosisProps {
  ideas: any[];
  zeroWinnerDiagnosis: string | null;
  totalSpend: number;
}

const STRUCTURAL_GATES = ["willingness_to_pay", "distribution_channel", "final_score"];
const EVIDENCE_GATES = ["data_feasibility"];

function getGateColor(gate: string): string {
  if (STRUCTURAL_GATES.includes(gate)) return "#3b82f6";
  if (EVIDENCE_GATES.includes(gate)) return "#a855f7";
  return "#64748b";
}

function humanizeGate(gate: string): string {
  return gate
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function Diagnosis({ ideas, zeroWinnerDiagnosis, totalSpend }: DiagnosisProps) {
  const { histogram, totalIdeas, killedCount, maxCount } = useMemo(() => {
    const counts: Record<string, number> = {};
    let killed = 0;

    for (const idea of ideas || []) {
      if (idea?.terminal_verdict === "KILL") {
        killed++;
      }
      const results: any[] = idea?.gate_results || [];
      for (const g of results) {
        if (g?.outcome === "FAIL") {
          const name = g.gate_name || "unknown";
          counts[name] = (counts[name] || 0) + 1;
          break;
        }
      }
    }

    const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    const mx = entries.length > 0 ? Math.max(...entries.map((e) => e[1])) : 1;

    return {
      histogram: entries,
      totalIdeas: (ideas || []).length,
      killedCount: killed,
      maxCount: mx,
    };
  }, [ideas]);

  // Guard: do not render if a pursue winner exists (parent should also gate this)
  const hasPursueWinner = (ideas || []).some((i: any) => i?.terminal_verdict === "PURSUE_SPIKE");
  if (hasPursueWinner || totalIdeas === 0) {
    return null;
  }

  return (
    <div
      className="mt-12 rounded-2xl border p-6"
      style={{
        background: T.glassBg,
        border: `1px solid ${T.glassBorder}`,
        backdropFilter: "blur(16px)",
      }}
    >
      {/* Section header */}
      <div
        className="font-mono text-xs tracking-[1px] mb-4"
        style={{ color: T.accent }}
      >
        ZERO-WINNER DIAGNOSIS
      </div>

      {/* Gate Histogram */}
      <div className="mb-6">
        <div className="text-[13px] font-medium text-white/90 mb-3">
          First-fail gate distribution
        </div>

        {histogram.length === 0 ? (
          <div className="text-xs text-[#888] py-2">No terminal gate failures recorded in payload.</div>
        ) : (
          <div className="space-y-2.5">
            {histogram.map(([gate, count], idx) => {
              const color = getGateColor(gate);
              const pct = maxCount > 0 ? (count / maxCount) * 100 : 0;
              return (
                <div key={gate} className="flex items-center gap-3 text-sm">
                  {/* Color dot */}
                  <span
                    className="inline-block w-2 h-2 rounded-full shrink-0"
                    style={{ background: color }}
                  />
                  {/* Gate name */}
                  <div
                    className="w-44 font-mono text-[12px] text-[#ccc] truncate"
                    title={gate}
                  >
                    {humanizeGate(gate)}
                  </div>
                  {/* Bar track + fill */}
                  <div className="flex-1 h-2.5 rounded bg-[#1f1f1f] overflow-hidden">
                    <motion.div
                      className="h-full rounded"
                      style={{ background: color }}
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 0.65, ease: "easeOut", delay: Math.min(idx * 0.035, 0.2) }}
                    />
                  </div>
                  {/* Count */}
                  <div className="w-7 text-right font-mono tabular-nums text-[#e2ff5d] text-[13px]">
                    {count}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* What-Would-Flip (amber warning card) */}
      {zeroWinnerDiagnosis && (
        <div
          className="mb-6 rounded-xl border p-4"
          style={{
            background: T.glassBg,
            border: `1px solid ${T.glassBorder}`,
            borderLeft: `3px solid ${T.warning}`,
          }}
        >
          <div className="font-mono text-[10px] tracking-[2.5px] uppercase text-[#f59e0b] mb-1.5">
            WHAT WOULD FLIP
          </div>
          <div className="text-[13px] leading-snug text-[#ddd]">
            {zeroWinnerDiagnosis}
          </div>
        </div>
      )}

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
        <div
          className="p-3.5 rounded-xl border"
          style={{ background: T.glassBg, borderColor: T.border }}
        >
          <div className="text-[#888] text-[10px] font-mono tracking-[1px]">TOTAL IDEAS</div>
          <div className="mt-1 text-2xl font-semibold tabular-nums">{totalIdeas}</div>
        </div>

        <div
          className="p-3.5 rounded-xl border"
          style={{ background: T.glassBg, borderColor: T.border }}
        >
          <div className="text-[#888] text-[10px] font-mono tracking-[1px]">TOTAL SPEND</div>
          <div className="mt-1 text-2xl font-semibold tabular-nums">${totalSpend.toFixed(2)}</div>
        </div>

        <div
          className="p-3.5 rounded-xl border"
          style={{ background: T.glassBg, borderColor: T.border }}
        >
          <div className="text-[#888] text-[10px] font-mono tracking-[1px]">KILLED</div>
          <div
            className="mt-1 text-2xl font-semibold tabular-nums"
            style={{ color: T.danger }}
          >
            {killedCount}
          </div>
        </div>
      </div>
    </div>
  );
}
