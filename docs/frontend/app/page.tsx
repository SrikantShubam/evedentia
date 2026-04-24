"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useInView, useScroll, useTransform } from "motion/react";

// --- Tokens ------------------------------------------------------------
const T = {
  bg: "#0a0a0a",
  surface: "#111111",
  surfaceHover: "#161616",
  border: "#1f1f1f",
  accent: "#e2ff5d",
  accentDim: "rgba(226,255,93,0.08)",
  text: "#f0f0f0",
  muted: "#666666",
  mutedLight: "#888888",
};

// --- Data --------------------------------------------------------------
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

// --- Hooks -------------------------------------------------------------
function useFadeInView(threshold = 0.15) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "0px 0px -80px 0px" });
  return { ref, inView };
}

// --- Shared components -------------------------------------------------
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
        margin: "80px 0",
      }}
    />
  );
}

// --- Nav ---------------------------------------------------------------
function Nav() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handler);
    return () => window.removeEventListener("scroll", handler);
  }, []);

  return (
    <motion.nav
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        borderBottom: `1px solid ${scrolled ? T.border : "transparent"}`,
        background: scrolled ? "rgba(10,10,10,0.92)" : "transparent",
        backdropFilter: scrolled ? "blur(12px)" : "none",
        transition: "all 0.3s ease",
        padding: "0 max(24px, calc((100vw - 960px) / 2))",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: "56px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontWeight: 600,
            fontSize: "15px",
            color: T.text,
            letterSpacing: "-0.02em",
          }}
        >
          evidentia
        </span>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            padding: "2px 8px",
            borderRadius: "4px",
            border: `1px solid ${T.border}`,
            color: T.muted,
            letterSpacing: "0.06em",
          }}
        >
          v0.1.0
        </span>
      </div>
      <div style={{ display: "flex", gap: "24px", alignItems: "center" }}>
        {["pipeline", "scoring", "try", "cli"].map((s) => (
          <a
            key={s}
            href={`#${s}`}
            style={{
              fontFamily: "var(--font-sans)",
              fontSize: "13px",
              color: T.muted,
              textDecoration: "none",
              transition: "color 0.2s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = T.text)}
            onMouseLeave={(e) => (e.currentTarget.style.color = T.muted)}
          >
            {s}
          </a>
        ))}
      </div>
    </motion.nav>
  );
}

