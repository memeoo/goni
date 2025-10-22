'use client'

import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import Cookies from 'js-cookie'

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
  orderNo?: string
  stockName?: string
}

export default function RecapModal({
  isOpen,
  onClose,
  tradingPlanId,
  orderNo,
  stockName,
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

  // 기존 복기 데이터 조회
  const { data: existingRecap, isLoading } = useQuery({
    queryKey: ['recap', orderNo || tradingPlanId],
    queryFn: async () => {
      const token = Cookies.get('access_token') || localStorage.getItem('access_token')

      // order_no가 있으면 order_no로 조회, 없으면 trading_plan_id로 조회
      let url
      if (orderNo) {
        url = `/api/recap/by-order/${orderNo}`
      } else if (tradingPlanId) {
        url = `/api/recap/${tradingPlanId}`
      } else {
        return null
      }

      const response = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (response.status === 404) return null
      if (!response.ok) throw new Error('복기 데이터 조회 실패')
      return response.json()
    },
    enabled: isOpen && (!!orderNo || !!tradingPlanId),
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
    } else if (!isLoading) {
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
  }, [existingRecap, isLoading])

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
      // 쿼리 캐시 무효화하여 다음에 열릴 때 새로 조회하도록 함
      queryClient.removeQueries({ queryKey: ['recap'] })
    }
  }, [isOpen, queryClient])

  // 복기 생성 mutation
  const createMutation = useMutation({
    mutationFn: async (data: RecapData) => {
      const token = Cookies.get('access_token') || localStorage.getItem('access_token')
      console.log('Token found:', !!token, token?.substring(0, 20) + '...')
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
      queryClient.invalidateQueries({ queryKey: ['recap', tradingPlanId] })
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

      // order_no가 있으면 order_no 기반으로 수정, 없으면 trading_plan_id 기반으로 수정
      let url
      if (orderNo) {
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

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto m-4">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">
            {stockName ? `${stockName} - 매매 복기` : '매매 복기'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="p-6 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">로딩 중...</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* 재료 */}
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

            {/* 시황 */}
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

            {/* 가격(차트) */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                가격(차트)
              </label>
              <textarea
                name="price_chart"
                value={formData.price_chart}
                onChange={handleChange}
                placeholder="차트 패턴, 지지/저항선, 기술적 지표 등을 입력하세요"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={3}
              />
            </div>

            {/* 거래량 */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                거래량
              </label>
              <textarea
                name="volume"
                value={formData.volume}
                onChange={handleChange}
                placeholder="거래량 추이 및 특이사항을 입력하세요"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={2}
              />
            </div>

            {/* 수급(외국인/기관) */}
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
                rows={2}
              />
            </div>

            {/* 심리(매매 당시의 감정) */}
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
                rows={2}
              />
            </div>

            {/* 평가 */}
            <div>
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
              <textarea
                name="evaluation_reason"
                value={formData.evaluation_reason}
                onChange={handleChange}
                placeholder="평가의 이유를 입력하세요"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={2}
              />
            </div>

            {/* 기타 */}
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
                rows={4}
              />
            </div>

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
        )}
      </div>
    </div>
  )
}
