"use client";

import { useState } from "react";
import { motion } from "motion/react";
import Link from "next/link";
import { T } from "@/lib/tokens";

// --- Data (ported from original homepage) ------------------------------
const PIPELINE = [
  {
    step: "01",
    name: "scan",
    icon: "S",
    tagline: "Harvest real demand signals",
    input: "Domain keyword",
    output: "Raw candidates from Hacker News (HN) | Reddit | GitHub",
    detail:
      "Queries the Hacker News Algolia API, Reddit JSON search, and GitHub Issues REST endpoint. Each hit is normalised into a candidate dict with source_url, verbatim_quote, and cluster_id, then clustered for later hypothesis synthesis.",
  },
  {
    step: "02",
    name: "verify",
    icon: "V",
    tagline: "Confirm quotes are traceable",
    input: "Candidate + source_url",
    output: "verified: true | false | proof_level",
    detail:
      "Fetches the live page at source_url (50 KB cap) and checks that verbatim_quote appears verbatim. Falls back to in-memory text if the fetch fails. Verified signals can then feed synthesis and prosecution without losing traceability.",
  },
  {
    step: "03",
    name: "score",
    icon: "C",
    tagline: "Prosecute hypotheses before scoring",
    input: "Synthesized hypothesis",
    output: "status: keep | revise | kill | verdict: PURSUE | HOLD",
    detail:
      "Synthesizes cluster-level hypotheses, prosecutes each one against explicit keep/revise/kill checks, then applies hard gates (willingness_to_pay, distribution_channel, data_feasibility). Any single failure -> HOLD, score 0. PURSUE score = competition_gap x 0.4 + buildability x 0.3 + reachability x 0.3, then freshness-decayed over 365 days.",
  },
  {
    step: "04",
    name: "spec",
    icon: "P",
    tagline: "Generate a traceable product spec",
    input: "PURSUE opportunity",
    output: "ProductSpec JSON + PRD sections",
    detail:
      "Writes a ProductSpec with opportunity_id, title, sources (min 1), and approved: false. An LLM-assisted call appends target_user, core_problem, and wedge_feature as a prd sidecar. Human reviews and sets approved: true.",
  },
  {
    step: "05",
    name: "build",
    icon: "B",
    tagline: "Scaffold the wedge app",
    input: "Approved spec",
    output: "Next.js project skeleton",
    detail:
      "Validates spec.approved is strictly true (boolean identity check). Generates package.json and app/page.tsx. The approval gate is enforced at the CLI layer -- no spec without human sign-off reaches the build stage.",
  },
  {
    step: "06",
    name: "ship",
    icon: "Sh",
    tagline: "Produce deployment metadata",
    input: "Approved spec",
    output: "DeploymentMetadata | proof_level: dry-run | live",
    detail:
      "Validates spec then calls build_deployment_metadata. Without a deploy adapter the status is dry_run with explicit proof_level: dry-run so no one mistakes the artifact for live evidence. A real Vercel adapter upgrades proof_level to live.",
  },
  {
    step: "07",
    name: "track",
    icon: "T",
    tagline: "Measure real traction",
    input: "Metrics JSON file",
    output: "Normalised {visits, signups, revenue_proxy}",
    detail:
      "Reads a structured JSON payload, validates required numeric keys, normalises into a canonical envelope with status, proof_level, and missing_fields. Designed to be replaced with a live Vercel Analytics or PostHog fetch.",
  },
];

const PROOF_LEVELS = [
  {
    id: "fixture",
    label: "Fixture Proof",
    badge: "L1",
    color: "#3a7aff",
    description:
      "Data comes from hand-crafted JSON fixtures. Logic is verified but no real-world signal has been observed.",
    use: "Unit + integration tests",
  },
  {
    id: "dry-run",
    label: "Dry-Run Proof",
    badge: "L2",
    color: "#f59e0b",
    description:
      "Pipeline ran end-to-end on live-scanned data but no external system (Vercel, database) was written to.",
    use: "Acceptance + smoke tests",
  },
  {
    id: "live",
    label: "Live Proof",
    badge: "L3",
    color: T.accent,
    description:
      "A real deploy adapter ran. The deployment_id and URL exist in the wild. Traction metrics are from real users.",
    use: "Production release gate",
  },
];

