import type { Metadata } from "next";
import { Roboto } from "next/font/google";
import "./globals.css";

const roboto = Roboto({
  variable: "--font-roboto",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

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
      <body className={`${roboto.className} ${roboto.variable}`}>
        {children}
      </body>
    </html>
  );
}
