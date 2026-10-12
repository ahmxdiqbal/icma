import type { NextConfig } from "next";

const TRADITION_FILES = ["./data/traditions/**/*.json"];

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // Pages read tradition packages from disk; keep them in traced server output.
  outputFileTracingIncludes: {
    "/": TRADITION_FILES,
    "/t/[id]": TRADITION_FILES,
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
