export const T = {
  bg: "#0a0a0a",
  surface: "#111111",
  surfaceHover: "#161616",
  border: "#1f1f1f",
  accent: "#e2ff5d",
  accentDim: "rgba(226,255,93,0.08)",
  text: "#f0f0f0",
  muted: "#666666",
  mutedLight: "#888888",
  success: "#22c55e",
  danger: "#ef4444",
  warning: "#f59e0b",
  glassBg: "rgba(255,255,255,0.03)",
  glassBorder: "rgba(255,255,255,0.08)",
  glassAccentBg: "rgba(226,255,93,0.06)",
  glassAccentBorder: "rgba(226,255,93,0.15)",
} as const;

export type Tokens = typeof T;
