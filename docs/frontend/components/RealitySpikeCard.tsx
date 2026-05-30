"use client";

import { T } from "@/lib/tokens";

interface RealitySpikeCardProps {
  realitySpike: {
    idea_id: string;
    target_customer_profile: string;
    outreach_message: string;
    landing_page_headline: string;
    landing_page_subhead: string;
    interview_questions: string[];
    success_criteria: string;
    fail_criteria: string;
    weeks_to_run: number;
    provenance: string;
  };
}

export function RealitySpikeCard({ realitySpike }: RealitySpikeCardProps) {
  const rs = realitySpike;

  return (
    <div
      className="rounded-2xl border p-6 space-y-5"
      style={{
        borderColor: "rgba(245,158,11,0.25)",
        background: "rgba(245,158,11,0.04)",
        backdropFilter: "blur(16px)",
      }}
    >
      <div className="flex items-center justify-between">
        <div className="font-mono text-xs tracking-[1px] text-[#f59e0b] uppercase">
          REALITY SPIKE
        </div>
        <span
          className="px-2 py-0.5 rounded text-[10px] font-mono tracking-wider"
          style={{
            background: "rgba(245,158,11,0.1)",
            color: "#f59e0b",
            border: "1px solid rgba(245,158,11,0.2)",
            backdropFilter: "blur(8px)",
          }}
        >
          {rs.provenance}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          className="p-4 rounded-xl border col-span-2"
          style={{ borderColor: T.border, background: T.glassBg }}
        >
          <div className="text-[10px] font-mono tracking-wider text-[#888] uppercase mb-1">
            Target Customer Profile
          </div>
          <div className="text-sm leading-relaxed text-[#ddd]">{rs.target_customer_profile}</div>
        </div>

        <div
          className="p-4 rounded-xl border col-span-2"
          style={{
            borderColor: T.border,
            background: T.glassBg,
            borderLeft: "3px solid rgba(245,158,11,0.4)",
          }}
        >
          <div className="text-[10px] font-mono tracking-wider text-[#888] uppercase mb-1">
            Outreach Message
          </div>
          <div className="text-sm italic leading-relaxed text-[#ccc]">
            &ldquo;{rs.outreach_message}&rdquo;
          </div>
        </div>

        <div className="p-4 rounded-xl border" style={{ borderColor: T.border, background: T.glassBg }}>
          <div className="text-[10px] font-mono tracking-wider text-[#888] uppercase mb-1">
            Landing Page Headline
          </div>
          <div className="text-sm font-semibold text-white">{rs.landing_page_headline}</div>
        </div>

        <div className="p-4 rounded-xl border" style={{ borderColor: T.border, background: T.glassBg }}>
          <div className="text-[10px] font-mono tracking-wider text-[#888] uppercase mb-1">
            Subhead
          </div>
          <div className="text-sm text-[#ccc]">{rs.landing_page_subhead}</div>
        </div>

        <div
          className="p-4 rounded-xl border col-span-2"
          style={{ borderColor: T.border, background: T.glassBg }}
        >
          <div className="text-[10px] font-mono tracking-wider text-[#888] uppercase mb-2">
            Interview Questions
          </div>
          <ol className="space-y-1.5">
            {rs.interview_questions.map((q, i) => (
              <li key={i} className="text-sm text-[#ddd] flex gap-2">
                <span className="text-[#f59e0b] font-mono text-xs mt-0.5 shrink-0">{i + 1}.</span>
                <span>{q}</span>
              </li>
            ))}
          </ol>
        </div>

        <div className="p-4 rounded-xl border" style={{ borderColor: T.border, background: T.glassBg }}>
          <div className="text-[10px] font-mono tracking-wider text-[#888] uppercase mb-1">
            Success Criteria
          </div>
          <div className="text-sm text-[#22c55e]">{rs.success_criteria}</div>
        </div>

        <div className="p-4 rounded-xl border" style={{ borderColor: T.border, background: T.glassBg }}>
          <div className="text-[10px] font-mono tracking-wider text-[#888] uppercase mb-1">
            Fail Criteria
          </div>
          <div className="text-sm text-[#ef4444]">{rs.fail_criteria}</div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="font-mono text-[11px] text-[#888]">Duration</span>
        <span
          className="px-2 py-0.5 rounded text-xs font-mono"
          style={{
            background: T.glassBg,
            border: `1px solid ${T.glassBorder}`,
            color: T.accent,
          }}
        >
          {rs.weeks_to_run} weeks
        </span>
      </div>

      <div className="text-[10px] font-mono text-[#666] pt-2 border-t" style={{ borderColor: "rgba(245,158,11,0.15)" }}>
        idea_id: {rs.idea_id}
      </div>
    </div>
  );
}
