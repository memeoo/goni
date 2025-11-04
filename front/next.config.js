/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
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