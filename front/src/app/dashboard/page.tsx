'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { tradingAPI, tradingStocksAPI, tradingPlansAPI } from '@/lib/api'
import Header from '@/components/header'
import PlanStockCard from '@/components/plan-stock-card'
import RecapStockCard from '@/components/recap-stock-card'
import RecapModal from '@/components/recap-modal'
import StockSearchModal from '@/components/stock-search-modal'
import RecapStockAddModal from '@/components/recap-stock-add-modal'
import TradingPlanFormModal from '@/components/trading-plan-form-modal'

// 계획 모드 종목 조회 함수 (trading_plans 테이블에서 조회)
const fetchPlanModeStocks = async () => {
  const response = await tradingPlansAPI.getPlanModeStocks(0, 100)

  // axios 응답 처리: response.data = { data: [...], total: ..., ... }
  const stocks = response.data?.data || []

  return stocks.map((stock: any) => ({
    id: stock.id,
    stock_code: stock.stock_code,
    stock_name: stock.stock_name,
  }))
}

// 매매 종목 조회 함수 (trading_stocks 테이블에서 조회)
const fetchTradingStocks = async () => {
  const response = await tradingStocksAPI.getTradingStocks(0, 100)

  // axios 응답 처리: response.data = { data: [...], total: ..., ... }
  const stocks = response.data?.data || []

  return stocks.map((stock: any) => ({
    id: stock.id,
    stock_code: stock.stock_code,
    stock_name: stock.stock_name,
    is_downloaded: stock.is_downloaded,
  }))
}

// 복기 모드용 종목 조회 함수 (trading_stocks 테이블에서 조회)
const fetchRecentTrades = async () => {
  const response = await tradingStocksAPI.getTradingStocks(0, 100)

  // axios 응답 처리: response.data = { data: [...], total: ..., ... }
  const stocks = response.data?.data || []

  return stocks.map((stock: any) => ({
    id: stock.id,
    stock_code: stock.stock_code,
    stock_name: stock.stock_name,
    is_downloaded: stock.is_downloaded,
    recent_trades: stock.recent_trades || [],
  }))
}

type Mode = 'plan' | 'review'

