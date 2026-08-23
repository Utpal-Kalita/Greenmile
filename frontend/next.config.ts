import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Vercel packages the normal Next.js output; standalone is for the Docker image.
  ...(process.env.VERCEL === "1" ? {} : { output: "standalone" as const }),
  turbopack: {
    root: path.resolve(__dirname, ".."),
  },
};

export default nextConfig;
