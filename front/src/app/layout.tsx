import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { QueryProvider } from '@/lib/providers'
import { ToastProvider } from '@/lib/toast-provider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Goni - 매매 계획 및 복기 일지',
  description: '주식 매매 계획 수립과 복기를 통한 트레이딩 실력 향상 플랫폼',
  keywords: ['주식', '매매', '투자', '트레이딩', '복기', '일지'],
  authors: [{ name: 'Goni Team' }],
  icons: {
    icon: '/favicon.ico',
  },
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className={inter.className}>
        <QueryProvider>
          {children}
          <ToastProvider />
        </QueryProvider>
      </body>
    </html>
  )
}