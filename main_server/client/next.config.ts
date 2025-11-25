import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  transpilePackages: ['echarts', 'zrender'],
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '81',
        pathname: '/image/**',
      },
    ],
  },
};

export default nextConfig;
