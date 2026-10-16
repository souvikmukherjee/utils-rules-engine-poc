import type { NextConfig } from "next";
import path from "path";

/** Backend target for same-origin `/api/*` rewrites (avoids browser CORS). */
const API_PROXY_TARGET =
  process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  turbopack: {
    root: path.join(__dirname, "../.."),
  },
  transpilePackages: ["@gorules/jdm-editor"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_PROXY_TARGET.replace(/\/$/, "")}/:path*`,
      },
    ];
  },
};

export default nextConfig;
