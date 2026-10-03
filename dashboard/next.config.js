/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // Server actions need this for fetch to the api service in development.
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/proxy/:path*",
        destination: `${apiUrl}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;