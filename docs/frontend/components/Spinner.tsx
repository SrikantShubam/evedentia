export function Spinner({ size = 24 }: { size?: number }) {
  return (
    <div style={{
      width: size, height: size,
      border: "3px solid rgba(124,92,252,0.2)",
      borderTopColor: "#7c5cfc",
      borderRadius: "50%",
      animation: "spin 0.6s linear infinite",
    }} />
  );
}
