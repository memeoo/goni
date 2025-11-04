'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { tradingAPI, tradingStocksAPI } from '@/lib/api'
import Header from '@/components/header'
import PlanStockCard from '@/components/plan-stock-card'
import TradeCard from '@/components/trade-card'
import RecapModal from '@/components/recap-modal'

// 매매 종목 조회 함수 (trading_stocks 테이블에서 조회)
const fetchTradingStocks = async () => {
  const response = await tradingStocksAPI.getTradingStocks(0, 100)

  // 응답 데이터 형식에 따라 처리
  const stocksData = response.data || (Array.isArray(response) ? response : [])

  return stocksData.map((stock: any) => ({
    id: stock.id,
    stock_code: stock.stock_code,
    stock_name: stock.stock_name,
    is_downloaded: stock.is_downloaded,
  }))
}

// 실제 매매 내역 조회 함수 (Trading DB에서 조회)
const fetchRecentTrades = async () => {
  const response = await tradingAPI.getRecentTrades(100)

  // Trading API 응답을 TradeCard 형식으로 변환
  const trades = Array.isArray(response) ? response : response.data || []

  return trades.map((trade: any) => ({
    id: trade.id,
    stock_code: trade.stock_code,
    stock_name: trade.stock_name,
    trade_type: trade.trade_type === 'buy' ? '매수' : '매도', // 'buy'/'sell' -> '매수'/'매도'
    price: trade.executed_price,
    quantity: trade.executed_quantity,
    datetime: trade.executed_at, // ISO 형식
    order_no: trade.order_no,
    has_recap: false, // TODO: 복기 여부 확인 로직 추가
  }))
}

type Mode = 'plan' | 'review'

export default function DashboardPage() {
  const [mounted, setMounted] = useState(false)
  const [mode, setMode] = useState<Mode>('review')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedTradingPlanId, setSelectedTradingPlanId] = useState<number | null>(null)
  const [selectedTradingId, setSelectedTradingId] = useState<number | null>(null)
  const [selectedOrderNo, setSelectedOrderNo] = useState<string | undefined>(undefined)
  const [selectedStockName, setSelectedStockName] = useState<string | undefined>(undefined)
  const [selectedStockCode, setSelectedStockCode] = useState<string | undefined>(undefined)

  // 매매 종목 데이터 조회 (계획 모드용)
  const { data: stocks = [], isLoading: isLoadingStocks, error: stocksError } = useQuery({
    queryKey: ['tradingStocks'],
    queryFn: fetchTradingStocks,
    refetchInterval: 60000, // 1분마다 갱신
    enabled: mode === 'plan', // 계획 모드일 때만 실행
  })

  // 실제 매매 내역 조회 (복기 모드용)
  const { data: tradesData, isLoading: isLoadingTrades, error: tradesError } = useQuery({
    queryKey: ['recentTrades'],
    queryFn: fetchRecentTrades,
    refetchInterval: 300000, // 5분마다 갱신
  })

  const trades = tradesData || []
  const isLoading = mode === 'plan' ? isLoadingStocks : isLoadingTrades
  const error = mode === 'plan' ? stocksError : tradesError

  // 마운트 상태 설정 및 Kiwoom 자동 동기화
  useEffect(() => {
    setMounted(true)

    // 컴포넌트 마운트 시 Kiwoom에서 매매 기록 동기화
    const syncKiwoomTrades = async () => {
      try {
        console.log('🔄 Kiwoom API에서 매매 기록 동기화 중...')
        const response = await tradingStocksAPI.syncFromKiwoom(30) // 최근 30일 조회
        console.log('✅ Kiwoom 동기화 완료:', response.data)
      } catch (error) {
        console.warn('⚠️ Kiwoom 동기화 실패:', error)
        // 동기화 실패해도 계속 진행 (기존 데이터 표시)
      }
    }

    syncKiwoomTrades()
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

  const handleStockCardClick = (tradeId: number) => {
    if (mode === 'review') {
      // 복기 모드에서는 모달 열기
      // trading_id를 기반으로 거래 기록과 매핑
      setSelectedTradingPlanId(null)
      setSelectedTradingId(tradeId)
      setSelectedOrderNo(undefined)
      setIsModalOpen(true)
    } else {
      // 계획 모드에서는 아직 미구현
      console.log(`카드 클릭: ${tradeId}`)
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
      try {
        const aTime = a.datetime ? new Date(a.datetime).getTime() : 0
        const bTime = b.datetime ? new Date(b.datetime).getTime() : 0
        return bTime - aTime
      } catch (e) {
        console.warn('[getLatestTradesByStock] Error parsing date:', a.datetime, b.datetime)
        return 0
      }
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
            onClick={item && item.id ? handleStockCardClick : undefined}
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
        tradingId={selectedTradingId}
        orderNo={selectedOrderNo}
        stockName={selectedStockName}
        stockCode={selectedStockCode}
      />
    </div>
  )
}