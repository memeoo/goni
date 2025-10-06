import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tradingPlansAPI } from '@/lib/api'
import { TradingPlan, TradingPlanCreate, TradingPlanUpdate } from '@/types'
import toast from 'react-hot-toast'

export function useTradingPlans(skip = 0, limit = 100) {
  return useQuery({
    queryKey: ['trading-plans', skip, limit],
    queryFn: async () => {
      const response = await tradingPlansAPI.getTradingPlans(skip, limit)
      return response.data as TradingPlan[]
    },
    staleTime: 60 * 1000, // 1 minute
  })
}

export function useTradingPlan(planId: number) {
  return useQuery({
    queryKey: ['trading-plan', planId],
    queryFn: async () => {
      const response = await tradingPlansAPI.getTradingPlan(planId)
      return response.data as TradingPlan
    },
    enabled: !!planId,
  })
}

export function useCreateTradingPlan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (planData: TradingPlanCreate) =>
      tradingPlansAPI.createTradingPlan(planData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trading-plans'] })
      toast.success('매매 계획이 성공적으로 생성되었습니다')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '매매 계획 생성에 실패했습니다')
    },
  })
}

export function useUpdateTradingPlan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ planId, planData }: { planId: number; planData: TradingPlanUpdate }) =>
      tradingPlansAPI.updateTradingPlan(planId, planData),
    onSuccess: (_, { planId }) => {
      queryClient.invalidateQueries({ queryKey: ['trading-plans'] })
      queryClient.invalidateQueries({ queryKey: ['trading-plan', planId] })
      toast.success('매매 계획이 성공적으로 업데이트되었습니다')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '매매 계획 업데이트에 실패했습니다')
    },
  })
}

export function useDeleteTradingPlan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (planId: number) => tradingPlansAPI.deleteTradingPlan(planId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trading-plans'] })
      toast.success('매매 계획이 성공적으로 삭제되었습니다')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '매매 계획 삭제에 실패했습니다')
    },
  })
}