// --- Hero --------------------------------------------------------------
function Hero() {
  const words = ["Replace", "opinions", "with", "evidence."];
  const stages = ["scan", "verify", "score", "spec", "build", "ship", "track"];

  return (
    <section
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: "120px max(24px, calc((100vw - 960px) / 2)) 80px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background grid */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `
            linear-gradient(${T.border} 1px, transparent 1px),
            linear-gradient(90deg, ${T.border} 1px, transparent 1px)
          `,
          backgroundSize: "40px 40px",
          opacity: 0.4,
          maskImage: "radial-gradient(ellipse 80% 60% at 50% 40%, black 30%, transparent 100%)",
        }}
      />

      {/* Accent glow */}
      <div
        style={{
          position: "absolute",
          top: "30%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: "600px",
          height: "300px",
          background: `radial-gradient(ellipse, rgba(226,255,93,0.06) 0%, transparent 70%)`,
          pointerEvents: "none",
        }}
      />

      <div style={{ position: "relative", zIndex: 1 }}>
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            padding: "4px 12px",
            borderRadius: "20px",
            border: `1px solid ${T.border}`,
            background: T.surface,
            marginBottom: "32px",
          }}
        >
          <span
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              background: T.accent,
              boxShadow: `0 0 8px ${T.accent}`,
            }}
          />
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "11px",
              color: T.mutedLight,
              letterSpacing: "0.08em",
            }}
          >
            evidence-first | anti-hallucination
          </span>
        </motion.div>

        {/* Headline */}
        <h1
          style={{
            fontSize: "clamp(40px, 7vw, 72px)",
            fontWeight: 700,
            lineHeight: 1.08,
            letterSpacing: "-0.03em",
            marginBottom: "28px",
            display: "flex",
            flexWrap: "wrap" as const,
            gap: "0.25em",
          }}
        >
          {words.map((word, i) => (
            <motion.span
              key={word}
              initial={{ opacity: 0, y: 20, filter: "blur(4px)" }}
              animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              transition={{ duration: 0.5, delay: 0.3 + i * 0.1, ease: "easeOut" }}
              style={{
                color: i === words.length - 1 ? T.accent : T.text,
              }}
            >
              {word}
            </motion.span>
          ))}
        </h1>

        {/* Subline */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          style={{
            fontSize: "17px",
            color: T.muted,
            maxWidth: "520px",
            lineHeight: 1.7,
            marginBottom: "56px",
          }}
        >
          Evidentia turns raw demand signals from HN, Reddit, and GitHub into
          cluster-synthesized hypotheses, prosecutes them with explicit keep / revise / kill
          status, then scores only the survivors. Every claim anchors to a URL and a verbatim
          quote.
        </motion.p>

        {/* Pipeline steps */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 1.0 }}
          style={{
            display: "flex",
            flexWrap: "wrap" as const,
            gap: "4px",
            alignItems: "center",
          }}
        >
          {stages.map((stage, i) => (
            <motion.div
              key={stage}
              initial={{ opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: 1.1 + i * 0.07, ease: "easeOut" }}
              style={{ display: "flex", alignItems: "center", gap: "4px" }}
            >
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "13px",
                  padding: "5px 12px",
                  borderRadius: "6px",
                  border: `1px solid ${T.border}`,
                  background: T.surface,
                  color: T.text,
                  transition: "all 0.2s",
                  cursor: "default",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = T.accent;
                  e.currentTarget.style.color = T.accent;
                  e.currentTarget.style.background = T.accentDim;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = T.border;
                  e.currentTarget.style.color = T.text;
                  e.currentTarget.style.background = T.surface;
                }}
              >
                {stage}
              </span>
              {i < stages.length - 1 && (
                <span style={{ color: T.border, fontSize: "12px", margin: "0 2px" }}>-&gt;</span>
              )}
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

// --- Pipeline Section --------------------------------------------------
function PipelineSection() {
  const { ref, inView } = useFadeInView();

  return (
    <section id="pipeline" ref={ref} style={{ padding: "0 max(24px, calc((100vw - 960px) / 2))" }}>
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={inView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.5 }}
        style={{ marginBottom: "48px" }}
      >
        <SectionLabel>Pipeline Stages</SectionLabel>
        <h2
          style={{
            fontSize: "clamp(24px, 4vw, 36px)",
            fontWeight: 700,
            letterSpacing: "-0.025em",
            color: T.text,
          }}
        >
          Seven stages. Zero invented claims.
        </h2>
      </motion.div>

      <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
        {PIPELINE.map((stage, i) => (
          <PipelineCard key={stage.name} stage={stage} index={i} parentInView={inView} />
        ))}
      </div>
    </section>
  );
}

function PipelineCard({
  stage,
  index,
  parentInView,
}: {
  stage: (typeof PIPELINE)[0];
  index: number;
  parentInView: boolean;
}) {
  const [open, setOpen] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, x: -16 }}
      animate={parentInView ? { opacity: 1, x: 0 } : {}}
      transition={{ duration: 0.4, delay: index * 0.07, ease: "easeOut" }}
      onClick={() => setOpen(!open)}
      style={{
        border: `1px solid ${open ? T.accent : T.border}`,
        borderRadius: "8px",
        padding: "20px 24px",
        cursor: "pointer",
        background: open ? T.accentDim : T.surface,
        transition: "all 0.2s ease",
        userSelect: "none" as const,
      }}
      whileHover={{ borderColor: T.mutedLight }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: "20px" }}>
        {/* Step + icon */}
        <div style={{ minWidth: "48px", flexShrink: 0 }}>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "11px",
              color: T.muted,
              letterSpacing: "0.06em",
              display: "block",
              marginBottom: "4px",
            }}
          >
            {stage.step}
          </span>
          <span style={{ fontSize: "22px", lineHeight: 1 }}>{stage.icon}</span>
        </div>

        {/* Main info */}
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: "12px", marginBottom: "4px" }}>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "15px",
                fontWeight: 600,
                color: open ? T.accent : T.text,
                transition: "color 0.2s",
              }}
            >
              {stage.name}
            </span>
            <span style={{ fontSize: "13px", color: T.muted }}>{stage.tagline}</span>
          </div>
          <div
            style={{
              display: "flex",
              gap: "24px",
              flexWrap: "wrap" as const,
              fontSize: "12px",
              fontFamily: "var(--font-mono)",
            }}
          >
            <span>
              <span style={{ color: T.muted }}>in -&gt; </span>
              <span style={{ color: T.mutedLight }}>{stage.input}</span>
            </span>
            <span>
              <span style={{ color: T.muted }}>out -&gt; </span>
              <span style={{ color: T.mutedLight }}>{stage.output}</span>
            </span>
          </div>
        </div>

        {/* Chevron */}
        <motion.span
          animate={{ rotate: open ? 90 : 0 }}
          transition={{ duration: 0.2 }}
          style={{ color: T.muted, fontSize: "14px", flexShrink: 0, marginTop: "2px" }}
        >
          {">"}
        </motion.span>
      </div>

      {/* Expanded detail */}
      <motion.div
        initial={false}
        animate={{ height: open ? "auto" : 0, opacity: open ? 1 : 0 }}
        transition={{ duration: 0.25, ease: "easeInOut" }}
        style={{ overflow: "hidden" }}
      >
        <p
          style={{
            marginTop: "16px",
            paddingTop: "16px",
            borderTop: `1px solid ${T.border}`,
            fontSize: "13px",
            color: T.mutedLight,
            lineHeight: 1.7,
            paddingLeft: "68px",
          }}
        >
          {stage.detail}
        </p>
      </motion.div>
    </motion.div>
  );
}

// --- Proof Levels ------------------------------------------------------
function ProofLevelsSection() {
  const { ref, inView } = useFadeInView();
  const [active, setActive] = useState("dry-run");

  return (
    <section ref={ref} style={{ padding: "0 max(24px, calc((100vw - 960px) / 2))" }}>
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={inView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.5 }}
        style={{ marginBottom: "40px" }}
      >
        <SectionLabel>Proof Levels</SectionLabel>
        <h2
          style={{
            fontSize: "clamp(24px, 4vw, 36px)",
            fontWeight: 700,
            letterSpacing: "-0.025em",
          }}
        >
          Three tiers of evidence.
        </h2>
        <p style={{ color: T.muted, marginTop: "12px", fontSize: "14px", maxWidth: "480px" }}>
          Fixture proof stays in tests. Dry-run proof stays in CI. Live proof is the only kind
          that counts in production.
        </p>
      </motion.div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "12px" }}>
        {PROOF_LEVELS.map((level, i) => {
          const isActive = active === level.id;
          return (
            <motion.div
              key={level.id}
              initial={{ opacity: 0, y: 20 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.4, delay: i * 0.1 }}
              onClick={() => setActive(level.id)}
              style={{
                border: `1px solid ${isActive ? level.color : T.border}`,
                borderRadius: "10px",
                padding: "24px",
                cursor: "pointer",
                background: isActive
                  ? `radial-gradient(ellipse at top left, ${level.color}10, ${T.surface})`
                  : T.surface,
                boxShadow: isActive ? `0 0 24px ${level.color}20` : "none",
                transition: "all 0.25s ease",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "11px",
                    fontWeight: 700,
                    padding: "3px 8px",
                    borderRadius: "4px",
                    background: `${level.color}18`,
                    color: level.color,
                    border: `1px solid ${level.color}40`,
                  }}
                >
                  {level.badge}
                </span>
                {isActive && (
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    style={{
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
                      background: level.color,
                      boxShadow: `0 0 10px ${level.color}`,
                      display: "block",
                    }}
                  />
                )}
              </div>
              <h3 style={{ fontSize: "16px", fontWeight: 600, color: isActive ? level.color : T.text, marginBottom: "10px", transition: "color 0.2s" }}>
                {level.label}
              </h3>
              <p style={{ fontSize: "13px", color: T.muted, lineHeight: 1.6, marginBottom: "16px" }}>
                {level.description}
              </p>
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  color: T.muted,
                  borderTop: `1px solid ${T.border}`,
                  paddingTop: "12px",
                  display: "block",
                }}
              >
                {level.use}
              </span>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}

// --- Scoring Section ---------------------------------------------------
function ScoringSection() {
  const { ref, inView } = useFadeInView();

  return (
    <section id="scoring" ref={ref} style={{ padding: "0 max(24px, calc((100vw - 960px) / 2))" }}>
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={inView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.5 }}
        style={{ marginBottom: "48px" }}
      >
        <SectionLabel>Scoring Model</SectionLabel>
        <h2
          style={{
            fontSize: "clamp(24px, 4vw, 36px)",
            fontWeight: 700,
            letterSpacing: "-0.025em",
          }}
        >
          Hard gates before heuristics.
        </h2>
        <p style={{ color: T.muted, marginTop: "12px", fontSize: "14px", maxWidth: "520px" }}>
          All three gates must pass. A single failure forces{" "}
          <code style={{ fontFamily: "var(--font-mono)", color: T.text, background: T.surface, padding: "1px 6px", borderRadius: "4px" }}>
            HOLD, score 0
          </code>
          . No heuristic can rescue a gate failure.
        </p>
      </motion.div>

      {/* Hard gates */}
      <div style={{ display: "flex", flexDirection: "column", gap: "2px", marginBottom: "48px" }}>
        {GATES.map((gate, i) => (
          <motion.div
            key={gate.key}
            initial={{ opacity: 0, x: -12 }}
            animate={inView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.4, delay: i * 0.1 }}
            style={{
              border: `1px solid ${T.border}`,
              borderRadius: "8px",
              overflow: "hidden", overflowX: "auto",
            }}
          >
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "200px 1fr 1fr", minWidth: "720px",
                gap: "0",
              }}
            >
              <div
                style={{
                  padding: "18px 20px",
                  borderRight: `1px solid ${T.border}`,
                  background: T.surface,
                }}
              >
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.accent, display: "block", marginBottom: "4px", letterSpacing: "0.04em" }}>
                  GATE {String(i + 1).padStart(2, "0")}
                </span>
                <span style={{ fontSize: "13px", fontWeight: 600, color: T.text, lineHeight: 1.3 }}>
                  {gate.label}
                </span>
              </div>
              <div style={{ padding: "18px 20px", borderRight: `1px solid ${T.border}` }}>
                <span style={{ fontSize: "10px", fontFamily: "var(--font-mono)", color: "#4ade80", display: "block", marginBottom: "6px", letterSpacing: "0.08em" }}>
                  PASS
                </span>
                <p style={{ fontSize: "12px", color: T.muted, lineHeight: 1.5 }}>{gate.pass}</p>
              </div>
              <div style={{ padding: "18px 20px" }}>
                <span style={{ fontSize: "10px", fontFamily: "var(--font-mono)", color: "#f87171", display: "block", marginBottom: "6px", letterSpacing: "0.08em" }}>
                  FAIL
                </span>
                <p style={{ fontSize: "12px", color: T.muted, lineHeight: 1.5 }}>{gate.fail}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Heuristic weights */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={inView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.5, delay: 0.4 }}
      >
        <SectionLabel>Heuristic Weights</SectionLabel>
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {WEIGHTS.map((w, i) => (
            <div key={w.key}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", alignItems: "baseline" }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: T.text }}>
                  {w.key}
                </span>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: w.color, fontWeight: 700 }}>
                  {(w.weight * 100).toFixed(0)}%
                </span>
              </div>
              <div style={{ height: "4px", borderRadius: "2px", background: T.border, overflow: "hidden" }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={inView ? { width: `${w.weight * 100}%` } : {}}
                  transition={{ duration: 0.8, delay: 0.6 + i * 0.15, ease: "easeOut" }}
                  style={{ height: "100%", borderRadius: "2px", background: w.color }}
                />
              </div>
            </div>
          ))}
        </div>
        <p style={{ marginTop: "20px", fontFamily: "var(--font-mono)", fontSize: "12px", color: T.muted }}>
          score = competition_gap x 0.4 + buildability x 0.3 + reachability_strength x 0.3
          &nbsp;-&gt;&nbsp; decayed over 365 days
        </p>
      </motion.div>
    </section>
  );
}

// --- CLI Section -------------------------------------------------------
function CLISection() {
  const { ref, inView } = useFadeInView();
  const [copied, setCopied] = useState<number | null>(null);

  const copy = (i: number, text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(i);
      setTimeout(() => setCopied(null), 1800);
    });
  };

  return (
    <section id="cli" ref={ref} style={{ padding: "0 max(24px, calc((100vw - 960px) / 2))" }}>
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={inView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.5 }}
        style={{ marginBottom: "40px" }}
      >
        <SectionLabel>CLI Reference</SectionLabel>
        <h2
          style={{
            fontSize: "clamp(24px, 4vw, 36px)",
            fontWeight: 700,
            letterSpacing: "-0.025em",
          }}
        >
          One command per stage.
        </h2>
      </motion.div>

      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {CLI_COMMANDS.map((c, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.35, delay: i * 0.07 }}
            style={{
              border: `1px solid ${T.border}`,
              borderRadius: "8px",
              background: T.surface,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "14px 20px",
                gap: "16px",
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                {/* Terminal line */}
                <div
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "13px",
                    lineHeight: 1.5,
                    whiteSpace: "pre-wrap" as const,
                    wordBreak: "break-all" as const,
                  }}
                >
                  <span style={{ color: T.muted, userSelect: "none" as const }}>$ </span>
                  <span style={{ color: T.accent }}>{c.cmd}</span>
                  <span style={{ color: "#7dd3fc" }}> {c.flags}</span>
                </div>
                <p style={{ fontSize: "12px", color: T.muted, marginTop: "4px" }}>{c.desc}</p>
              </div>

              {/* Copy button */}
              <button
                onClick={() => copy(i, `${c.cmd} ${c.flags}`)}
                style={{
                  flexShrink: 0,
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  padding: "4px 10px",
                  borderRadius: "5px",
                  border: `1px solid ${T.border}`,
                  background: "transparent",
                  color: copied === i ? T.accent : T.muted,
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
              >
                {copied === i ? "copied" : "copy"}
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

// --- Try It Section ----------------------------------------------------

const API_URL =
  process.env.NEXT_PUBLIC_EVIDENTIA_API_URL || "http://localhost:8000";

const SOURCE_OPTIONS = [
  { id: "hn", label: "Hacker News (HN)" },
  { id: "reddit", label: "Reddit" },
  { id: "github", label: "GitHub" },
] as const;

const SOURCE_LABEL_BY_ID = SOURCE_OPTIONS.reduce<Record<string, string>>((acc, option) => {
  acc[option.id] = option.label;
  return acc;
}, {});

function sourceShortcutTitle(sourceId: string): string {
  const fullLabel = SOURCE_LABEL_BY_ID[sourceId] ?? sourceId;
  return `${sourceId} = ${fullLabel}`;
}

type Opportunity = {
  opportunity_id: string;
  title: string;
  cluster_id: string;
  verdict: string;
  gate_verdict: string;
  qualification_state?: string;
  gate_failures?: string[];
  missing_evidence?: string[];
  next_action?: string;
  spec_readiness?: {
    ready_for_spec: boolean;
    blocked_by: string[];
  };
  score: number;
  final_score: number;
  willingness_to_pay: string;
  distribution_channel: string;
  data_feasibility: string;
  competition_gap: number;
  buildability: number;
  reachability_strength: number;
  published_at: string | null;
  verified_signals: { source_url: string; verbatim_quote: string }[];
};

type ScanResult = {
  opportunities: Opportunity[];
  discard_log: { source_url: string; verbatim_quote: string; reason: string }[];
  source_attempts: { source: string; status: string; count: number; message?: string }[];
};

type SpecResult = {
  opportunity_id: string;
  title: string;
  approved: boolean;
  sources: { source_url: string; verbatim_quote: string }[];
  prd: { target_user: string; core_problem: string; wedge_feature: string } | null;
};

function VerdictBadge({ verdict }: { verdict: string }) {
  const isPursue = verdict === "PURSUE";
  return (
    <span
      style={{
        fontFamily: "var(--font-mono)",
        fontSize: "10px",
        fontWeight: 700,
        letterSpacing: "0.08em",
        padding: "3px 8px",
        borderRadius: "4px",
        background: isPursue ? "rgba(74,222,128,0.1)" : "rgba(248,113,113,0.1)",
        color: isPursue ? "#4ade80" : "#f87171",
        border: `1px solid ${isPursue ? "rgba(74,222,128,0.3)" : "rgba(248,113,113,0.3)"}`,
      }}
    >
      {verdict}
    </span>
  );
}

function GatePip({ value }: { value: string }) {
  const pass = value === "pass";
  return (
    <span
      style={{
        display: "inline-block",
        width: "8px",
        height: "8px",
        borderRadius: "50%",
        background: pass ? "#4ade80" : "#f87171",
        flexShrink: 0,
      }}
      title={value}
    />
  );
}

function normalizeStatus(value: string | null | undefined): string | null {
  if (!value) return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  const lowered = trimmed.toLowerCase();
  if (lowered === "keep" || lowered === "revise" || lowered === "kill") {
    return lowered.toUpperCase();
  }
  return trimmed.toUpperCase();
}

function statusBadgeStyle(status: string) {
  if (status === "KEEP") {
    return {
      background: "rgba(74,222,128,0.1)",
      color: "#4ade80",
      border: "1px solid rgba(74,222,128,0.3)",
    };
  }
  if (status === "REVISE") {
    return {
      background: "rgba(245,158,11,0.1)",
      color: "#f59e0b",
      border: "1px solid rgba(245,158,11,0.3)",
    };
  }
  if (status === "KILL") {
    return {
      background: "rgba(248,113,113,0.1)",
      color: "#f87171",
      border: "1px solid rgba(248,113,113,0.3)",
    };
  }
  return {
    background: "rgba(148,163,184,0.1)",
    color: "#cbd5e1",
    border: "1px solid rgba(148,163,184,0.25)",
  };
}

function readTextField(value: unknown): string | null {
  if (typeof value === "string") {
    return value.trim() ? value : null;
  }
  if (Array.isArray(value)) {
    const joined = value
      .map((item) => (typeof item === "string" ? item.trim() : ""))
      .filter(Boolean)
      .join(" • ");
    return joined || null;
  }
  if (value && typeof value === "object") {
    const candidate = value as Record<string, unknown>;
    for (const key of ["text", "title", "summary", "value", "status", "status_text", "reason", "notes"]) {
      const nested = readTextField(candidate[key]);
      if (nested) {
        return nested;
      }
    }
  }
  return null;
}

function pickTextField(source: Opportunity, keys: string[]) {
  for (const key of keys) {
    const text = readTextField((source as Record<string, unknown>)[key]);
    if (text) {
      return text;
    }
  }
  return null;
}

function renderHypothesisStatus(opp: Opportunity) {
  return pickTextField(opp, [
    "prosecution_status",
    "prosecution",
    "validator_status",
    "status",
    "decision",
    "hypothesis_status",
  ]);
}

function renderHypothesisSummary(opp: Opportunity) {
  return pickTextField(opp, [
    "hypothesis",
    "hypotheses",
    "synthesis",
    "cluster_summary",
    "summary",
    "opportunity_summary",
    "generated_hypothesis",
    "hypothesis_summary",
  ]);
}

function renderProsecutionNotes(opp: Opportunity) {
  return pickTextField(opp, [
    "prosecution_notes",
    "prosecution_reason",
    "prosecution_detail",
    "prosecutor_notes",
    "validator_notes",
    "reasons",
    "notes",
  ]);
}

function OpportunityCard({
  opp,
  onSpec,
}: {
  opp: Opportunity;
  onSpec: (opp: Opportunity) => void;
}) {
  const [open, setOpen] = useState(false);
  const isPursue = opp.verdict === "PURSUE";
  const canGenerateSpec = isPursue && (opp.spec_readiness ? opp.spec_readiness.ready_for_spec : true);
  const status = renderHypothesisStatus(opp);
  const hypothesisSummary = renderHypothesisSummary(opp);
  const prosecutionNotes = renderProsecutionNotes(opp);

  return (
    <div
      style={{
        border: `1px solid ${isPursue ? "rgba(74,222,128,0.25)" : T.border}`,
        borderRadius: "8px",
        background: T.surface,
        overflow: "hidden",
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: "16px",
          padding: "16px 20px",
          cursor: "pointer",
        }}
        onClick={() => setOpen(!open)}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px", flexWrap: "wrap" as const }}>
            <VerdictBadge verdict={opp.verdict} />
            {status && (
              <span
                style={{
                  ...statusBadgeStyle(status),
                  fontFamily: "var(--font-mono)",
                  fontSize: "10px",
                  fontWeight: 700,
                  letterSpacing: "0.08em",
                  padding: "3px 8px",
                  borderRadius: "4px",
                }}
              >
                {status}
              </span>
            )}
            {opp.qualification_state && (
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.muted, letterSpacing: "0.08em" }}>
                {opp.qualification_state}
              </span>
            )}
            {isPursue && (
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.accent, fontWeight: 600 }}>
                {(opp.final_score * 100).toFixed(0)}
                <span style={{ color: T.muted, fontWeight: 400 }}>/100</span>
              </span>
            )}
            <span style={{ display: "flex", gap: "4px", alignItems: "center" }}>
              <GatePip value={opp.willingness_to_pay} />
              <GatePip value={opp.distribution_channel} />
              <GatePip value={opp.data_feasibility} />
            </span>
          </div>
          <p style={{ fontSize: "14px", fontWeight: 500, color: T.text, lineHeight: 1.4, marginBottom: "4px" }}>
            {opp.title}
          </p>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted }}>
            {opp.cluster_id}
          </span>
          {hypothesisSummary && (
            <p style={{ marginTop: "10px", fontSize: "13px", color: T.mutedLight, lineHeight: 1.6 }}>
              {hypothesisSummary}
            </p>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexShrink: 0 }}>
          {canGenerateSpec && (
            <button
              onClick={(e) => { e.stopPropagation(); onSpec(opp); }}
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "11px",
                padding: "5px 12px",
                borderRadius: "5px",
                border: `1px solid ${T.accent}`,
                background: T.accentDim,
                color: T.accent,
                cursor: "pointer",
                transition: "all 0.2s",
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = T.accent; e.currentTarget.style.color = "#000"; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = T.accentDim; e.currentTarget.style.color = T.accent; }}
            >
              {"generate spec ->"}
            </button>
          )}
          <motion.span
            animate={{ rotate: open ? 90 : 0 }}
            transition={{ duration: 0.2 }}
            style={{ color: T.muted, fontSize: "14px" }}
          >
            {">"}
          </motion.span>
        </div>
      </div>

      {/* Expanded signals */}
      <motion.div
        initial={false}
        animate={{ height: open ? "auto" : 0, opacity: open ? 1 : 0 }}
        transition={{ duration: 0.2 }}
        style={{ overflow: "hidden" }}
      >
        <div style={{ borderTop: `1px solid ${T.border}`, padding: "16px 20px" }}>
          {(hypothesisSummary || status || prosecutionNotes) && (
            <div style={{ marginBottom: "16px", display: "flex", flexDirection: "column", gap: "10px" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.muted, letterSpacing: "0.08em" }}>
                SYNTHESIZED HYPOTHESIS
              </span>
              {hypothesisSummary && (
                <p style={{ fontSize: "13px", color: T.text, lineHeight: 1.6 }}>
                  {hypothesisSummary}
                </p>
              )}
              {status && (
                <div>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.muted, letterSpacing: "0.08em", display: "block", marginBottom: "6px" }}>
                    PROSECUTION STATUS
                  </span>
                  <span
                    style={{
                      ...statusBadgeStyle(status),
                      fontFamily: "var(--font-mono)",
                      fontSize: "10px",
                      fontWeight: 700,
                      letterSpacing: "0.08em",
                      padding: "3px 8px",
                      borderRadius: "4px",
                    }}
                  >
                    {status}
                  </span>
                </div>
              )}
              {prosecutionNotes && (
                <div>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.muted, letterSpacing: "0.08em", display: "block", marginBottom: "6px" }}>
                    PROSECUTION NOTES
                  </span>
                  <p style={{ fontSize: "12px", color: T.mutedLight, lineHeight: 1.6 }}>
                    {prosecutionNotes}
                  </p>
                </div>
              )}
            </div>
          )}
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.muted, letterSpacing: "0.08em", display: "block", marginBottom: "10px" }}>
            VERIFIED SIGNALS
          </span>
          {opp.verified_signals.map((sig, i) => (
            <div key={i} style={{ marginBottom: "12px", paddingLeft: "12px", borderLeft: `2px solid ${T.border}` }}>
              <p style={{ fontSize: "13px", color: T.text, lineHeight: 1.5, marginBottom: "4px", fontStyle: "italic" }}>
                &ldquo;{sig.verbatim_quote}&rdquo;
              </p>
              <a
                href={sig.source_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted, textDecoration: "none", wordBreak: "break-all" as const }}
                onMouseEnter={(e) => { e.currentTarget.style.color = T.accent; }}
                onMouseLeave={(e) => { e.currentTarget.style.color = T.muted; }}
              >
                {sig.source_url}
              </a>
            </div>
          ))}

          {opp.missing_evidence && opp.missing_evidence.length > 0 && (
            <div style={{ marginTop: "10px", display: "flex", gap: "6px", flexWrap: "wrap" as const }}>
              {opp.missing_evidence.map((item, idx) => (
                <span
                  key={`${item}-${idx}`}
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "10px",
                    color: "#f87171",
                    border: "1px solid rgba(248,113,113,0.3)",
                    background: "rgba(248,113,113,0.06)",
                    borderRadius: "4px",
                    padding: "2px 8px",
                  }}
                >
                  {item}
                </span>
              ))}
            </div>
          )}

          {opp.next_action && (
            <div style={{ marginTop: "10px" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.muted, letterSpacing: "0.08em" }}>
                NEXT ACTION: {opp.next_action}
              </span>
            </div>
          )}

          {opp.verdict === "HOLD" && opp.gate_failures && opp.gate_failures.length > 0 ? (
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" as const, marginTop: "12px", paddingTop: "12px", borderTop: `1px solid ${T.border}` }}>
              {opp.gate_failures.map((gate) => (
                <span
                  key={gate}
                  style={{
                    background: "rgba(255,60,60,0.12)",
                    color: "#ff6b6b",
                    border: "1px solid rgba(255,60,60,0.3)",
                    borderRadius: "4px",
                    padding: "2px 8px",
                    fontSize: "11px",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  {gate.replace(/_/g, " ")} x
                </span>
              ))}
            </div>
          ) : (
            <div style={{ display: "flex", gap: "16px", marginTop: "12px", paddingTop: "12px", borderTop: `1px solid ${T.border}` }}>
              {[
                { k: "competition_gap", v: opp.competition_gap },
                { k: "buildability", v: opp.buildability },
                { k: "reachability", v: opp.reachability_strength },
              ].map(({ k, v }) => (
                <div key={k}>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.muted, display: "block", marginBottom: "4px" }}>{k}</span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: T.text }}>{v.toFixed(2)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}

function SpecPanel({ spec, onClose }: { spec: SpecResult; onClose: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        border: `1px solid ${T.accent}`,
        borderRadius: "10px",
        background: T.accentDim,
        padding: "24px",
        marginTop: "16px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
        <div>
          <SectionLabel>Generated Spec</SectionLabel>
          <h3 style={{ fontSize: "16px", fontWeight: 600, color: T.text }}>{spec.title}</h3>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted }}>{spec.opportunity_id}</span>
        </div>
        <button
          onClick={onClose}
          style={{ background: "none", border: "none", color: T.muted, cursor: "pointer", fontSize: "18px", lineHeight: 1, padding: "4px" }}
        >
          x
        </button>
      </div>

      {spec.prd && (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "20px" }}>
          {(["target_user", "core_problem", "wedge_feature"] as const).map((key) => (
            <div key={key}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.muted, letterSpacing: "0.08em", display: "block", marginBottom: "4px" }}>
                {key.replace("_", " ").toUpperCase()}
              </span>
              <p style={{ fontSize: "13px", color: T.text, lineHeight: 1.6 }}>{spec.prd![key]}</p>
            </div>
          ))}
        </div>
      )}

      <div style={{ borderTop: `1px solid ${T.border}`, paddingTop: "16px" }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.muted, letterSpacing: "0.08em", display: "block", marginBottom: "10px" }}>
          SOURCES ({spec.sources.length})
        </span>
        {spec.sources.map((s, i) => (
          <div key={i} style={{ marginBottom: "8px", paddingLeft: "10px", borderLeft: `2px solid ${T.border}` }}>
            <p style={{ fontSize: "12px", color: T.mutedLight, fontStyle: "italic", marginBottom: "2px" }}>
              &ldquo;{s.verbatim_quote}&rdquo;
            </p>
            <a href={s.source_url} target="_blank" rel="noopener noreferrer" style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.muted, textDecoration: "none" }}>
              {s.source_url}
            </a>
          </div>
        ))}
      </div>

      <div style={{ marginTop: "16px", padding: "12px", borderRadius: "6px", background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.2)" }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "#f87171" }}>
          approved: false -- review the spec and set approved: true before deploying
        </span>
      </div>
    </motion.div>
  );
}

function TryItSection() {
  const { ref, inView } = useFadeInView();
  const [domain, setDomain] = useState("");
  const [sources, setSources] = useState({ hn: true, reddit: true, github: true });
  const [maxResults, setMaxResults] = useState(3);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [specLoading, setSpecLoading] = useState<string | null>(null);
  const [specs, setSpecs] = useState<Record<string, SpecResult>>({});

  const selectedSources = Object.entries(sources).filter(([, v]) => v).map(([k]) => k);
  const normalizedDomain = domain.trim();
  const projectName = normalizedDomain ? `Evidentia + ${normalizedDomain}` : "Evidentia + Domain";

  const runScan = async () => {
    if (!domain.trim() || selectedSources.length === 0) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setSpecs({});
    try {
      const res = await fetch(`${API_URL}/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain: domain.trim(), sources: selectedSources, max_results: maxResults }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || res.statusText);
      }
      setResult(await res.json());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const generateSpec = async (opp: Opportunity) => {
    setSpecLoading(opp.opportunity_id);
    try {
      const res = await fetch(`${API_URL}/spec`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ opportunity: opp }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || res.statusText);
      }
      const spec: SpecResult = await res.json();
      setSpecs((prev) => ({ ...prev, [opp.opportunity_id]: spec }));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Spec generation failed");
    } finally {
      setSpecLoading(null);
    }
  };

  return (
    <section
      id="try"
      ref={ref}
      style={{ padding: "0 max(24px, calc((100vw - 960px) / 2))" }}
    >
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={inView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.5 }}
        style={{ marginBottom: "40px" }}
      >
        <SectionLabel>Live Pipeline</SectionLabel>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "12px",
            color: T.accent,
            marginBottom: "10px",
            letterSpacing: "0.06em",
          }}
        >
          {projectName}
        </div>
        <h2 style={{ fontSize: "clamp(24px, 4vw, 36px)", fontWeight: 700, letterSpacing: "-0.025em" }}>
          Try it now.
        </h2>
        <p style={{ color: T.muted, marginTop: "12px", fontSize: "14px", maxWidth: "480px" }}>
          Enter a domain or problem keyword. The pipeline scans real sources, verifies quotes,
          clusters the signals into synthesized hypotheses, prosecutes them, and only then scores
          the survivors. Requires{" "}
          <code style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.text, background: T.surface, padding: "1px 5px", borderRadius: "3px" }}>
            evidentia-server
          </code>{" "}
          running.
        </p>
      </motion.div>

      {/* Input form */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={inView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.4, delay: 0.15 }}
        style={{
          border: `1px solid ${T.border}`,
          borderRadius: "10px",
          background: T.surface,
          padding: "24px",
          marginBottom: "24px",
        }}
      >
        {/* Domain input */}
        <div style={{ marginBottom: "20px" }}>
          <label style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted, letterSpacing: "0.08em", display: "block", marginBottom: "8px" }}>
            DOMAIN / KEYWORD
          </label>
          <div style={{ display: "flex", gap: "10px" }}>
            <input
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runScan()}
              placeholder="e.g. invoice reconciliation, expense tracking, dev tooling..."
              style={{
                flex: 1,
                fontFamily: "var(--font-mono)",
                fontSize: "14px",
                padding: "10px 14px",
                borderRadius: "6px",
                border: `1px solid ${T.border}`,
                background: T.bg,
                color: T.text,
                outline: "none",
                transition: "border-color 0.2s",
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = T.accent; }}
              onBlur={(e) => { e.currentTarget.style.borderColor = T.border; }}
            />
            <button
              onClick={runScan}
              disabled={loading || !domain.trim() || selectedSources.length === 0}
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "13px",
                fontWeight: 600,
                padding: "10px 24px",
                borderRadius: "6px",
                border: `1px solid ${T.accent}`,
                background: loading ? T.border : T.accent,
                color: loading ? T.muted : "#000",
                cursor: loading || !domain.trim() ? "not-allowed" : "pointer",
                transition: "all 0.2s",
                whiteSpace: "nowrap" as const,
                minWidth: "100px",
              }}
            >
              {loading ? (
                <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <motion.span
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    style={{ display: "block", width: "12px", height: "12px", border: `2px solid ${T.muted}`, borderTopColor: T.text, borderRadius: "50%" }}
                  />
                  scanning
                </span>
              ) : "scan ->"}
            </button>
          </div>
        </div>

        {/* Sources + max results */}
        <div style={{ display: "flex", gap: "32px", alignItems: "flex-start", flexWrap: "wrap" as const }}>
          <div>
            <label style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted, letterSpacing: "0.08em", display: "block", marginBottom: "8px" }}>
              SOURCES
            </label>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" as const }}>
              {SOURCE_OPTIONS.map(({ id, label }) => (
                <button
                  key={id}
                  onClick={() => setSources((prev) => ({ ...prev, [id]: !prev[id] }))}
                  title={sourceShortcutTitle(id)}
                  aria-label={sourceShortcutTitle(id)}
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "12px",
                    padding: "5px 12px",
                    borderRadius: "5px",
                    border: `1px solid ${sources[id] ? T.accent : T.border}`,
                    background: sources[id] ? T.accentDim : "transparent",
                    color: sources[id] ? T.accent : T.muted,
                    cursor: "pointer",
                    transition: "all 0.15s",
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: T.muted, letterSpacing: "0.08em", display: "block", marginBottom: "8px" }}>
              MAX RESULTS PER SOURCE
            </label>
            <div style={{ display: "flex", gap: "4px" }}>
              {[1, 3, 5, 10].map((n) => (
                <button
                  key={n}
                  onClick={() => setMaxResults(n)}
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "12px",
                    width: "36px",
                    height: "30px",
                    borderRadius: "5px",
                    border: `1px solid ${maxResults === n ? T.accent : T.border}`,
                    background: maxResults === n ? T.accentDim : "transparent",
                    color: maxResults === n ? T.accent : T.muted,
                    cursor: "pointer",
                    transition: "all 0.15s",
                  }}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Error */}
      {error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{
            padding: "14px 18px",
            borderRadius: "8px",
            border: "1px solid rgba(248,113,113,0.3)",
            background: "rgba(248,113,113,0.06)",
            marginBottom: "20px",
          }}
        >
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "#f87171" }}>
            error: {error}
          </span>
        </motion.div>
      )}

      {/* Results */}
      {result && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          {/* Source attempt badges */}
          {result.source_attempts?.length > 0 && (
            <div style={{ display: "flex", gap: "6px", marginBottom: "20px", flexWrap: "wrap" as const }}>
              {result.source_attempts.map((a) => (
                <span
                  key={a.source}
                  title={sourceShortcutTitle(a.source)}
                  aria-label={sourceShortcutTitle(a.source)}
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "11px",
                    padding: "3px 10px",
                    borderRadius: "4px",
                    border: `1px solid ${a.status === "ok" ? "rgba(74,222,128,0.3)" : "rgba(248,113,113,0.3)"}`,
                    color: a.status === "ok" ? "#4ade80" : "#f87171",
                    background: a.status === "ok" ? "rgba(74,222,128,0.06)" : "rgba(248,113,113,0.06)",
                  }}
                >
                  {a.source}: {a.status === "ok" ? `${a.count} hits` : a.status}
                </span>
              ))}
            </div>
          )}

          {/* Synthesized hypotheses */}
          {result.opportunities.length === 0 ? (
            <div style={{ textAlign: "center" as const, padding: "48px 0", color: T.muted, fontFamily: "var(--font-mono)", fontSize: "13px" }}>
              no synthesized hypotheses returned -- all candidates were KEEP/REVISE/KILL or discarded
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginBottom: "24px" }}>
              {result.opportunities.map((opp) => (
                <div key={opp.opportunity_id}>
                  <OpportunityCard
                    opp={opp}
                    onSpec={generateSpec}
                  />
                  {specLoading === opp.opportunity_id && (
                    <div style={{ padding: "12px 0", fontFamily: "var(--font-mono)", fontSize: "12px", color: T.muted }}>
                      generating spec...
                    </div>
                  )}
                  {specs[opp.opportunity_id] && (
                    <SpecPanel
                      spec={specs[opp.opportunity_id]}
                      onClose={() => setSpecs((prev) => {
                        const next = { ...prev };
                        delete next[opp.opportunity_id];
                        return next;
                      })}
                    />
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Discard log */}
          {result.discard_log?.length > 0 && (
            <details style={{ marginTop: "8px" }}>
              <summary
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "12px",
                  color: T.muted,
                  cursor: "pointer",
                  padding: "8px 0",
                  listStyle: "none",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <span style={{ color: T.border }}>{">"}</span>
                {result.discard_log.length} discarded
              </summary>
              <div style={{ marginTop: "8px", display: "flex", flexDirection: "column", gap: "4px" }}>
                {result.discard_log.map((d, i) => (
                  <div
                    key={i}
                    style={{
                      padding: "10px 14px",
                      borderRadius: "6px",
                      border: `1px solid ${T.border}`,
                      background: T.surface,
                    }}
                  >
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "#f87171", display: "block", marginBottom: "4px" }}>
                      {d.reason}
                    </span>
                    <p style={{ fontSize: "12px", color: T.muted, fontStyle: "italic" }}>
                      &ldquo;{d.verbatim_quote}&rdquo;
                    </p>
                    <a href={d.source_url} target="_blank" rel="noopener noreferrer" style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: T.muted, textDecoration: "none", wordBreak: "break-all" as const }}>
                      {d.source_url}
                    </a>
                  </div>
                ))}
              </div>
            </details>
          )}
        </motion.div>
      )}
    </section>
  );
}

