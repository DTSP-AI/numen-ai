/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    ignoreDuringBuilds: true, // Allow build to proceed despite linting warnings
  },
  typescript: {
    ignoreBuildErrors: false, // Keep type checking enabled
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003',
  },
}

module.exports = nextConfig