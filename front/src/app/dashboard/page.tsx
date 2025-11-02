'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { tradingPlansAPI } from '@/lib/api'
import Header from '@/components/header'
import PlanStockCard from '@/components/plan-stock-card'
import TradeCard from '@/components/trade-card'
import RecapModal from '@/components/recap-modal'

// 실제 주식 데이터 조회 함수
// Next.js API route를 통해 프록시로 백엔드 호출 (상대 경로 사용)
const fetchStocks = async () => {
  // const response = await fetch('/api/stocks')
  // if (!response.ok) {
  //   throw new Error('주식 데이터 조회 실패')
  // }
  // return response.json()
  return []
}

// 실제 매매 내역 조회 함수 (Trading DB에서 조회)
const fetchRecentTrades = async () => {
  const response = await tradingPlansAPI.getRecentTrades(20)
  return response.data
}

type Mode = 'plan' | 'review'

export default function DashboardPage() {
  const [mounted, setMounted] = useState(false)
  const [mode, setMode] = useState<Mode>('review')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedTradingPlanId, setSelectedTradingPlanId] = useState<number | null>(null)
  const [selectedOrderNo, setSelectedOrderNo] = useState<string | undefined>(undefined)
  const [selectedStockName, setSelectedStockName] = useState<string | undefined>(undefined)
  const [selectedStockCode, setSelectedStockCode] = useState<string | undefined>(undefined)

  // 실제 주식 데이터 조회 (계획 모드용)
  const { data: stocks = [], isLoading: isLoadingStocks, error: stocksError } = useQuery({
    queryKey: ['stocks'],
    queryFn: fetchStocks,
    refetchInterval: 60000, // 1분마다 갱신
    enabled: mode === 'plan', // 계획 모드일 때만 실행
  })

  // 실제 매매 내역 조회 (복기 모드용)
  const { data: tradesData, isLoading: isLoadingTrades, error: tradesError } = useQuery({
    queryKey: ['recentTrades'],
    queryFn: fetchRecentTrades,
    refetchInterval: 300000, // 5분마다 갱신
  })

  const trades = tradesData?.data || []
  const isLoading = mode === 'plan' ? isLoadingStocks : isLoadingTrades
  const error = mode === 'plan' ? stocksError : tradesError

  // 대시보드 진입 시 매매 기록 동기화
  useEffect(() => {
    setMounted(true)

    // 로그인 후 처음 대시보드에 진입할 때만 동기화 수행
    const syncTrades = async () => {
      try {
        console.log('📊 매매 기록 동기화 시작...')
        const response = await tradingPlansAPI.syncRecentTrades(20)
        console.log('✅ 매매 기록 동기화 완료:', response.data)
      } catch (error) {
        console.error('❌ 매매 기록 동기화 실패:', error)
        // 동기화 실패해도 대시보드는 정상 진행
      }
    }

    syncTrades()
  }, [])

  if (!mounted) return null

  // 로딩 상태 처리
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">주식 데이터 로딩 중...</p>
        </div>
      </div>
    )
  }

  // 오류 상태 처리
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">데이터 로딩 중 오류가 발생했습니다.</p>
          <p className="text-gray-600">{error.message}</p>
        </div>
      </div>
    )
  }

  const handleModeChange = (newMode: Mode) => {
    setMode(newMode)
  }

  const handleRefresh = () => {
    // TODO: Implement refresh functionality
    console.log('새로고침')
  }

  const handleAddStock = () => {
    // TODO: Implement add stock functionality
    console.log('종목 추가')
  }

  const handleStrategyManage = () => {
    // TODO: Implement strategy management functionality
    console.log('전략 관리')
  }

  const handleStockCardClick = (id: number, trade?: any) => {
    if (mode === 'review' && trade) {
      // 복기 모드에서는 모달 열기
      // trade 데이터에는 order_no만 있고 trading_plan_id가 없음
      setSelectedTradingPlanId(null)
      setSelectedOrderNo(trade.order_no)
      setSelectedStockName(trade.stock_name || trade.name)
      setSelectedStockCode(trade.stock_code)
      setIsModalOpen(true)
    } else {
      // 계획 모드에서는 아직 미구현
      console.log(`카드 클릭: ${id}`)
    }
  }

  // 복기 모드에서 종목별 최신 거래만 필터링
  const getLatestTradesByStock = (trades: any[]) => {
    const tradeMap = new Map<string, any>()

    // 각 종목의 가장 최신 거래만 유지
    for (const trade of trades) {
      const stockCode = trade.stock_code
      if (!tradeMap.has(stockCode)) {
        tradeMap.set(stockCode, trade)
      }
    }

    // Map을 배열로 변환하고 최신순 정렬
    return Array.from(tradeMap.values()).sort((a, b) => {
      return new Date(b.datetime).getTime() - new Date(a.datetime).getTime()
    })
  }

  // Create empty slots to fill grid to at least 8 items (2 rows × 4 columns)
  const createGridItems = (items: any[], mode: Mode) => {
    const minItems = 8
    const gridItems = mode === 'review' ? getLatestTradesByStock(items) : [...items]

    while (gridItems.length < minItems) {
      gridItems.push(null)
    }

    return gridItems.map((item, index) => (
      <div key={item?.id || item?.order_no || `empty-${index}`}>
        {mode === 'plan' ? (
          <PlanStockCard
            stock={item}
            onClick={item ? () => handleStockCardClick(item.id) : undefined}
          />
        ) : (
          <TradeCard
            trade={item}
            onClick={item ? () => handleStockCardClick(item.order_no || index, item) : undefined}
          />
        )}
      </div>
    ))
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <Header
        mode={mode}
        onModeChange={handleModeChange}
        onRefresh={handleRefresh}
        onAddStock={handleAddStock}
        onStrategyManage={handleStrategyManage}
      />

      {/* Main Content */}
      <main className="mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Mode Title */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            {mode === 'plan' ? '계획 모드' : '복기 모드'}
          </h2>
          <p className="text-gray-600">
            {mode === 'plan' 
              ? '관심 종목을 모니터링하고 매매 계획을 세워보세요'
              : '완료된 매매 기록을 확인하고 복기해보세요'
            }
          </p>
        </div>

        {/* Grid Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
          {mode === 'plan'
            ? createGridItems(stocks, 'plan')
            : createGridItems(trades, 'review')
          }
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

      {/* Recap Modal */}
      <RecapModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        tradingPlanId={selectedTradingPlanId}
        orderNo={selectedOrderNo}
        stockName={selectedStockName}
        stockCode={selectedStockCode}
      />
    </div>
  )
}