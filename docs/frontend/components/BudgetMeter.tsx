"use client";

import { motion } from "motion/react";
import { T } from "@/lib/tokens";

interface BudgetMeterProps {
  llmUsed: number;
  llmMax: number;
  searchUsed: number;
  searchMax: number;
  spend: number;
  spendMax: number;
}

export function BudgetMeter({
  llmUsed,
  llmMax,
  searchUsed,
  searchMax,
  spend,
  spendMax,
}: BudgetMeterProps) {
  const llmPct = Math.min((llmUsed / llmMax) * 100, 100);
  const searchPct = Math.min((searchUsed / searchMax) * 100, 100);
  const spendPct = Math.min((spend / spendMax) * 100, 100);

  const isSpendWarning = spendPct > 70;

  return (
    <div className="rounded-xl border p-4" style={{ background: T.surface, borderColor: T.border }}>
      <div className="flex items-center justify-between mb-3">
        <div className="text-[11px] font-mono uppercase tracking-[1px] text-[#888]">
          Budget Meter
        </div>
        <div className="text-[11px] font-mono text-[#666]">
          LIVE
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* LLM Calls */}
        <div>
          <div className="flex justify-between text-xs mb-1.5 font-mono">
            <span className="text-[#888]">LLM CALLS</span>
            <span className="text-white tabular-nums">
              {llmUsed} <span className="text-[#555]">/ {llmMax}</span>
            </span>
          </div>
          <div className="h-1.5 bg-[#1f1f1f] rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ background: T.accent }}
              initial={{ width: 0 }}
              animate={{ width: `${llmPct}%` }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            />
          </div>
        </div>

        {/* Search */}
        <div>
          <div className="flex justify-between text-xs mb-1.5 font-mono">
            <span className="text-[#888]">SEARCH</span>
            <span className="text-white tabular-nums">
              {searchUsed} <span className="text-[#555]">/ {searchMax}</span>
            </span>
          </div>
          <div className="h-1.5 bg-[#1f1f1f] rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ background: "#7dd3fc" }}
              initial={{ width: 0 }}
              animate={{ width: `${searchPct}%` }}
              transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
            />
          </div>
        </div>

        {/* Spend */}
        <div>
          <div className="flex justify-between text-xs mb-1.5 font-mono">
            <span className="text-[#888]">SPEND</span>
            <span
              className="tabular-nums"
              style={{ color: isSpendWarning ? T.warning : T.text }}
            >
              ${spend.toFixed(2)} <span className="text-[#555]">/ ${spendMax}</span>
            </span>
          </div>
          <div className="h-1.5 bg-[#1f1f1f] rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ background: isSpendWarning ? T.warning : T.accent }}
              initial={{ width: 0 }}
              animate={{ width: `${spendPct}%` }}
              transition={{ duration: 0.6, ease: "easeOut", delay: 0.2 }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