const GATES = [
  {
    key: "willingness_to_pay",
    label: "Willingness to Pay",
    pass: "Explicit spend intent, pricing discussion, budget mention, or stated WTP in the signal.",
    fail: "General frustration, feature request, or curiosity without monetary signal.",
  },
  {
    key: "distribution_channel",
    label: "Distribution Channel",
    pass: "Clear reachable audience: named community, job title filter, platform, or mailing list.",
    fail: "Vague 'everyone needs this' or audience not identifiable without paid acquisition.",
  },
  {
    key: "data_feasibility",
    label: "Data Feasibility",
    pass: "Required data is public, accessible via API, or already in the operator's possession.",
    fail: "Depends on proprietary datasets, consent-gated personal data, or non-existent APIs.",
  },
];

const WEIGHTS = [
  { key: "competition_gap", label: "Competition Gap", weight: 0.4, color: T.accent },
  { key: "buildability", label: "Buildability", weight: 0.3, color: "#7dd3fc" },
  { key: "reachability_strength", label: "Reachability", weight: 0.3, color: "#c4b5fd" },
];

const CLI_COMMANDS = [
  {
    cmd: "evidentia scan",
    flags: "--fixture hn_sample.json --output scan.json",
    desc: "Fixture scan -- no network call",
  },
  {
    cmd: "evidentia scan",
    flags: "--live --domain invoicing --sources hn,reddit,github --output scan.json",
    desc: "Live multi-source scan",
  },
  {
    cmd: "evidentia spec",
    flags: "--input opp.json --output spec.json",
    desc: "Generate product spec from opportunity",
  },
  {
    cmd: "evidentia build",
    flags: "--spec spec_approved.json --output-dir ./build",
    desc: "Scaffold Next.js wedge app (requires approved: true)",
  },
  {
    cmd: "evidentia ship",
    flags: "--spec spec_approved.json --output deploy.json",
    desc: "Produce deployment metadata",
  },
  {
    cmd: "evidentia track",
    flags: "--input metrics.json",
    desc: "Normalise and validate traction metrics",
  },
];

// --- Hooks & Shared ----------------------------------------------------
function useFadeInView(threshold = 0.15) {
  const ref = { current: null } as any;
  // Simplified for about page - animations still work via motion
  return { ref, inView: true };
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <span
      style={{
        fontFamily: "var(--font-mono)",
        fontSize: "11px",
        letterSpacing: "0.12em",
        textTransform: "uppercase" as const,
        color: T.accent,
        display: "block",
        marginBottom: "12px",
      }}
    >
      {children}
    </span>
  );
}

function Divider() {
  return (
    <div
      style={{
        height: "1px",
        background: T.border,
        margin: "64px 0",
      }}
    />
  );
}

// --- Pipeline Card (expandable) ----------------------------------------
function PipelineCard({ stage, index }: { stage: (typeof PIPELINE)[0]; index: number }) {
  const [open, setOpen] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: index * 0.06 }}
      onClick={() => setOpen(!open)}
      style={{
        border: `1px solid ${open ? T.accent : T.border}`,
        borderRadius: "8px",
        padding: "18px 22px",
        cursor: "pointer",
        background: open ? T.accentDim : T.surface,
        transition: "all 0.2s ease",
        userSelect: "none" as const,
      }}
      whileHover={{ borderColor: T.mutedLight }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: "18px" }}>
        <div style={{ minWidth: "46px", flexShrink: 0 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted, letterSpacing: "0.06em", display: "block", marginBottom: "4px" }}>
            {stage.step}
          </span>
          <span style={{ fontSize: "20px", lineHeight: 1 }}>{stage.icon}</span>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: "12px", marginBottom: "4px", flexWrap: "wrap" as const }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "15px", fontWeight: 600, color: open ? T.accent : T.text, transition: "color 0.2s" }}>
              {stage.name}
            </span>
            <span style={{ fontSize: "13px", color: T.muted }}>{stage.tagline}</span>
          </div>
          <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" as const, fontSize: "12px", fontFamily: "var(--font-mono)" }}>
            <span><span style={{ color: T.muted }}>in -&gt; </span><span style={{ color: T.mutedLight }}>{stage.input}</span></span>
            <span><span style={{ color: T.muted }}>out -&gt; </span><span style={{ color: T.mutedLight }}>{stage.output}</span></span>
          </div>
        </div>
        <motion.span animate={{ rotate: open ? 90 : 0 }} transition={{ duration: 0.2 }} style={{ color: T.muted, fontSize: "14px", flexShrink: 0, marginTop: "2px" }}>
          {">"}
        </motion.span>
      </div>
      <motion.div
        initial={false}
        animate={{ height: open ? "auto" : 0, opacity: open ? 1 : 0 }}
        transition={{ duration: 0.25, ease: "easeInOut" }}
        style={{ overflow: "hidden" }}
      >
        <p style={{ marginTop: "14px", paddingTop: "14px", borderTop: `1px solid ${T.border}`, fontSize: "13px", color: T.mutedLight, lineHeight: 1.65, paddingLeft: "64px" }}>
          {stage.detail}
        </p>
      </motion.div>
    </motion.div>
  );
}

