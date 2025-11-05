'use client'

import { useState, useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import Cookies from 'js-cookie'
import DailyChart from './daily-chart'

// 거래량을 1000 단위로 K로 표시
const formatVolume = (value: number): string => {
  if (value >= 1000000) {
    return (value / 1000000).toFixed(1) + 'M'
  } else if (value >= 1000) {
    return (value / 1000).toFixed(0) + 'K'
  }
  return value.toString()
}

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

interface Trade {
  date: string // YYYYMMDD
  price: number
  quantity: number
  trade_type: string // '매수' 또는 '매도'
  order_no: string
  datetime: string
}

interface RecapData {
  catalyst?: string
  market_condition?: string
  price_chart?: string
  volume?: string
  supply_demand?: string
  emotion?: string
  evaluation?: string
  evaluation_reason?: string
  etc?: string
}

interface RecapModalProps {
  isOpen: boolean
  onClose: () => void
  tradingPlanId: number | null
  tradingId?: number | null  // Trading 테이블의 ID
  orderNo?: string
  stockName?: string
  stockCode?: string
}

export default function RecapModal({
  isOpen,
  onClose,
  tradingPlanId,
  tradingId,
  orderNo,
  stockName,
  stockCode,
}: RecapModalProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<RecapData>({
    catalyst: '',
    market_condition: '',
    price_chart: '',
    volume: '',
    supply_demand: '',
    emotion: '',
    evaluation: '',
    evaluation_reason: '',
    etc: '',
  })
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)
  const [showFormInputs, setShowFormInputs] = useState(false)
  const priceChartRef = useRef<HTMLTextAreaElement>(null)
  const volumeRef = useRef<HTMLTextAreaElement>(null)
  const formContainerRef = useRef<HTMLDivElement>(null)

  // 기존 복기 데이터 조회는 폼이 표시될 때만 (B/S 마커 클릭 후)
  const { data: existingRecap } = useQuery({
    queryKey: ['recap', tradingId || orderNo || tradingPlanId],
    queryFn: async () => {
      const token = Cookies.get('access_token') || localStorage.getItem('access_token')

      // trading_id가 있으면 trading_id로 조회, order_no가 있으면 order_no로 조회, 없으면 trading_plan_id로 조회
      let url
      if (tradingId) {
        url = `/api/recap/by-trading/${tradingId}`
      } else if (orderNo) {
        url = `/api/recap/by-order/${orderNo}`
      } else if (tradingPlanId) {
        url = `/api/recap/${tradingPlanId}`
      } else {
        return null
      }

      const response = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (response.status === 404) {
        return null // 복기가 없으면 null 반환
      }
      if (!response.ok) throw new Error('복기 데이터 조회 실패')
      const data = await response.json()
      return data
    },
    // 폼이 표시될 때만 복기 데이터 조회 (B/S 마커 클릭 후)
    enabled: isOpen && showFormInputs && (!!tradingId || !!orderNo || !!tradingPlanId),
    retry: false, // 404도 재시도하지 않음
  })

  // 일봉 차트 데이터 조회
  const { data: chartData, isLoading: chartLoading, error: chartError } = useQuery({
    queryKey: ['dailyChart', stockCode],
    queryFn: async () => {
      if (!stockCode) return null

      try {
        const url = `/api/stocks/${stockCode}/daily-chart`
        console.log('[RecapModal] 차트 데이터 요청:', url)
        const response = await fetch(url)
        if (!response.ok) {
          console.warn(`[RecapModal] 차트 데이터 조회 실패: ${response.status}`)
          return null
        }
        const result = await response.json()
        console.log('[RecapModal] 차트 데이터 수신:', {
          stockCode,
          totalRecords: result.total_records,
          firstRecord: result.data?.[0],
        })
        return result.data || []
      } catch (error) {
        console.warn('[RecapModal] 차트 데이터 조회 중 오류:', error)
        return null
      }
    },
    enabled: isOpen && !!stockCode,
    retry: 1, // 1회만 재시도
  })

  // 매매 기록 조회 (Trading 테이블에서 - 해당 종목의 모든 거래 내역)
  const { data: tradesData } = useQuery({
    queryKey: ['stockTrades', stockCode],
    queryFn: async () => {
      if (!stockCode) return null

      try {
        const token = Cookies.get('access_token') || localStorage.getItem('access_token')
        const url = `/api/trading/${stockCode}/trades`
        const response = await fetch(url, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        if (!response.ok) {
          return null
        }
        const result = await response.json()
        return result.trades || []
      } catch (error) {
        return null
      }
    },
    enabled: isOpen && !!stockCode,
    retry: 1,
  })

  // 기존 데이터가 있으면 form에 채우기
  useEffect(() => {
    if (existingRecap) {
      setFormData({
        catalyst: existingRecap.catalyst || '',
        market_condition: existingRecap.market_condition || '',
        price_chart: existingRecap.price_chart || '',
        volume: existingRecap.volume || '',
        supply_demand: existingRecap.supply_demand || '',
        emotion: existingRecap.emotion || '',
        evaluation: existingRecap.evaluation || '',
        evaluation_reason: existingRecap.evaluation_reason || '',
        etc: existingRecap.etc || '',
      })
    } else {
      // 기존 복기가 없으면 폼 초기화
      setFormData({
        catalyst: '',
        market_condition: '',
        price_chart: '',
        volume: '',
        supply_demand: '',
        emotion: '',
        evaluation: '',
        evaluation_reason: '',
        etc: '',
      })
    }
  }, [existingRecap])

  // 모달이 닫힐 때 폼 초기화
  useEffect(() => {
    if (!isOpen) {
      setFormData({
        catalyst: '',
        market_condition: '',
        price_chart: '',
        volume: '',
        supply_demand: '',
        emotion: '',
        evaluation: '',
        evaluation_reason: '',
        etc: '',
      })
      setShowFormInputs(false)
      // 쿼리 캐시 무효화하여 다음에 열릴 때 새로 조회하도록 함
      queryClient.removeQueries({ queryKey: ['recap'] })
    }
  }, [isOpen, queryClient])

  // 복기 생성 mutation
  const createMutation = useMutation({
    mutationFn: async (data: RecapData) => {
      const token = Cookies.get('access_token') || localStorage.getItem('access_token')
      console.log('Token found:', !!token, token?.substring(0, 20) + '...')
      console.log('Trading ID:', tradingId)
      console.log('Trading Plan ID:', tradingPlanId)
      console.log('Order No:', orderNo)
      if (!token) {
        throw new Error('로그인이 필요합니다. 다시 로그인해주세요.')
      }
      const response = await fetch('/api/recap/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          trading_id: tradingId || null,
          trading_plan_id: tradingPlanId || null,
          order_no: orderNo || null,
          ...data,
        }),
        redirect: 'follow',
      })
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || '복기 생성 실패')
      }
      return response.json()
    },
    onSuccess: () => {
      toast.success('복기가 저장되었습니다')
      queryClient.invalidateQueries({ queryKey: ['recap', tradingId || tradingPlanId] })
      queryClient.invalidateQueries({ queryKey: ['recentTrades'] })
      onClose()
    },
    onError: (error: Error) => {
      console.error('복기 저장 에러:', error)
      toast.error(error.message || '복기 저장에 실패했습니다')
    },
  })

  // 복기 수정 mutation
  const updateMutation = useMutation({
    mutationFn: async (data: RecapData) => {
      const token = Cookies.get('access_token') || localStorage.getItem('access_token')

      // trading_id가 있으면 trading_id 기반으로, order_no가 있으면 order_no 기반으로, 없으면 trading_plan_id 기반으로 수정
      let url
      if (tradingId) {
        url = `/api/recap/by-trading/${tradingId}`
      } else if (orderNo) {
        url = `/api/recap/by-order/${orderNo}`
      } else if (tradingPlanId) {
        url = `/api/recap/${tradingPlanId}`
      } else {
        throw new Error('복기를 수정할 수 없습니다')
      }

      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(data),
      })
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || '복기 수정 실패')
      }
      return response.json()
    },
    onSuccess: () => {
      toast.success('복기가 수정되었습니다')
      queryClient.invalidateQueries({ queryKey: ['recap', orderNo || tradingPlanId] })
      queryClient.invalidateQueries({ queryKey: ['recentTrades'] })
      onClose()
    },
    onError: (error: Error) => {
      toast.error(error.message || '복기 수정에 실패했습니다')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (existingRecap) {
      updateMutation.mutate(formData)
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>
  ) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  // Buy/Sell 마커 클릭 처리
  const handleMarkerClick = (trade: Trade) => {
    const isLongTrade = trade.trade_type === '매수'

    // 폼 입력 레이아웃 표시
    setShowFormInputs(true)

    // Buy일 경우 "가격(차트)" 필드에 포커스, Sell일 경우 "거래량" 필드에 포커스
    if (isLongTrade) {
      // Buy: 가격(차트) 필드로 스크롤 및 포커스
      setTimeout(() => {
        priceChartRef.current?.focus()
        priceChartRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      }, 100)
    } else {
      // Sell: 거래량 필드로 스크롤 및 포커스
      setTimeout(() => {
        volumeRef.current?.focus()
        volumeRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      }, 100)
    }
  }

  // 호버된 봉의 정보를 포맷팅하는 함수
  const getHoveredCandleInfo = () => {
    if (hoveredIndex === null || !chartData || chartData.length === 0) {
      return null
    }

    // DailyChart와 동일하게 데이터 정렬
    // DailyChart: const recentData = data.slice(0, 50).reverse()
    // 즉, 최신 50개를 역순으로 정렬
    const recentData = chartData.slice(0, 50).reverse()

    if (hoveredIndex >= recentData.length) {
      return null
    }

    const candle = recentData[hoveredIndex]

    return {
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
      volume: candle.volume,
      changeRate: candle.change_rate ?? 0, // 백엔드에서 받은 change_rate 사용, 없으면 0
    }
  }

  const hoveredInfo = getHoveredCandleInfo()

  // 디버깅: 초기 데이터 로깅
  useEffect(() => {
    if (chartData && chartData.length > 0) {
      console.log('[RecapModal DEBUG] chartData loaded:', {
        length: chartData.length,
        stockCode,
        first3: chartData.slice(0, 3).map((d: ChartDataPoint) => ({
          date: d.date,
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
          volume: d.volume,
          change_rate: d.change_rate,
        })),
      })
    }
  }, [chartData])


  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-[80%] max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">
            {stockName || '매매 복기'}
          </h2>
          {/* 호버된 봉의 정보 표시 */}
          {hoveredInfo && (
            <div className="flex items-center gap-6 text-sm text-gray-700">
              <div className="flex gap-4">
                <div>
                  <span className="text-gray-500">시가:</span>{' '}
                  <span className="font-semibold">
                    {hoveredInfo.open.toLocaleString('ko-KR', {
                      maximumFractionDigits: 0,
                    })}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">고가:</span>{' '}
                  <span className="font-semibold">
                    {hoveredInfo.high.toLocaleString('ko-KR', {
                      maximumFractionDigits: 0,
                    })}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">저가:</span>{' '}
                  <span className="font-semibold">
                    {hoveredInfo.low.toLocaleString('ko-KR', {
                      maximumFractionDigits: 0,
                    })}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">종가:</span>{' '}
                  <span className="font-semibold">
                    {hoveredInfo.close.toLocaleString('ko-KR', {
                      maximumFractionDigits: 0,
                    })}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">변화율:</span>{' '}
                  <span
                    className={`font-semibold ${
                      hoveredInfo.changeRate > 0
                        ? 'text-red-600'
                        : hoveredInfo.changeRate < 0
                          ? 'text-blue-600'
                          : 'text-gray-700'
                    }`}
                  >
                    {hoveredInfo.changeRate > 0 ? '+' : ''}
                    {hoveredInfo.changeRate.toFixed(2)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">거래량:</span>{' '}
                  <span className="font-semibold">
                    {formatVolume(hoveredInfo.volume)}
                  </span>
                </div>
              </div>
            </div>
          )}
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-4">
          {/* 일봉 차트 */}
          {chartLoading ? (
            <div className="mb-4 text-center py-6 bg-gray-50 rounded-lg border border-gray-200">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600 text-sm">차트 로딩 중...</p>
            </div>
          ) : chartData && chartData.length > 0 ? (
            <div className="mb-6 border-b pb-4">
              <DailyChart
                stockCode={stockCode || ''}
                data={chartData}
                trades={tradesData}
                onHoveredIndexChange={setHoveredIndex}
                onMarkerClick={handleMarkerClick}
              />
            </div>
          ) : (
            <div className="mb-4 text-center py-6 bg-gray-50 rounded-lg border border-gray-200">
              <p className="text-gray-600 text-sm">차트 데이터를 불러올 수 없습니다</p>
            </div>
          )}

            {/* 폼 입력 섹션 - Buy/Sell 아이콘 클릭 후에만 표시 */}
            {showFormInputs && (
              <div ref={formContainerRef}>
                {/* Row 1: 재료 & 시황 */}
                <div className="grid grid-cols-2 gap-6 mb-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      재료
                    </label>
                    <textarea
                      name="catalyst"
                      value={formData.catalyst}
                      onChange={handleChange}
                      placeholder="종목 매매의 근거가 된 재료를 입력하세요 (예: 실적 발표, 신제품 출시, 정책 변화 등)"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      rows={2}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      시황
                    </label>
                    <textarea
                      name="market_condition"
                      value={formData.market_condition}
                      onChange={handleChange}
                      placeholder="당시 시장 전반의 상황을 입력하세요 (예: 코스피 상승세, 업종별 동향 등)"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      rows={2}
                    />
                  </div>
                </div>

                {/* Row 2: 가격(차트) & 거래량 */}
                <div className="grid grid-cols-2 gap-6 mb-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      가격(차트)
                    </label>
                    <textarea
                      ref={priceChartRef}
                      name="price_chart"
                      value={formData.price_chart}
                      onChange={handleChange}
                      placeholder="차트 패턴, 지지/저항선, 기술적 지표 등을 입력하세요"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      rows={3}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      거래량
                    </label>
                    <textarea
                      ref={volumeRef}
                      name="volume"
                      value={formData.volume}
                      onChange={handleChange}
                      placeholder="거래량 추이 및 특이사항을 입력하세요"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      rows={3}
                    />
                  </div>
                </div>

                {/* Row 3: 수급(외국인/기관) & 심리(매매 당시의 감정) */}
                <div className="grid grid-cols-2 gap-6 mb-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      수급(외국인/기관)
                    </label>
                    <textarea
                      name="supply_demand"
                      value={formData.supply_demand}
                      onChange={handleChange}
                      placeholder="외국인, 기관의 매수/매도 동향을 입력하세요"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      rows={3}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      심리(매매 당시의 감정)
                    </label>
                    <textarea
                      name="emotion"
                      value={formData.emotion}
                      onChange={handleChange}
                      placeholder="매매 결정 당시의 심리 상태, 감정을 솔직하게 입력하세요 (예: 두려움, 확신, 초조함 등)"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      rows={3}
                    />
                  </div>
                </div>

                {/* Row 4: 평가 (Full Width) */}
                <div className="mb-6">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    평가
                  </label>
                  <div className="flex gap-6 mb-3">
                    <label className="flex items-center cursor-pointer">
                      <input
                        type="radio"
                        name="evaluation"
                        value="good"
                        checked={formData.evaluation === 'good'}
                        onChange={handleChange}
                        className="w-4 h-4 text-blue-600 focus:ring-2 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-gray-700">Good</span>
                    </label>
                    <label className="flex items-center cursor-pointer">
                      <input
                        type="radio"
                        name="evaluation"
                        value="so-so"
                        checked={formData.evaluation === 'so-so'}
                        onChange={handleChange}
                        className="w-4 h-4 text-blue-600 focus:ring-2 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-gray-700">So-So</span>
                    </label>
                    <label className="flex items-center cursor-pointer">
                      <input
                        type="radio"
                        name="evaluation"
                        value="bad"
                        checked={formData.evaluation === 'bad'}
                        onChange={handleChange}
                        className="w-4 h-4 text-blue-600 focus:ring-2 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-gray-700">Bad</span>
                    </label>
                  </div>
                </div>

                {/* Row 5: 평가이유 & 기타 */}
                <div className="grid grid-cols-2 gap-6 mb-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      평가이유
                    </label>
                    <textarea
                      name="evaluation_reason"
                      value={formData.evaluation_reason}
                      onChange={handleChange}
                      placeholder="평가의 이유를 입력하세요"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      rows={3}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      기타(자유 기술)
                    </label>
                    <textarea
                      name="etc"
                      value={formData.etc}
                      onChange={handleChange}
                      placeholder="그 외 특이사항이나 배운 점을 자유롭게 입력하세요"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      rows={3}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Footer Buttons */}
            <div className="flex justify-end gap-4 pt-4 border-t">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                취소
              </button>
              <button
                type="submit"
                disabled={createMutation.isPending || updateMutation.isPending}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {createMutation.isPending || updateMutation.isPending
                  ? '저장 중...'
                  : existingRecap
                  ? '수정'
                  : '저장'}
              </button>
            </div>
          </form>
      </div>
    </div>
  )
}
