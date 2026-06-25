import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    const apiTarget = process.env.NEXT_PUBLIC_API_TARGET ?? "http://127.0.0.1:8000";

    return [
      {
        source: "/api/:path*",
        destination: `${apiTarget}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