// --- Proof Level Card --------------------------------------------------
function ProofLevelCard({ level, inView, index }: { level: (typeof PROOF_LEVELS)[0]; inView: boolean; index: number }) {
  const [active, setActive] = useState(level.id === "dry-run");

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.4, delay: index * 0.1 }}
      onClick={() => setActive(!active)}
      style={{
        border: `1px solid ${active ? level.color : T.border}`,
        borderRadius: "10px",
        padding: "22px",
        cursor: "pointer",
        background: active ? `radial-gradient(ellipse at top left, ${level.color}10, ${T.surface})` : T.surface,
        boxShadow: active ? `0 0 20px ${level.color}18` : "none",
        transition: "all 0.25s ease",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "14px" }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", fontWeight: 700, padding: "3px 8px", borderRadius: "4px", background: `${level.color}18`, color: level.color, border: `1px solid ${level.color}40` }}>
          {level.badge}
        </span>
        {active && (
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: level.color, boxShadow: `0 0 10px ${level.color}`, display: "block" }} />
        )}
      </div>
      <h3 style={{ fontSize: "16px", fontWeight: 600, color: active ? level.color : T.text, marginBottom: "10px", transition: "color 0.2s" }}>
        {level.label}
      </h3>
      <p style={{ fontSize: "13px", color: T.muted, lineHeight: 1.6, marginBottom: "14px" }}>{level.description}</p>
      <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted, borderTop: `1px solid ${T.border}`, paddingTop: "10px", display: "block" }}>
        {level.use}
      </span>
    </motion.div>
  );
}

// --- CLI Command Card --------------------------------------------------
function CLICommandCard({ c, index, inView }: { c: (typeof CLI_COMMANDS)[0]; index: number; inView: boolean }) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    const text = `${c.cmd} ${c.flags}`;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.35, delay: index * 0.06 }}
      style={{ border: `1px solid ${T.border}`, borderRadius: "8px", background: T.surface, overflow: "hidden" }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "13px 18px", gap: "14px" }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "13px", lineHeight: 1.5, whiteSpace: "pre-wrap" as const, wordBreak: "break-all" as const }}>
            <span style={{ color: T.muted, userSelect: "none" as const }}>$ </span>
            <span style={{ color: T.accent }}>{c.cmd}</span>
            <span style={{ color: "#7dd3fc" }}> {c.flags}</span>
          </div>
          <p style={{ fontSize: "12px", color: T.muted, marginTop: "3px" }}>{c.desc}</p>
        </div>
        <button
          onClick={copy}
          style={{
            flexShrink: 0,
            fontFamily: "var(--font-mono)", fontSize: "11px", padding: "4px 10px", borderRadius: "5px",
            border: `1px solid ${T.border}`, background: "transparent", color: copied ? T.accent : T.muted, cursor: "pointer",
          }}
        >
          {copied ? "copied" : "copy"}
        </button>
      </div>
    </motion.div>
  );
}

// --- Try It Section (old scan -> generate flow, adapted) ---------------
const API_URL = process.env.NEXT_PUBLIC_EVIDENTIA_API ?? "http://127.0.0.1:8000";

const SOURCE_OPTIONS = [
  { id: "hn", label: "Hacker News (HN)" },
  { id: "reddit", label: "Reddit" },
  { id: "github", label: "GitHub" },
] as const;

