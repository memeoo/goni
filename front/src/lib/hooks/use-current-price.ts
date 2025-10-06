'use client'

import { useQuery } from '@tanstack/react-query'
import { stocksAPI } from '@/lib/api'

export interface CurrentPriceData {
  stock_code: string
  current_price: number
  change_price: number
  change_rate: number
  volume: number
  updated_at: string
}

export function useCurrentPrice(stockCode: string) {
  return useQuery({
    queryKey: ['current-price', stockCode],
    queryFn: async (): Promise<CurrentPriceData> => {
      const response = await stocksAPI.getCurrentPrice(stockCode)
      return response.data
    },
    enabled: !!stockCode,
    staleTime: 0, // 캐시 비활성화 - 항상 새로운 데이터 요청
    refetchOnWindowFocus: true, // 창 포커스시 새로고침
    refetchOnMount: true, // 컴포넌트 마운트시 새로고침
    refetchInterval: 60 * 1000, // 1분마다 자동 갱신
    retry: 2,
    retryDelay: 1000,
  })
}