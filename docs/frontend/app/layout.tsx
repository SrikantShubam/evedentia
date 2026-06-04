import type { Metadata } from "next";
import "./globals.css";
import { StitchShell } from "@/components/stitch/StitchShell";
import { Sidebar } from "@/components/stitch/Sidebar";
import { TopNav } from "@/components/stitch/TopNav";

export const metadata: Metadata = {
  title: "Evidentia + Domain",
  description:
    "Replace opinion-based product decisions with traceable demand signals. Every claim traces to a URL and a verbatim quote.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body suppressHydrationWarning>
        <StitchShell>
          <div style={{ display: "flex", minHeight: "100vh" }}>
            <Sidebar />
            <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
              <TopNav />
              <main style={{ flex: 1, padding: "24px" }}>{children}</main>
            </div>
          </div>
        </StitchShell>
      </body>
    </html>
  );
}
