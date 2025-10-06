'use client'

import { useQuery } from '@tanstack/react-query'
import { stocksAPI } from '@/lib/api'

export interface ChartDataPoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  trade_amount: number
  volume_change?: number
}

export interface ChartDataResponse {
  stock_code: string
  days: number
  data: ChartDataPoint[]
  total_records: number
}

export function useChartData(stockCode: string, days: number = 60) {
  return useQuery({
    queryKey: ['chart-data', stockCode, days],
    queryFn: async (): Promise<ChartDataResponse> => {
      const response = await stocksAPI.getChartData(stockCode, days)
      return response.data
    },
    enabled: !!stockCode,
    staleTime: 0, // 캐시 비활성화 - 항상 새로운 데이터 요청
    refetchOnWindowFocus: true, // 창 포커스시 새로고침
    refetchOnMount: true, // 컴포넌트 마운트시 새로고침
    retry: 2,
    retryDelay: 1000,
  })
}

export function useOHLCData(stockCode: string, days: number = 60) {
  return useQuery({
    queryKey: ['ohlc-data', stockCode, days],
    queryFn: async () => {
      const response = await stocksAPI.getOHLCData(stockCode, days)
      return response.data
    },
    enabled: !!stockCode,
    staleTime: 0, // 캐시 비활성화
    refetchOnWindowFocus: true,
    refetchOnMount: true,
    retry: 2,
    retryDelay: 1000,
  })
}

export function useVolumeData(stockCode: string, days: number = 60) {
  return useQuery({
    queryKey: ['volume-data', stockCode, days],
    queryFn: async () => {
      const response = await stocksAPI.getVolumeData(stockCode, days)
      return response.data
    },
    enabled: !!stockCode,
    staleTime: 0, // 캐시 비활성화
    refetchOnWindowFocus: true,
    refetchOnMount: true,
    retry: 2,
    retryDelay: 1000,
  })
}