function TryItSection() {
  const [domain, setDomain] = useState("");
  const [sources, setSources] = useState({ hn: true, reddit: true, github: true });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedIdeas, setGeneratedIdeas] = useState<any[]>([]);
  const [hasRun, setHasRun] = useState(false);

  const selectedSources = Object.entries(sources).filter(([, v]) => v).map(([k]) => k);
  const normalizedDomain = domain.trim();
  const projectName = normalizedDomain ? `Evidentia + ${normalizedDomain}` : "Evidentia + Domain";

  const runScan = async () => {
    if (!domain.trim()) return;
    setLoading(true);
    setError(null);
    setGeneratedIdeas([]);
    setHasRun(true);
    try {
      await fetch(`${API_URL}/harvest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ anchor_slug: domain.trim(), limit: 20 }),
      }).catch(() => null); // best effort

      const genRes = await fetch(`${API_URL}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ anchor_slug: domain.trim(), count: 6 }),
      });
      if (!genRes.ok) {
        const err = await genRes.json().catch(() => ({ detail: genRes.statusText }));
        throw new Error(err.detail || genRes.statusText);
      }
      const genData = await genRes.json();
      setGeneratedIdeas(genData.ideas || []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section style={{ padding: "0 24px" }}>
      <div style={{ marginBottom: "32px" }}>
        <SectionLabel>Live Pipeline (Old Flow)</SectionLabel>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.accent, marginBottom: "8px", letterSpacing: "0.06em" }}>
          {projectName}
        </div>
        <h2 style={{ fontSize: "clamp(22px, 3.6vw, 30px)", fontWeight: 700, letterSpacing: "-0.02em" }}>Try it now.</h2>
        <p style={{ color: T.muted, marginTop: "10px", fontSize: "14px", maxWidth: "520px" }}>
          Enter a domain or problem keyword. Harvests signals then generates ideas. Requires evidentia-server running locally.
        </p>
      </div>

      <div style={{ border: `1px solid ${T.border}`, borderRadius: "10px", background: T.surface, padding: "20px", marginBottom: "20px" }}>
        <div style={{ marginBottom: "16px" }}>
          <label style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted, letterSpacing: "0.08em", display: "block", marginBottom: "6px" }}>DOMAIN / KEYWORD</label>
          <div style={{ display: "flex", gap: "10px" }}>
            <input
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runScan()}
              placeholder="e.g. invoice reconciliation, dev tooling..."
              style={{ flex: 1, fontFamily: "var(--font-mono)", fontSize: "14px", padding: "9px 12px", borderRadius: "6px", border: `1px solid ${T.border}`, background: T.bg, color: T.text, outline: "none" }}
            />
            <button
              onClick={runScan}
              disabled={loading || !domain.trim()}
              style={{ fontFamily: "var(--font-mono)", fontSize: "13px", fontWeight: 600, padding: "9px 18px", borderRadius: "6px", border: `1px solid ${T.accent}`, background: loading ? T.border : T.accent, color: loading ? T.muted : "#000", cursor: loading || !domain.trim() ? "not-allowed" : "pointer" }}
            >
              {loading ? "harvesting..." : "harvest → generate"}
            </button>
          </div>
        </div>

        <div style={{ display: "flex", gap: "24px", alignItems: "flex-start", flexWrap: "wrap" as const }}>
          <div>
            <label style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted, letterSpacing: "0.08em", display: "block", marginBottom: "6px" }}>SOURCES (UI only)</label>
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" as const }}>
              {SOURCE_OPTIONS.map(({ id, label }) => (
                <button
                  key={id}
                  onClick={() => setSources((prev) => ({ ...prev, [id]: !prev[id] }))}
                  style={{ fontFamily: "var(--font-mono)", fontSize: "11px", padding: "4px 10px", borderRadius: "4px", border: `1px solid ${sources[id] ? T.accent : T.border}`, background: sources[id] ? T.accentDim : "transparent", color: sources[id] ? T.accent : T.muted, cursor: "pointer" }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div style={{ padding: "12px 14px", borderRadius: "8px", border: "1px solid rgba(248,113,113,0.3)", background: "rgba(248,113,113,0.06)", marginBottom: "16px" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.danger }}>error: {error}</span>
        </div>
      )}

      {loading && (
        <div style={{ padding: "14px 16px", borderRadius: "10px", background: T.glassBg, border: `1px solid ${T.glassBorder}`, backdropFilter: "blur(12px)", marginBottom: "14px", display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.muted }}>harvesting signals → generating ideas...</span>
        </div>
      )}

      {!loading && generatedIdeas.length > 0 && (
        <div style={{ marginBottom: "16px" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.accent, marginBottom: "10px", letterSpacing: "0.06em" }}>GENERATED IDEAS ({generatedIdeas.length})</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "12px" }}>
            {generatedIdeas.map((idea, idx) => (
              <div key={idea.id || idx} style={{ background: T.glassBg, border: `1px solid ${T.glassBorder}`, borderRadius: "10px", backdropFilter: "blur(14px)", padding: "14px" }}>
                <div style={{ fontSize: "14px", fontWeight: 600, marginBottom: "4px", color: T.text }}>{idea.label}</div>
                {idea.cohort && <div style={{ fontSize: "11px", color: T.muted, marginBottom: "8px", fontFamily: "var(--font-mono)" }}>{idea.cohort}</div>}
                {idea.pain_hypothesis && <div style={{ fontSize: "12px", color: T.mutedLight, lineHeight: 1.4, marginBottom: "10px" }}>{idea.pain_hypothesis}</div>}
                {idea.kill_condition && <div style={{ fontSize: "10px", color: T.danger, marginBottom: "10px" }}>KILL IF: {idea.kill_condition.description || JSON.stringify(idea.kill_condition)}</div>}
                <button
                  onClick={() => {
                    try {
                      const payload = encodeURIComponent(JSON.stringify(idea));
                      window.location.href = `/tournament/new?prefill=${payload}`;
                    } catch { window.location.href = "/tournament/new"; }
                  }}
                  style={{ width: "100%", padding: "8px 10px", background: T.glassAccentBg, color: T.accent, fontWeight: 600, fontSize: "12px", fontFamily: "var(--font-mono)", border: `1px solid ${T.glassAccentBorder}`, borderRadius: "5px", cursor: "pointer" }}
                >
                  Run Tournament →
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {hasRun && !loading && generatedIdeas.length === 0 && !error && (
        <div style={{ padding: "16px 18px", borderRadius: "10px", background: T.glassBg, border: `1px solid ${T.glassBorder}`, backdropFilter: "blur(12px)", textAlign: "center" as const, marginBottom: "12px" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.muted }}>enter a keyword above and hit harvest to generate ideas from real signals</span>
        </div>
      )}
    </section>
  );
}

// --- Main About Page ---------------------------------------------------
export default function AboutPage() {
  const [inView] = useState(true);

  return (
    <main style={{ background: T.bg, minHeight: "100vh", color: T.text }}>
      {/* Top nav */}
      <div style={{ position: "sticky", top: 0, zIndex: 50, background: "rgba(10,10,10,0.9)", backdropFilter: "blur(10px)", borderBottom: `1px solid ${T.border}`, padding: "12px 24px", display: "flex", alignItems: "center", gap: "16px" }}>
        <Link href="/" style={{ color: T.accent, fontFamily: "var(--font-mono)", fontSize: "13px", textDecoration: "none" }}>← Back to Dashboard</Link>
        <div style={{ flex: 1 }} />
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.muted }}>About Evidentia</span>
      </div>

      <div style={{ maxWidth: "980px", margin: "0 auto", padding: "40px 24px 80px" }}>
        <div style={{ marginBottom: "48px" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.accent, letterSpacing: "0.1em", marginBottom: "8px" }}>EVIDENTIA</div>
          <h1 style={{ fontSize: "clamp(28px, 5vw, 42px)", fontWeight: 700, letterSpacing: "-0.025em", marginBottom: "12px" }}>About Evidentia</h1>
          <p style={{ fontSize: "15px", color: T.muted, maxWidth: "560px" }}>
            Evidence-first product pipeline. Every claim traces to a URL and a verbatim quote. Hard gates before heuristics.
          </p>
        </div>

        {/* Pipeline Stages */}
        <section style={{ marginBottom: "64px" }}>
          <SectionLabel>Pipeline Stages</SectionLabel>
          <h2 style={{ fontSize: "clamp(22px, 3.8vw, 30px)", fontWeight: 700, letterSpacing: "-0.02em", marginBottom: "20px" }}>Seven stages. Zero invented claims.</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
            {PIPELINE.map((stage, i) => (
              <PipelineCard key={stage.name} stage={stage} index={i} />
            ))}
          </div>
        </section>

        <Divider />

        {/* Proof Levels */}
        <section style={{ marginBottom: "64px" }}>
          <SectionLabel>Proof Levels</SectionLabel>
          <h2 style={{ fontSize: "clamp(22px, 3.8vw, 30px)", fontWeight: 700, letterSpacing: "-0.02em", marginBottom: "12px" }}>Three tiers of evidence.</h2>
          <p style={{ color: T.muted, marginBottom: "20px", fontSize: "14px", maxWidth: "520px" }}>
            Fixture proof stays in tests. Dry-run proof stays in CI. Live proof is the only kind that counts in production.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "10px" }}>
            {PROOF_LEVELS.map((level, i) => (
              <ProofLevelCard key={level.id} level={level} inView={inView} index={i} />
            ))}
          </div>
        </section>

        <Divider />

        {/* Scoring Model */}
        <section style={{ marginBottom: "64px" }}>
          <SectionLabel>Scoring Model</SectionLabel>
          <h2 style={{ fontSize: "clamp(22px, 3.8vw, 30px)", fontWeight: 700, letterSpacing: "-0.02em", marginBottom: "12px" }}>Hard gates before heuristics.</h2>
          <p style={{ color: T.muted, marginBottom: "18px", fontSize: "14px", maxWidth: "520px" }}>
            All three gates must pass. A single failure forces <code style={{ fontFamily: "var(--font-mono)", background: T.surface, padding: "1px 5px", borderRadius: "3px" }}>HOLD, score 0</code>. No heuristic can rescue a gate failure.
          </p>

          {/* Gates table */}
          <div style={{ display: "flex", flexDirection: "column", gap: "2px", marginBottom: "40px" }}>
            {GATES.map((gate, i) => (
              <div key={gate.key} style={{ border: `1px solid ${T.border}`, borderRadius: "8px", overflow: "hidden" }}>
                <div style={{ display: "grid", gridTemplateColumns: "200px 1fr 1fr", gap: "0", minWidth: "680px" }}>
                  <div style={{ padding: "16px 18px", borderRight: `1px solid ${T.border}`, background: T.surface }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.accent, display: "block", marginBottom: "3px", letterSpacing: "0.04em" }}>GATE {String(i + 1).padStart(2, "0")}</span>
                    <span style={{ fontSize: "13px", fontWeight: 600, color: T.text }}>{gate.label}</span>
                  </div>
                  <div style={{ padding: "16px 18px", borderRight: `1px solid ${T.border}` }}>
                    <span style={{ fontSize: "10px", fontFamily: "var(--font-mono)", color: "#4ade80", display: "block", marginBottom: "5px", letterSpacing: "0.08em" }}>PASS</span>
                    <p style={{ fontSize: "12px", color: T.muted, lineHeight: 1.5 }}>{gate.pass}</p>
                  </div>
                  <div style={{ padding: "16px 18px" }}>
                    <span style={{ fontSize: "10px", fontFamily: "var(--font-mono)", color: "#f87171", display: "block", marginBottom: "5px", letterSpacing: "0.08em" }}>FAIL</span>
                    <p style={{ fontSize: "12px", color: T.muted, lineHeight: 1.5 }}>{gate.fail}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Weights */}
          <SectionLabel>Heuristic Weights</SectionLabel>
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {WEIGHTS.map((w, i) => (
              <div key={w.key}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px", alignItems: "baseline" }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: T.text }}>{w.key}</span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: w.color, fontWeight: 700 }}>{(w.weight * 100).toFixed(0)}%</span>
                </div>
                <div style={{ height: "4px", borderRadius: "2px", background: T.border, overflow: "hidden" }}>
                  <motion.div initial={{ width: 0 }} animate={{ width: `${w.weight * 100}%` }} transition={{ duration: 0.7, delay: 0.1 + i * 0.1 }} style={{ height: "100%", background: w.color }} />
                </div>
              </div>
            ))}
          </div>
          <p style={{ marginTop: "16px", fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted }}>
            score = competition_gap × 0.4 + buildability × 0.3 + reachability_strength × 0.3 → decayed over 365 days
          </p>
        </section>

        <Divider />

        {/* CLI Reference */}
        <section style={{ marginBottom: "64px" }}>
          <SectionLabel>CLI Reference</SectionLabel>
          <h2 style={{ fontSize: "clamp(22px, 3.8vw, 30px)", fontWeight: 700, letterSpacing: "-0.02em", marginBottom: "18px" }}>One command per stage.</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            {CLI_COMMANDS.map((c, i) => (
              <CLICommandCard key={i} c={c} index={i} inView={inView} />
            ))}
          </div>
        </section>

        <Divider />

        {/* Old Try It */}
        <section>
          <TryItSection />
        </section>
      </div>

      <footer style={{ borderTop: `1px solid ${T.border}`, padding: "28px 24px", textAlign: "center" as const }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted }}>Evidentia — evidence over opinion</span>
      </footer>
    </main>
  );
}