// --- Footer ------------------------------------------------------------
function Footer() {
  return (
    <footer
      style={{
        borderTop: `1px solid ${T.border}`,
        padding: "40px max(24px, calc((100vw - 960px) / 2))",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap" as const,
        gap: "16px",
      }}
    >
      <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: T.muted }}>
        evidentia v0.1.0
      </span>
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "12px",
          color: T.muted,
          display: "flex",
          alignItems: "center",
          gap: "8px",
        }}
      >
        <span style={{ color: T.border }}>*</span>
        <span>
          anti-hallucination contract: every claim traces to a{" "}
          <span style={{ color: T.text }}>URL</span> and a{" "}
          <span style={{ color: T.text }}>verbatim quote</span>
        </span>
      </div>
    </footer>
  );
}

// --- Page --------------------------------------------------------------
export default function Page() {
  return (
    <main style={{ background: T.bg, minHeight: "100vh" }}>
      <Nav />
      <Hero />

      <div style={{ padding: "80px 0", display: "flex", flexDirection: "column", gap: "80px" }}>
        <PipelineSection />
        <Divider />
        <ProofLevelsSection />
        <Divider />
        <ScoringSection />
        <Divider />
        <TryItSection />
        <Divider />
        <CLISection />
      </div>

      <Footer />
    </main>
  );
}
