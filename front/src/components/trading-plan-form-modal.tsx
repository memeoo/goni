'use client'

import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import DailyChart from './daily-chart'
import { useQuery } from '@tanstack/react-query'
import Cookies from 'js-cookie'
import { tradingStocksAPI } from '@/lib/api'

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

  // 보유 수량 (백엔드에서 가져와야 함)
  const [holdingQuantity, setHoldingQuantity] = useState(0)
  const [isHolding, setIsHolding] = useState(false)

  // 보유 종목 조회
  const { data: ownedStocks } = useQuery({
    queryKey: ['ownedStocks'],
    queryFn: async () => {
      try {
        const response = await tradingStocksAPI.getOwnedStocks(0, 100)
        return response.data?.data || []
      } catch (error) {
        console.warn('보유 종목 조회 중 오류:', error)
        return []
      }
    },
    enabled: isOpen,
    retry: 1,
  })

  // 보유 종목 여부 확인
  useEffect(() => {
    if (ownedStocks && stockCode) {
      const ownedStock = ownedStocks.find(
        (stock: any) => stock.stock_code === stockCode
      )
      setIsHolding(!!ownedStock)
      setHoldingQuantity(ownedStock?.quantity || 0)
    }
  }, [ownedStocks, stockCode])

  // 모달이 열리거나 종목이 변경될 때 입력 필드 초기화
  useEffect(() => {
    if (isOpen && stockCode) {
      // 매수 계획 초기화
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

      // 매도 계획 초기화
      setSellPrice('')
      setSellRatio('')
      setSellQuantity('')
      setSellCondition('')
      setSellReason('')

      // 거래 종류를 매수로 리셋
      setTradeType('buy')
    }
  }, [isOpen, stockCode])

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

  const handleSave = () => {
    // TODO: 백엔드에 저장
    console.log('Save trading plan:', {
      tradeType,
      buyPrice,
      buyQuantity,
      buyAmount,
      buyCondition,
      buyReason,
      profitTarget,
      profitCondition,
      profitRate,
      lossTarget,
      lossCondition,
      lossRate,
      sellPrice,
      sellRatio,
      sellQuantity,
      sellCondition,
      sellReason,
    })
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg w-full max-w-7xl max-h-[90vh] flex flex-col shadow-xl">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{stockName}</h2>
            <p className="text-sm text-gray-500">{stockCode}</p>
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
          <div className="grid grid-cols-3 gap-6 p-6">
            {/* Left: Chart - 2 columns */}
            <div className="col-span-2">
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

            {/* Right: Form */}
            <div className="space-y-6">
              {/* Trade Type Selection */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">거래 종류</label>
                <div className="flex gap-4">
                  <button
                    onClick={() => setTradeType('buy')}
                    className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                      tradeType === 'buy'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    매수
                  </button>
                  {isHolding && (
                    <button
                      onClick={() => setTradeType('sell')}
                      className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                        tradeType === 'sell'
                          ? 'bg-red-500 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      매도
                    </button>
                  )}
                  {!isHolding && (
                    <div className="flex-1 py-2 px-4 rounded-lg font-medium bg-gray-100 text-gray-400 flex items-center justify-center">
                      매도 (미보유)
                    </div>
                  )}
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
        <div className="p-6 border-t bg-gray-50 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 transition-colors"
          >
            취소
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors"
          >
            저장
          </button>
        </div>
      </div>
    </div>
  )
}
