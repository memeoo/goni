'use client'

import { useState, useEffect } from 'react'
import { X, Trash2 } from 'lucide-react'
import DailyChart from './daily-chart'
import { useQuery } from '@tanstack/react-query'
import Cookies from 'js-cookie'
import { tradingStocksAPI, tradingPlansAPI } from '@/lib/api'

interface ChartDataPoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  trade_amount: number
  change_rate?: number | null
  ma5?: number | null
  ma10?: number | null
  ma20?: number | null
  ma60?: number | null
}

interface TradingPlan {
  id?: number
  stock_code: string
  stock_name: string
  trading_type: string
  condition: string
  target_price: number | null
  amount?: number | null
  reason: string
  sp_condition?: string
  sp_price?: number | null
  sp_ratio?: number | null
  sl_condition?: string
  sl_price?: number | null
  sl_ratio?: number | null
  proportion?: number | null
  created_at?: string
}

interface TradingPlanFormModalProps {
  isOpen: boolean
  onClose: () => void
  stockCode?: string
  stockName?: string
  planId?: number
}

export default function TradingPlanFormModal({
  isOpen,
  onClose,
  stockCode,
  stockName,
  planId,
}: TradingPlanFormModalProps) {
  const [tradeType, setTradeType] = useState<'buy' | 'sell'>('buy')

  // 매수 계획
  const [buyPrice, setBuyPrice] = useState('')
  const [buyQuantity, setBuyQuantity] = useState('')
  const [buyAmount, setBuyAmount] = useState('')
  const [buyCondition, setBuyCondition] = useState('')
  const [buyReason, setBuyReason] = useState('')
  const [profitTarget, setProfitTarget] = useState('')
  const [profitCondition, setProfitCondition] = useState('')
  const [profitRate, setProfitRate] = useState('')
  const [lossTarget, setLossTarget] = useState('')
  const [lossCondition, setLossCondition] = useState('')
  const [lossRate, setLossRate] = useState('')

  // 매도 계획
  const [sellPrice, setSellPrice] = useState('')
  const [sellRatio, setSellRatio] = useState('')
  const [sellQuantity, setSellQuantity] = useState('')
  const [sellCondition, setSellCondition] = useState('')
  const [sellReason, setSellReason] = useState('')

  // 보유 수량 (사용자가 직접 입력)
  const [holdingQuantity, setHoldingQuantity] = useState(0)

  // 이 종목의 계획 목록
  const [plansList, setPlansList] = useState<TradingPlan[]>([])
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null)

  // 모달이 열리거나 종목이 변경될 때 입력 필드 초기화
  useEffect(() => {
    if (isOpen && stockCode) {
      clearForm()
    }
  }, [isOpen, stockCode])

  // 이 종목의 계획 목록 조회
  const { data: plansData, refetch: refetchPlans } = useQuery({
    queryKey: ['tradingPlans', stockCode],
    queryFn: async () => {
      if (!stockCode) return []

      try {
        const token = Cookies.get('access_token') || localStorage.getItem('access_token')
        const url = `/api/trading-plans/by-stock/${stockCode}`
        console.log('[TradingPlanFormModal] 계획 목록 조회 시작:', url)
        const response = await fetch(url, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        if (!response.ok) {
          console.warn('[TradingPlanFormModal] 계획 목록 조회 실패:', response.status)
          return []
        }
        const result = await response.json()
        console.log('[TradingPlanFormModal] 계획 목록 조회 완료:', result)
        return result.plans || []
      } catch (error) {
        console.warn('[TradingPlanFormModal] 계획 목록 조회 중 오류:', error)
        return []
      }
    },
    enabled: isOpen && !!stockCode,
    retry: 1,
  })

  // 계획 목록 업데이트
  useEffect(() => {
    if (plansData) {
      setPlansList(plansData)
    }
  }, [plansData])

  // 일봉 차트 데이터 조회
  const { data: chartData, isLoading: chartLoading, error: chartError } = useQuery({
    queryKey: ['tradingPlanChart', stockCode],
    queryFn: async () => {
      if (!stockCode) return null

      try {
        const url = `/api/stocks/${stockCode}/daily-chart`
        const response = await fetch(url)
        if (!response.ok) {
          throw new Error(`차트 데이터 조회 실패 (${response.status})`)
        }
        const result = await response.json()
        return result.data || []
      } catch (error) {
        console.warn('차트 데이터 조회 중 오류:', error)
        throw error
      }
    },
    enabled: isOpen && !!stockCode,
    retry: 1,
  })

  // 매매 기록 조회
  const { data: tradesData } = useQuery({
    queryKey: ['tradingPlanChartTrades', stockCode],
    queryFn: async () => {
      if (!stockCode) return null

      try {
        const token = Cookies.get('access_token') || localStorage.getItem('access_token')
        const url = `/api/trading/${stockCode}/trades`
        const response = await fetch(url, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        if (!response.ok) return null
        const result = await response.json()
        return result.trades || []
      } catch (error) {
        console.warn('거래 기록 조회 중 오류:', error)
        return null
      }
    },
    enabled: isOpen && !!stockCode,
    retry: 1,
  })

  // 입력 필드 초기화
  const clearForm = () => {
    setBuyPrice('')
    setBuyQuantity('')
    setBuyAmount('')
    setBuyCondition('')
    setBuyReason('')
    setProfitTarget('')
    setProfitCondition('')
    setProfitRate('')
    setLossTarget('')
    setLossCondition('')
    setLossRate('')

    setSellPrice('')
    setSellRatio('')
    setSellQuantity('')
    setSellCondition('')
    setSellReason('')

    setTradeType('buy')
    setSelectedPlanId(null)
    setHoldingQuantity(0)
  }

  // 계획 리스트의 항목 클릭 시 폼에 데이터 로드
  const handleSelectPlan = (plan: TradingPlan) => {
    setSelectedPlanId(plan.id || null)

    if (plan.trading_type === 'buy') {
      setTradeType('buy')
      setBuyPrice(plan.target_price?.toString() || '')
      setBuyCondition(plan.condition || '')
      setBuyReason(plan.reason || '')
      setProfitCondition(plan.sp_condition || '')
      setProfitTarget(plan.sp_price?.toString() || '')
      setProfitRate(plan.sp_ratio?.toString() || '')
      setLossCondition(plan.sl_condition || '')
      setLossTarget(plan.sl_price?.toString() || '')
      setLossRate(plan.sl_ratio?.toString() || '')

      // 가격과 수량에서 금액 계산
      if (plan.target_price && plan.amount) {
        const quantity = Math.floor(plan.amount / plan.target_price)
        setBuyQuantity(quantity.toString())
        setBuyAmount(plan.amount.toString())
      }
    } else {
      setTradeType('sell')
      setSellPrice(plan.target_price?.toString() || '')
      setSellCondition(plan.condition || '')
      setSellReason(plan.reason || '')
      setSellRatio(plan.proportion?.toString() || '')
    }
  }

  // 매수 가격 변경
  const handleBuyPriceChange = (value: string) => {
    setBuyPrice(value)
    if (value && buyQuantity) {
      const total = (parseFloat(value) || 0) * (parseFloat(buyQuantity) || 0)
      setBuyAmount(total.toString())
    }
  }

  // 매수 수량 변경
  const handleBuyQuantityChange = (value: string) => {
    setBuyQuantity(value)
    if (buyPrice && value) {
      const total = (parseFloat(buyPrice) || 0) * (parseFloat(value) || 0)
      setBuyAmount(total.toString())
    }
  }

  // 매수 금액 변경
  const handleBuyAmountChange = (value: string) => {
    setBuyAmount(value)
    if (buyPrice && value) {
      const qty = (parseFloat(value) || 0) / (parseFloat(buyPrice) || 1)
      setBuyQuantity(Math.floor(qty).toString())
    }
  }

  // 익절 가격 변경
  const handleProfitTargetChange = (value: string) => {
    setProfitTarget(value)
    if (value && buyPrice) {
      const rate = ((parseFloat(value) - parseFloat(buyPrice)) / parseFloat(buyPrice)) * 100
      setProfitRate(rate.toFixed(2))
    }
  }

  // 익절 수익률 변경
  const handleProfitRateChange = (value: string) => {
    setProfitRate(value)
    if (value && buyPrice) {
      const target = parseFloat(buyPrice) * (1 + parseFloat(value) / 100)
      setProfitTarget(target.toFixed(0))
    }
  }

  // 손절 가격 변경
  const handleLossTargetChange = (value: string) => {
    setLossTarget(value)
    if (value && buyPrice) {
      const rate = ((parseFloat(value) - parseFloat(buyPrice)) / parseFloat(buyPrice)) * 100
      setLossRate(rate.toFixed(2))
    }
  }

  // 손절 수익률 변경
  const handleLossRateChange = (value: string) => {
    setLossRate(value)
    if (value && buyPrice) {
      const target = parseFloat(buyPrice) * (1 + parseFloat(value) / 100)
      setLossTarget(target.toFixed(0))
    }
  }

  // 매도 비중 변경
  const handleSellRatioChange = (value: string) => {
    setSellRatio(value)
    if (value && holdingQuantity) {
      const qty = Math.floor((holdingQuantity * parseFloat(value)) / 100)
      setSellQuantity(qty.toString())
    }
  }

  // 매도 수량 변경
  const handleSellQuantityChange = (value: string) => {
    setSellQuantity(value)
    if (value && holdingQuantity) {
      const ratio = ((parseFloat(value) / holdingQuantity) * 100).toFixed(0)
      setSellRatio(ratio)
    }
  }

  const handleSave = async () => {
    try {
      // 입력값 검증
      if (!stockCode) {
        alert('종목코드가 없습니다.')
        return
      }

      if (!tradeType) {
        alert('거래 종류를 선택해주세요.')
        return
      }

      // 거래 종류에 따라 필수값 검증
      if (tradeType === 'buy') {
        if (!buyPrice) {
          alert('매수 가격을 입력해주세요.')
          return
        }
      } else {
        if (!sellPrice) {
          alert('매도 가격을 입력해주세요.')
          return
        }
      }

      // 저장할 데이터 구성
      const tradingPlanData = {
        stock_code: stockCode,
        stock_name: stockName,
        trading_type: tradeType,
        ...(tradeType === 'buy'
          ? {
              condition: buyCondition,
              target_price: buyPrice ? parseFloat(buyPrice) : null,
              amount: buyAmount ? parseInt(buyAmount) : null,
              reason: buyReason,
              sp_condition: profitCondition,
              sp_price: profitTarget ? parseFloat(profitTarget) : null,
              sp_ratio: profitRate ? parseFloat(profitRate) : null,
              sl_condition: lossCondition,
              sl_price: lossTarget ? parseFloat(lossTarget) : null,
              sl_ratio: lossRate ? parseFloat(lossRate) : null,
            }
          : {
              condition: sellCondition,
              target_price: sellPrice ? parseFloat(sellPrice) : null,
              reason: sellReason,
              proportion: sellRatio ? parseFloat(sellRatio) : null,
            }),
      }

      console.log('Saving trading plan:', tradingPlanData)

      // 백엔드에 저장
      const response = await tradingPlansAPI.saveTradingPlan(tradingPlanData)

      if (response.status === 200 || response.status === 201) {
        alert('매매 계획이 저장되었습니다.')
        console.log('✅ 매매 계획 저장 완료:', response.data)
        clearForm()
        refetchPlans()
      } else {
        alert('매매 계획 저장 중 오류가 발생했습니다.')
      }
    } catch (error: any) {
      console.error('❌ 매매 계획 저장 오류:', error)
      const errorMessage =
        error.response?.data?.detail || error.message || '매매 계획 저장 중 오류가 발생했습니다.'
      alert(errorMessage)
    }
  }

  // 계획 삭제
  const handleDeletePlan = async (planId: number | undefined) => {
    if (!planId) return

    if (!confirm('이 계획을 삭제하시겠습니까?')) return

    try {
      const token = Cookies.get('access_token') || localStorage.getItem('access_token')
      const url = `/api/trading-plans/${planId}`
      const response = await fetch(url, {
        method: 'DELETE',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })

      if (response.ok) {
        alert('계획이 삭제되었습니다.')
        refetchPlans()
        clearForm()
      } else {
        alert('계획 삭제에 실패했습니다.')
      }
    } catch (error) {
      console.error('❌ 계획 삭제 오류:', error)
      alert('계획 삭제 중 오류가 발생했습니다.')
    }
  }

  // 텍스트 말줄임표 처리
  const truncateText = (text: string, maxLength: number = 20) => {
    if (!text) return '-'
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-2 sm:p-4">
      <div className="bg-white rounded-lg w-full h-[95vh] sm:h-auto sm:max-w-7xl sm:max-h-[90vh] flex flex-col shadow-xl">
        {/* Header */}
        <div className="flex justify-between items-center p-3 sm:p-6 border-b">
          <div>
            <h2 className="text-lg sm:text-xl font-bold text-gray-900">{stockName}</h2>
            <p className="text-xs sm:text-sm text-gray-500">{stockCode}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {/* 모바일: 세로 배열, 데스크톱: 3열 그리드 */}
          <div className="flex flex-col lg:grid lg:grid-cols-3 gap-3 sm:gap-4 md:gap-6 p-3 sm:p-6">
            {/* Left: Chart - 모바일: 전체, 데스크톱: 2 columns */}
            <div className="lg:col-span-2 space-y-4 sm:space-y-6">
              {/* Chart */}
              <div>
                {chartLoading && (
                  <div className="flex items-center justify-center h-96">
                    <p className="text-gray-600">차트 데이터 로딩 중...</p>
                  </div>
                )}
                {chartError && (
                  <div className="flex items-center justify-center h-96">
                    <p className="text-red-600">차트 데이터를 불러올 수 없습니다.</p>
                  </div>
                )}
                {!chartLoading && !chartError && chartData && chartData.length > 0 && (
                  <DailyChart
                    stockCode={stockCode || ''}
                    data={chartData}
                    trades={tradesData}
                    avgPrice={null}
                  />
                )}
              </div>

              {/* Plans List */}
              <div className="border rounded-lg p-4 bg-gray-50">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">계획 목록</h3>
                {plansList.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-4">
                    작성된 계획이 없습니다.
                  </p>
                ) : (
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {plansList.map((plan) => (
                      <div
                        key={plan.id}
                        onClick={() => handleSelectPlan(plan)}
                        className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer border transition-colors ${
                          selectedPlanId === plan.id
                            ? 'bg-blue-100 border-blue-500'
                            : 'bg-white border-gray-200 hover:bg-gray-100'
                        }`}
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span
                              className={`px-2 py-1 rounded text-xs font-medium text-white ${
                                plan.trading_type === 'buy'
                                  ? 'bg-blue-500'
                                  : 'bg-red-500'
                              }`}
                            >
                              {plan.trading_type === 'buy' ? '매수' : '매도'}
                            </span>
                            <span className="text-sm font-medium text-gray-900">
                              {plan.target_price?.toLocaleString()}원
                            </span>
                            {plan.trading_type === 'buy' && plan.amount && (
                              <span className="text-sm text-gray-600">
                                {Math.floor(plan.amount / plan.target_price!).toLocaleString()}주
                              </span>
                            )}
                            {plan.trading_type === 'sell' && plan.proportion && (
                              <span className="text-sm text-gray-600">
                                {plan.proportion}%
                              </span>
                            )}
                            <span className="text-sm text-gray-500">
                              {truncateText(plan.condition, 15)}
                            </span>
                            <span className="text-sm text-gray-500">
                              {truncateText(plan.reason, 15)}
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDeletePlan(plan.id)
                          }}
                          className="text-gray-400 hover:text-red-600 transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Right: Form - 모바일: 전체, 데스크톱: 1 column */}
            <div className="space-y-3 sm:space-y-4">
              {/* Clear Button */}
              <button
                onClick={clearForm}
                className="w-full py-2 px-4 rounded-lg bg-gray-300 text-gray-700 hover:bg-gray-400 transition-colors font-medium text-xs sm:text-sm"
              >
                Clear
              </button>

              {/* Trade Type Selection */}
              <div>
                <label className="block text-xs sm:text-sm font-semibold text-gray-700 mb-2">거래 종류</label>
                <div className="flex gap-2 sm:gap-4">
                  <button
                    onClick={() => setTradeType('buy')}
                    className={`flex-1 py-2 px-3 sm:px-4 rounded-lg font-medium transition-colors text-sm sm:text-base ${
                      tradeType === 'buy'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    매수
                  </button>
                  <button
                    onClick={() => setTradeType('sell')}
                    className={`flex-1 py-2 px-3 sm:px-4 rounded-lg font-medium transition-colors text-sm sm:text-base ${
                      tradeType === 'sell'
                        ? 'bg-red-500 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    매도
                  </button>
                </div>
              </div>

              {tradeType === 'buy' ? (
                // 매수 계획 폼
                <div className="space-y-4 border-t pt-6">
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        매수 가격 (원)
                      </label>
                      <input
                        type="number"
                        value={buyPrice}
                        onChange={(e) => handleBuyPriceChange(e.target.value)}
                        placeholder="0"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        수량 (주)
                      </label>
                      <input
                        type="number"
                        value={buyQuantity}
                        onChange={(e) => handleBuyQuantityChange(e.target.value)}
                        placeholder="0"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        금액 (원)
                      </label>
                      <input
                        type="number"
                        value={buyAmount}
                        onChange={(e) => handleBuyAmountChange(e.target.value)}
                        placeholder="0"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      매수 조건
                    </label>
                    <input
                      type="text"
                      value={buyCondition}
                      onChange={(e) => setBuyCondition(e.target.value)}
                      placeholder="예: 20일 이동평균선 지지 시"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      매수 이유
                    </label>
                    <textarea
                      value={buyReason}
                      onChange={(e) => setBuyReason(e.target.value)}
                      placeholder="매수 이유를 입력해주세요"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      rows={3}
                    />
                  </div>

                  {/* 익절 계획 */}
                  <div className="border-t pt-4 mt-4">
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">익절 계획</h3>
                    <div className="space-y-2">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          조건
                        </label>
                        <input
                          type="text"
                          value={profitCondition}
                          onChange={(e) => setProfitCondition(e.target.value)}
                          placeholder="예: 3% 수익"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            익절가 (원)
                          </label>
                          <input
                            type="number"
                            value={profitTarget}
                            onChange={(e) => handleProfitTargetChange(e.target.value)}
                            placeholder="0"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            수익률 (%)
                          </label>
                          <input
                            type="number"
                            value={profitRate}
                            onChange={(e) => handleProfitRateChange(e.target.value)}
                            placeholder="0"
                            step="0.01"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 손절 계획 */}
                  <div className="border-t pt-4 mt-4">
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">손절 계획</h3>
                    <div className="space-y-2">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          조건
                        </label>
                        <input
                          type="text"
                          value={lossCondition}
                          onChange={(e) => setLossCondition(e.target.value)}
                          placeholder="예: -2% 손실"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            손절가 (원)
                          </label>
                          <input
                            type="number"
                            value={lossTarget}
                            onChange={(e) => handleLossTargetChange(e.target.value)}
                            placeholder="0"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            손절률 (%)
                          </label>
                          <input
                            type="number"
                            value={lossRate}
                            onChange={(e) => handleLossRateChange(e.target.value)}
                            placeholder="0"
                            step="0.01"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                // 매도 계획 폼
                <div className="space-y-4 border-t pt-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      보유 수량 (주)
                    </label>
                    <input
                      type="number"
                      value={holdingQuantity}
                      onChange={(e) => setHoldingQuantity(parseInt(e.target.value) || 0)}
                      placeholder="0"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">매도 비중/수량 계산에 사용됩니다</p>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        매도 가격 (원)
                      </label>
                      <input
                        type="number"
                        value={sellPrice}
                        onChange={(e) => setSellPrice(e.target.value)}
                        placeholder="0"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        비중 (%)
                      </label>
                      <input
                        type="number"
                        value={sellRatio}
                        onChange={(e) => handleSellRatioChange(e.target.value)}
                        placeholder="0"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        수량 (주)
                      </label>
                      <input
                        type="number"
                        value={sellQuantity}
                        onChange={(e) => handleSellQuantityChange(e.target.value)}
                        placeholder="0"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      매도 조건
                    </label>
                    <input
                      type="text"
                      value={sellCondition}
                      onChange={(e) => setSellCondition(e.target.value)}
                      placeholder="예: 저항선 도달 시"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      매도 이유
                    </label>
                    <textarea
                      value={sellReason}
                      onChange={(e) => setSellReason(e.target.value)}
                      placeholder="매도 이유를 입력해주세요"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 resize-none"
                      rows={3}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 sm:p-6 border-t bg-gray-50 flex justify-end gap-2 sm:gap-3">
          <button
            onClick={onClose}
            className="px-3 sm:px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 transition-colors text-sm sm:text-base"
          >
            취소
          </button>
          <button
            onClick={handleSave}
            className="px-3 sm:px-4 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors text-sm sm:text-base"
          >
            저장
          </button>
        </div>
      </div>
    </div>
  )
}
