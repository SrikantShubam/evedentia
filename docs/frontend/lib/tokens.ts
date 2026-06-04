export const T = {
  bg: "#0a0a0a",
  surface: "#111111",
  surfaceHover: "#161616",
  border: "#1f1f1f",
  accent: "#7c5cfc",
  accentDim: "rgba(124,92,252,0.08)",
  text: "#f0f0f0",
  muted: "#666666",
  mutedLight: "#888888",
  success: "#22c55e",
  danger: "#ef4444",
  warning: "#f59e0b",
  glassBg: "rgba(255,255,255,0.03)",
  glassBorder: "rgba(255,255,255,0.08)",
  glassAccentBg: "rgba(124,92,252,0.06)",
  glassAccentBorder: "rgba(124,92,252,0.15)",
} as const;

export type Tokens = typeof T;
