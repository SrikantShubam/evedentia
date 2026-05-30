"use client";

import { motion } from "motion/react";
import { T } from "@/lib/tokens";

interface Idea {
  id: string;
  label: string;
  confidence?: number;
  kill_risk?: number;
  quote?: string;
  source_url?: string;
  cost_usd?: number;
  status?: "PENDING" | "PASS" | "FAIL" | "HOLD" | "SKIPPED";
  evidence_count?: number;
  current_gate?: string;
}

interface IdeaCardProps {
  idea: Idea;
  variant?: "board" | "memo" | "trail" | "compact";
  onPass?: () => void;
  onFail?: () => void;
  showActions?: boolean;
  className?: string;
  onTrail?: (id: string) => void;
}

export function IdeaCard({
  idea,
  variant = "board",
  onPass,
  onFail,
  showActions = false,
  className = "",
  onTrail,
}: IdeaCardProps & { onTrail?: (id: string) => void }) {
  const confidence = Math.max(0, Math.min(1, idea.confidence ?? 0.65));
  const killRisk = idea.kill_risk ?? 0.22;
  const cost = idea.cost_usd ?? 0.0;
  const quote = idea.quote || "No direct quote captured yet.";

  const status = (idea.status || "PENDING") as "PENDING" | "PASS" | "FAIL" | "SKIPPED" | "HOLD";

  const leftBorder =
    status === "PASS" ? T.success :
    status === "FAIL" ? T.danger :
    status === "SKIPPED" ? T.warning : T.muted;

  const glassStyle = {
    background: T.glassBg,
    border: `1px solid ${T.glassBorder}`,
    backdropFilter: "blur(16px)",
    borderRadius: "8px",
    borderLeft: `3px solid ${leftBorder}`,

  };

  // Status-driven animation / opacity (inline style objects per task)
  const getStatusStyle = () => {
    if (status === "PASS") {
      return { opacity: 1 };
    }
    if (status === "FAIL") {
      return { opacity: 0.4 };
    }
    if (status === "SKIPPED") {
      return { opacity: 0.9 };
    }
    return { opacity: 0.3 };
  };

  const statusStyle = getStatusStyle();
  const isSkipped = status === "SKIPPED";
  const isPass = status === "PASS";
  const shimmerClass = isSkipped ? "shimmer" : "";

  return (
    <motion.div
      className={`p-3 text-sm transition-all ${shimmerClass} ${className}`}
      style={{ ...glassStyle, ...statusStyle }}
      animate={{
        x: isPass ? 3 : 0,
        opacity: statusStyle.opacity,
      }}
      transition={{ type: "spring", stiffness: 120, damping: 20 }}
      whileHover={{ scale: 1.01 }}
    >
      {/* Label */}
      <div className="font-semibold text-[13px] leading-tight text-white pr-1 mb-1.5 line-clamp-2">
        {idea.label}
      </div>

      {/* Confidence bar */}
      <div className="flex items-center gap-2 mb-1.5">
        <div className="flex-1 h-1 bg-[#1f1f1f] rounded overflow-hidden">
          <div
            className="h-1 rounded transition-all"
            style={{ width: `${Math.round(confidence * 100)}%`, background: T.accent }}
          />
        </div>
          <span className="font-mono text-[10px] tabular-nums" style={{ color: T.accent }}>{Math.round(confidence * 100)}%</span>
      </div>

      {/* Top kill risk */}
      <div className="text-[10px] text-[#888] mb-1">
        kill risk <span className="font-semibold tabular-nums" style={{ color: killRisk > 0.3 ? T.danger : T.mutedLight }}>{(killRisk * 100).toFixed(0)}%</span>
      </div>

      {/* Strongest quote (italic, max 2 lines) */}
      <div className="text-[11px] italic text-[#888] line-clamp-2 mb-1.5 border-l border-white/10 pl-2">
        “{quote}”
      </div>

      {/* Running cost */}
      <div className="flex items-center justify-between text-[10px] font-mono text-[#666]">
        <span>cost</span>
        <span className="tabular-nums text-white">${cost.toFixed(3)}</span>
      </div>

      {/* Trail link */}
      <div className="mt-2 pt-2 border-t border-white/10">
        <a
          href={`/ideas/${idea.id}`}
          className="text-[10px] hover:underline font-mono tracking-wider" style={{ color: T.accent }}
          onClick={(e) => {
            if (onTrail) {
              e.preventDefault();
              onTrail(idea.id);
            }
          }}
        >
          evidence trail →
        </a>
      </div>

      {/* Optional actions kept for compatibility */}
      {showActions && (onPass || onFail) && (
        <div className="mt-3 flex gap-1.5 text-[10px]">
          {onPass && (
            <button onClick={onPass} className="flex-1 py-0.5 rounded" style={{ background: T.success, color: "#000" }}>PASS</button>
          )}
          {onFail && (
            <button onClick={onFail} className="flex-1 py-0.5 rounded border" style={{ borderColor: T.danger, color: T.danger }}>FAIL</button>
          )}
        </div>
      )}
    </motion.div>
  );
}
