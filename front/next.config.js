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
  allowedDevOrigins: ['http://3.34.102.218:3001'],
}

module.exports = nextConfig