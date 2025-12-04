'use client'

import { useState, useEffect } from 'react'
import Header from '@/components/header'
import AlgorithmCard from '@/components/algorithm-card'

interface Algorithm {
  id: number
  name: string
  description: string
  created_at: string
  updated_at: string
}

export default function RecommendationPage() {
  const [algorithms, setAlgorithms] = useState<Algorithm[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAlgorithms()
  }, [])

  const fetchAlgorithms = async () => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/algorithms')
      if (!response.ok) {
        throw new Error('알고리즘 목록 조회 실패')
      }
      const data = await response.json()
      setAlgorithms(data.data || [])
      console.log('✅ 알고리즘 목록 조회 완료:', data.data)
    } catch (err) {
      console.error('❌ 알고리즘 목록 조회 중 오류:', err)
      setError(err instanceof Error ? err.message : '알고리즘 목록을 불러올 수 없습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleModeChange = () => {
    // 추천 페이지에서는 모드 변경 불가
  }

  const handleRefresh = () => {
    // 새로고침 기능
    fetchAlgorithms()
  }

  const handleAddStock = () => {
    // 추천 페이지에서는 종목 추가 불가
  }

  const handleStrategyManage = () => {
    // 대시보드로 돌아가기
    window.location.href = '/dashboard'
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">알고리즘 정보 로딩 중...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">오류가 발생했습니다.</p>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <Header
        mode="plan"
        onModeChange={handleModeChange}
        onRefresh={handleRefresh}
        onAddStock={handleAddStock}
        onStrategyManage={handleStrategyManage}
        onPrincipleManage={() => { }}
        isRefreshing={false}
      />

      {/* Main Content */}
      <main className="mx-auto px-3 sm:px-4 md:px-6 lg:px-8 py-4 sm:py-6 md:py-8">
        {/* Title Section */}
        <div className="mb-4 sm:mb-6 md:mb-8">
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-1 sm:mb-2">
            알고리즘 종목 추천
          </h2>
          <p className="text-sm sm:text-base text-gray-600">
            고니 퀀트 알고리즘으로 제공되는 추천 종목
          </p>
        </div>

        {/* Grid Layout - 모바일 1열, 태블릿 2열, 데스크톱 3-4열 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
          {algorithms.length === 0 ? (
            // Empty state - 데이터가 없으므로 빈 상태 표시
            <div className="col-span-full flex items-center justify-center py-16">
              <div className="text-center">
                <p className="text-gray-500 text-lg">곧 추천 종목이 업데이트됩니다.</p>
                <p className="text-sm text-gray-400 mt-2">매일 아침 7시에 새로운 추천 종목이 제공됩니다.</p>
              </div>
            </div>
          ) : (
            // 알고리즘 카드 목록
            algorithms.map((algorithm) => (
              <AlgorithmCard key={algorithm.id} algorithm={algorithm} />
            ))
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-500 text-sm">
            © 2024 Goni. 타짜급 트레이더로 성장하는 매매 일지 플랫폼
          </div>
        </div>
      </footer>
    </div>
  )
}
