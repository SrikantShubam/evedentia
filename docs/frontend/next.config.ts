import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // NEXT_PUBLIC_EVIDENTIA_API_URL is baked in at build time for static hosts.
  // For Vercel, set it in Project -> Settings -> Environment Variables.
  // Default falls back to localhost for local dev.
};

export default nextConfig;