export default function DashboardPage() {
  const [mounted, setMounted] = useState(false)
  const [mode, setMode] = useState<Mode>('plan')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false)
  const [isPlanFormModalOpen, setIsPlanFormModalOpen] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [selectedTradingPlanId, setSelectedTradingPlanId] = useState<number | null>(null)
  const [selectedTradingId, setSelectedTradingId] = useState<number | null>(null)
  const [selectedOrderNo, setSelectedOrderNo] = useState<string | undefined>(undefined)
  const [selectedStockName, setSelectedStockName] = useState<string | undefined>(undefined)
  const [selectedStockCode, setSelectedStockCode] = useState<string | undefined>(undefined)
  const [planFormStockName, setPlanFormStockName] = useState<string | undefined>(undefined)
  const [planFormStockCode, setPlanFormStockCode] = useState<string | undefined>(undefined)

  // 매매 종목 데이터 조회 (계획 모드용)
  const {
    data: stocks = [],
    isLoading: isLoadingStocks,
    error: stocksError,
    refetch: refetchStocks
  } = useQuery({
    queryKey: ['planModeStocks'],
    queryFn: fetchPlanModeStocks,
    refetchInterval: 60000, // 1분마다 갱신
    enabled: mode === 'plan', // 계획 모드일 때만 실행
  })

  // 실제 매매 내역 조회 (복기 모드용)
  const {
    data: tradesData,
    isLoading: isLoadingTrades,
    error: tradesError,
    refetch: refetchTrades
  } = useQuery({
    queryKey: ['recentTrades'],
    queryFn: fetchRecentTrades,
    refetchInterval: 300000, // 5분마다 갱신
  })

  const trades = tradesData || []
  const isLoading = mode === 'plan' ? isLoadingStocks : isLoadingTrades
  const error = mode === 'plan' ? stocksError : tradesError

  // 마운트 상태 설정
  useEffect(() => {
    setMounted(true)

    // 대시보드 마운트 시 Kiwoom API에서 거래 기록 동기화
    // 1초 지연 후 백그라운드에서 실행 (UI 렌더링 완료 후)
    const syncTimer = setTimeout(() => {
      tradingStocksAPI
        .syncFromKiwoom(30) // 최근 30일 거래 기록 조회
        .then(() => {
          console.log('✅ Kiwoom API 거래 기록 동기화 완료')
          // 동기화 완료 후 거래 종목 목록 새로고침
          refetchTrades()
        })
        .catch((error) => {
          console.warn('⚠️ Kiwoom API 동기화 실패:', error)
          // 동기화 실패해도 UI는 계속 진행
        })
    }, 1000)

    return () => clearTimeout(syncTimer)
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

  const handleRefresh = async () => {
    // 이미 새로고침 중이면 중복 클릭 방지
    if (isRefreshing) return

    setIsRefreshing(true)
    try {
      // 현재 모드에 따라 데이터 새로고침
      if (mode === 'plan') {
        await refetchStocks()
      } else {
        await refetchTrades()
      }
    } catch (error) {
      console.error('데이터 새로고침 실패:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  const handleAddStock = () => {
    // 계획 모드와 복기 모드에서 다른 모달 열기
    if (mode === 'plan') {
      setIsSearchModalOpen(true)
    } else {
      setIsSearchModalOpen(true) // 복기 모드용 모달은 별도로 처리
    }
  }

  const handleStockAdded = () => {
    // 종목이 추가되면 목록 새로고침
    if (mode === 'plan') {
      refetchStocks()
    } else {
      refetchTrades()
    }
  }

  const handleDeleteStock = async (planId: number) => {
    // 삭제 확인 대화상자
    if (!confirm('정말 이 종목을 삭제하시겠습니까?')) {
      return
    }

    try {
      await tradingPlansAPI.deleteTradingPlan(planId)
      // 삭제 후 목록 새로고침
      refetchStocks()
    } catch (error) {
      console.error('종목 삭제 실패:', error)
      alert('종목 삭제에 실패했습니다.')
    }
  }

  const handleStrategyManage = () => {
    // 추천 페이지로 이동
    window.location.href = '/recommendation'
  }

  const handleStockCardClick = (stock: any) => {
    if (mode === 'review') {
      // 복기 모드에서는 모달 열기
      // trading_id를 기반으로 거래 기록과 매핑
      setSelectedTradingPlanId(null)
      setSelectedTradingId(stock.id)
      setSelectedOrderNo(undefined)
      setSelectedStockName(stock.stock_name)
      setSelectedStockCode(stock.stock_code)
      setIsModalOpen(true)
    } else {
      // 계획 모드에서는 거래 계획 폼 모달 열기
      setPlanFormStockName(stock.stock_name)
      setPlanFormStockCode(stock.stock_code)
      setIsPlanFormModalOpen(true)
    }
  }


  // Create grid items without empty slots
  const createGridItems = (items: any[], mode: Mode) => {
    // 계획 모드에서 추가된 종목이 없으면 메시지 표시
    if (mode === 'plan' && items.length === 0) {
      return (
        <div className="col-span-full flex items-center justify-center py-16">
          <div className="text-center">
            <p className="text-gray-500 text-lg">추가된 종목이 없습니다.</p>
          </div>
        </div>
      )
    }

    return items.map((item) => (
      <div key={item.id}>
        {mode === 'plan' ? (
          <PlanStockCard
            stock={item}
            onClick={() => handleStockCardClick(item)}
            onDelete={handleDeleteStock}
          />
        ) : (
          <RecapStockCard
            stock={item}
            onClick={handleStockCardClick}
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
        isRefreshing={isRefreshing}
      />

      {/* Main Content */}
      <main className="mx-auto px-3 sm:px-4 md:px-6 lg:px-8 py-4 sm:py-6 md:py-8">
        {/* Mode Title */}
        <div className="mb-4 sm:mb-6 md:mb-8">
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-1 sm:mb-2">
            {mode === 'plan' ? '계획 모드' : '복기 모드'}
          </h2>
          <p className="text-sm sm:text-base text-gray-600">
            {mode === 'plan'
              ? '관심 종목을 모니터링하고 매매 계획을 세워보세요'
              : '완료된 매매 기록을 확인하고 복기해보세요'
            }
          </p>
        </div>

        {/* Grid Layout - 모바일 1열, 태블릿 2열, 데스크톱 3-4열 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
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

      {/* Stock Search Modal - Plan Mode Only */}
      {mode === 'plan' && (
        <StockSearchModal
          isOpen={isSearchModalOpen}
          onClose={() => setIsSearchModalOpen(false)}
          onStockAdded={handleStockAdded}
        />
      )}

      {/* Recap Stock Add Modal - Review Mode Only */}
      {mode === 'review' && (
        <RecapStockAddModal
          isOpen={isSearchModalOpen}
          onClose={() => setIsSearchModalOpen(false)}
          onStockAdded={handleStockAdded}
        />
      )}

      {/* Trading Plan Form Modal - Plan Mode Only */}
      {mode === 'plan' && (
        <TradingPlanFormModal
          isOpen={isPlanFormModalOpen}
          onClose={() => setIsPlanFormModalOpen(false)}
          stockCode={planFormStockCode}
          stockName={planFormStockName}
        />
      )}
    </div>
  )
}