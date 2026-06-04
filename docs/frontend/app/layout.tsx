import type { Metadata } from "next";
import "./globals.css";
import StitchShell from "@/components/stitch/StitchShell";
import Sidebar from "@/components/stitch/Sidebar";
import TopNav from "@/components/stitch/TopNav";

export const metadata: Metadata = {
  title: "Evidentia — AI Idea Validator",
  description: "Replace opinion-based product decisions with traceable demand signals.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Public+Sans:wght@400;600&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet" />
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      </head>
      <body suppressHydrationWarning>
        <StitchShell>
          <div style={{ display: "flex", minHeight: "100vh" }}>
            <Sidebar />
            <div style={{ flex: 1, display: "flex", flexDirection: "column", marginLeft: 256 }}>
              <TopNav />
              <main style={{ flex: 1, padding: "24px" }}>{children}</main>
            </div>
          </div>
        </StitchShell>
      </body>
    </html>
  );
}
