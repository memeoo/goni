'use client'

import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { X, Loader2 } from 'lucide-react'
import Cookies from 'js-cookie'
import DailyChart from './daily-chart'

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
  id: number
  date: string // YYYYMMDD
  price: number
  quantity: number
  trade_type: string // '매수' 또는 '매도'
  order_no: string
  datetime: string
}

interface PlanModeChartModalProps {
  isOpen: boolean
  onClose: () => void
  stockCode?: string
  stockName?: string
}

export default function PlanModeChartModal({
  isOpen,
  onClose,
  stockCode,
  stockName,
}: PlanModeChartModalProps) {
  useEffect(() => {
    console.log('[PlanModeChartModal] 모달 상태 변경:', {
      isOpen,
      stockCode,
      stockName,
    })
  }, [isOpen, stockCode, stockName])

  // 일봉 차트 데이터 조회
  const { data: chartData, isLoading: chartLoading, error: chartError } = useQuery({
    queryKey: ['planModeChart', stockCode],
    queryFn: async () => {
      console.log('[PlanModeChartModal] queryFn 실행 시작:', stockCode)
      if (!stockCode) {
        console.log('[PlanModeChartModal] stockCode가 없음')
        return null
      }

      try {
        const url = `/api/stocks/${stockCode}/daily-chart`
        console.log('[PlanModeChartModal] 차트 데이터 요청:', url)
        const response = await fetch(url)
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          console.warn(`[PlanModeChartModal] 차트 데이터 조회 실패: ${response.status}`, errorData)
          throw new Error(errorData.detail || `차트 데이터 조회 실패 (${response.status})`)
        }
        const result = await response.json()
        console.log('[PlanModeChartModal] 차트 데이터 수신:', {
          stockCode,
          totalRecords: result.total_records,
          firstRecord: result.data?.[0],
        })
        return result.data || []
      } catch (error) {
        console.warn('[PlanModeChartModal] 차트 데이터 조회 중 오류:', error)
        throw error
      }
    },
    enabled: isOpen && !!stockCode,
    retry: 1,
  })

  // 매매 기록 조회
  const { data: tradesData, isLoading: tradesLoading } = useQuery({
    queryKey: ['planModeChartTrades', stockCode],
    queryFn: async () => {
      if (!stockCode) {
        console.log('[PlanModeChartModal] stockCode 없음 - 거래 기록 조회 스킵')
        return null
      }

      try {
        const token = Cookies.get('access_token') || localStorage.getItem('access_token')
        const url = `/api/trading/${stockCode}/trades`
        console.log('[PlanModeChartModal] 거래 기록 요청 시작:', { url, hasToken: !!token, stockCode })

        const response = await fetch(url, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })

        console.log('[PlanModeChartModal] 거래 기록 응답 상태:', response.status, response.statusText)

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          console.warn(`[PlanModeChartModal] 거래 기록 조회 실패: ${response.status}`, errorData)
          return []
        }

        const result = await response.json()
        console.log('[PlanModeChartModal] 거래 기록 수신 완료:', {
          stockCode,
          tradesCount: result.trades?.length || 0,
          totalRecords: result.total_records,
          firstTrade: result.trades?.[0],
        })
        return result.trades || []
      } catch (error) {
        console.error('[PlanModeChartModal] 거래 기록 조회 중 오류:', error)
        return []
      }
    },
    enabled: isOpen && !!stockCode,
    retry: 1,
  })

  useEffect(() => {
    console.log('[PlanModeChartModal] 쿼리 상태 변경:', {
      isLoading: chartLoading,
      error: chartError,
      dataLength: chartData?.length || 0,
    })
  }, [chartLoading, chartError, chartData])

  useEffect(() => {
    console.log('[PlanModeChartModal] 거래 데이터 상태 업데이트:', {
      stockCode,
      isLoading: tradesLoading,
      tradesDataLength: tradesData?.length || 0,
      tradesDataExists: !!tradesData,
      tradesData: tradesData,
    })
  }, [tradesData, stockCode, tradesLoading])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] flex flex-col shadow-xl">
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
        <div className="flex-1 overflow-y-auto p-6">
          {chartLoading && (
            <div className="flex items-center justify-center h-96">
              <div className="text-center">
                <Loader2 className="h-8 w-8 text-blue-500 animate-spin mx-auto mb-2" />
                <p className="text-gray-600">차트 데이터 로딩 중...</p>
              </div>
            </div>
          )}

          {chartError && (
            <div className="flex items-center justify-center h-96">
              <div className="text-center">
                <p className="text-red-600 mb-2">차트 데이터를 불러올 수 없습니다.</p>
                <p className="text-sm text-gray-600">
                  {chartError instanceof Error ? chartError.message : '잠시 후 다시 시도해주세요.'}
                </p>
              </div>
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

          {!chartLoading && !chartError && (!chartData || chartData.length === 0) && (
            <div className="flex items-center justify-center h-96">
              <div className="text-center">
                <p className="text-gray-600">차트 데이터가 없습니다.</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 transition-colors"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  )
}
