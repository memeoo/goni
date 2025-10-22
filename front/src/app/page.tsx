'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Cookies from 'js-cookie'

export default function HomePage() {
  const router = useRouter()

  useEffect(() => {
    // 토큰 확인 (쿠키와 로컬스토리지 모두 확인)
    const token = Cookies.get('access_token') || localStorage.getItem('access_token')

    // 로그인 여부에 따라 리다이렉트
    if (token) {
      router.push('/dashboard')
    } else {
      router.push('/login')
    }
  }, [router])

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">로딩 중...</p>
      </div>
    </div>
  )
}