'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { ArrowLeft, TrendingUp, Calendar } from 'lucide-react'
import Header from '@/components/header'
import { recStocksAPI } from '@/lib/api'

interface Algorithm {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

interface RecStock {
  id: number
  stock_name: string
  stock_code: string
  recommendation_date: string
  algorithm_id: number
  closing_price: number
  change_rate: number | null
  created_at: string
  updated_at: string
  algorithm: Algorithm
}

interface GroupedRecStocks {
  [date: string]: RecStock[]
}

export default function AlgorithmDetailPage() {
  const router = useRouter()
  const params = useParams()
  const algorithmId = params.algorithmId as string

  const [algorithm, setAlgorithm] = useState<Algorithm | null>(null)
  const [recStocks, setRecStocks] = useState<RecStock[]>([])
  const [groupedStocks, setGroupedStocks] = useState<GroupedRecStocks>({})
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchRecStocks()
  }, [algorithmId])

  const fetchRecStocks = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await recStocksAPI.getRecStocksByAlgorithm(parseInt(algorithmId), 0, 100)
      const data = response.data

      if (data && data.data) {
        setRecStocks(data.data)

        // 첫 번째 항목의 알고리즘 정보 설정
        if (data.data.length > 0 && data.data[0].algorithm) {
          setAlgorithm(data.data[0].algorithm)
        }

        // 날짜별로 그룹핑 (최신 순)
        if (data.data.length > 0) {
          const grouped: GroupedRecStocks = {}
          data.data.forEach((stock: RecStock) => {
            const date = stock.recommendation_date
            if (!grouped[date]) {
              grouped[date] = []
            }
            grouped[date].push(stock)
          })

          // 날짜를 최신순으로 정렬
          const sortedGrouped: GroupedRecStocks = {}
          Object.keys(grouped)
            .sort((a, b) => new Date(b).getTime() - new Date(a).getTime())
            .forEach((date) => {
              sortedGrouped[date] = grouped[date]
            })

          setGroupedStocks(sortedGrouped)
        }
      }
    } catch (err) {
      console.error('추천 종목 조회 중 오류:', err)
      setError(err instanceof Error ? err.message : '추천 종목을 불러올 수 없습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleBack = () => {
    router.back()
  }

  const handleModeChange = () => {
    // 추천 페이지에서는 모드 변경 불가
  }

  const handleRefresh = () => {
    fetchRecStocks()
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
          <p className="text-gray-600">추천 종목 로딩 중...</p>
        </div>
      </div>
    )
  }

  if (error && Object.keys(groupedStocks).length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">오류가 발생했습니다.</p>
          <p className="text-gray-600">{error}</p>
          <button
            onClick={handleBack}
            className="mt-6 inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            돌아가기
          </button>
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
        onPrincipleManage={() => {}}
        isRefreshing={false}
      />

      {/* Main Content */}
      <main className="mx-auto px-3 sm:px-4 md:px-6 lg:px-8 py-4 sm:py-6 md:py-8">
        {/* Back Button */}
        <button
          onClick={handleBack}
          className="inline-flex items-center px-3 py-2 mb-4 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          돌아가기
        </button>

        {/* Title Section */}
        <div className="mb-6 sm:mb-8">
          {algorithm ? (
            <>
              <div className="flex items-center gap-3 mb-2">
                <TrendingUp className="h-8 w-8 sm:h-10 sm:w-10 text-blue-600" />
                <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900">
                  {algorithm.name}
                </h2>
              </div>
              {algorithm.description && (
                <p className="text-sm sm:text-base text-gray-600 ml-11">
                  {algorithm.description}
                </p>
              )}
            </>
          ) : (
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">
              추천 종목
            </h2>
          )}
          <p className="text-sm sm:text-base text-gray-500 mt-2">
            총 {recStocks.length}개 종목
          </p>
        </div>

        {/* Grouped by Date */}
        {Object.keys(groupedStocks).length > 0 ? (
          <div className="space-y-8">
            {Object.entries(groupedStocks).map(([date, stocks]) => (
              <div key={date}>
                {/* Date Header */}
                <div className="flex items-center gap-2 mb-4">
                  <Calendar className="h-5 w-5 text-blue-600" />
                  <h3 className="text-lg sm:text-xl font-semibold text-gray-900">
                    {new Date(date).toLocaleDateString('ko-KR', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      weekday: 'short',
                    })}
                  </h3>
                  <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs sm:text-sm font-semibold rounded-full">
                    {stocks.length}개
                  </span>
                </div>

                {/* Stock List Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4">
                  {stocks.map((stock) => (
                    <div
                      key={stock.id}
                      className="bg-white border border-gray-200 rounded-lg p-3 sm:p-4 hover:shadow-md transition-shadow"
                    >
                      {/* Stock Name and Code */}
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="text-sm sm:text-base font-semibold text-gray-900">
                            {stock.stock_name}
                          </h4>
                          <p className="text-xs sm:text-sm text-gray-500">
                            {stock.stock_code}
                          </p>
                        </div>
                      </div>

                      {/* Stock Price */}
                      <div className="mb-3">
                        <p className="text-xs text-gray-500 mb-1">종가</p>
                        <p className="text-lg sm:text-xl font-bold text-gray-900">
                          ₩{stock.closing_price.toLocaleString()}
                        </p>
                      </div>

                      {/* Change Rate */}
                      {stock.change_rate !== null && (
                        <div className="pt-3 border-t border-gray-200">
                          <p className="text-xs text-gray-500 mb-1">전일비</p>
                          <p
                            className={`text-sm font-semibold ${
                              stock.change_rate >= 0
                                ? 'text-red-600'
                                : 'text-blue-600'
                            }`}
                          >
                            {stock.change_rate >= 0 ? '+' : ''}
                            {stock.change_rate.toFixed(2)}%
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <p className="text-gray-500 text-lg">추천 종목이 없습니다.</p>
              <p className="text-sm text-gray-400 mt-2">아직 이 알고리즘의 추천 데이터가 없습니다.</p>
            </div>
          </div>
        )}
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
