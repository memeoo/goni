import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { stocksAPI } from '@/lib/api'
import { Stock } from '@/types'
import toast from 'react-hot-toast'

export function useStocks(skip = 0, limit = 100) {
  return useQuery({
    queryKey: ['stocks', skip, limit],
    queryFn: async () => {
      const response = await stocksAPI.getStocks(skip, limit)
      return response.data as Stock[]
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  })
}

export function useStock(stockId: number) {
  return useQuery({
    queryKey: ['stock', stockId],
    queryFn: async () => {
      const response = await stocksAPI.getStock(stockId)
      return response.data as Stock
    },
    enabled: !!stockId,
    staleTime: 30 * 1000, // 30 seconds
  })
}

export function useCreateStock() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (stockData: any) => stocksAPI.createStock(stockData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stocks'] })
      toast.success('종목이 성공적으로 추가되었습니다')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '종목 추가에 실패했습니다')
    },
  })
}

export function useUpdateStock() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ stockId, stockData }: { stockId: number; stockData: any }) =>
      stocksAPI.updateStock(stockId, stockData),
    onSuccess: (_, { stockId }) => {
      queryClient.invalidateQueries({ queryKey: ['stocks'] })
      queryClient.invalidateQueries({ queryKey: ['stock', stockId] })
      toast.success('종목 정보가 성공적으로 업데이트되었습니다')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '종목 업데이트에 실패했습니다')
    },
  })
}