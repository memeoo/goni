/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // Use BACKEND_URL for server-side rewrites, fallback to localhost for development
    const apiUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ]
  },
  outputFileTracingRoot: '/home/ubuntu/goni/front',
  experimental: {
    allowedDevOrigins: ['3.34.102.218', 'localhost', '127.0.0.1'],
  },
}

module.exports = nextConfig