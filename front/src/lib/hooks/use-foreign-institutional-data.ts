'use client'

import { useQuery } from '@tanstack/react-query'
import { stocksAPI } from '@/lib/api'

export interface ForeignInstitutionalData {
  stock_code: string
  stock_name: string
  date: string
  institutional_net: number  // 기관 순매매량 (주)
  foreign_net: number       // 외국인 순매매량 (주)
  individual_net: number    // 개인 순매매량 (주)
}

export function useForeignInstitutionalData(stockCode: string) {
  return useQuery({
    queryKey: ['foreign-institutional-data', stockCode],
    queryFn: async (): Promise<ForeignInstitutionalData> => {
      const response = await stocksAPI.getForeignInstitutionalData(stockCode)
      return response.data
    },
    enabled: !!stockCode,
    staleTime: 0, // 캐시 비활성화 - 항상 새로운 데이터 요청
    refetchOnWindowFocus: true, // 창 포커스시 새로고침
    refetchOnMount: true, // 컴포넌트 마운트시 새로고침
    retry: 1, // 재시도 횟수를 줄임
    retryDelay: 2000,
  })
}