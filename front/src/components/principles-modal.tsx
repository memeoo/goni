'use client'

import { useState, useEffect } from 'react'
import { X, Trash2 } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { principlesAPI } from '@/lib/api'

interface PrinciplesModalProps {
  isOpen: boolean
  onClose: () => void
}

interface Principle {
  id: number
  user_id: number
  principle_text: string
  created_at: string
  updated_at: string
}

export default function PrinciplesModal({ isOpen, onClose }: PrinciplesModalProps) {
  const [inputValue, setInputValue] = useState('')
  const [localPrinciples, setLocalPrinciples] = useState<Principle[]>([])
  const queryClient = useQueryClient()

  // Fetch existing principles
  const { data: principlesData, isLoading } = useQuery({
    queryKey: ['principles'],
    queryFn: () => principlesAPI.getPrinciples(),
    enabled: isOpen,
    staleTime: 0
  })

  // Update local list when data is fetched
  useEffect(() => {
    // axios로 받은 응답이므로 data.data로 접근해야 함
    if (principlesData?.data?.data) {
      setLocalPrinciples(principlesData.data.data)
    }
  }, [principlesData])

  // Create principle mutation
  const createMutation = useMutation({
    mutationFn: (principleText: string) =>
      principlesAPI.createPrinciple(principleText),
    onSuccess: (response) => {
      // axios 응답이므로 response.data.data로 접근
      const newPrinciple = response?.data?.data
      if (newPrinciple) {
        setLocalPrinciples([newPrinciple, ...localPrinciples])
        setInputValue('')
      }
    }
  })

  // Delete principle mutation
  const deleteMutation = useMutation({
    mutationFn: (principleId: number) =>
      principlesAPI.deletePrinciple(principleId),
    onSuccess: (_, principleId) => {
      setLocalPrinciples(
        localPrinciples.filter(p => p.id !== principleId)
      )
    }
  })

  const handleAddPrinciple = () => {
    if (inputValue.trim()) {
      createMutation.mutate(inputValue.trim())
    }
  }

  const handleDeletePrinciple = (principleId: number) => {
    deleteMutation.mutate(principleId)
  }

  const handleConfirm = () => {
    queryClient.invalidateQueries({ queryKey: ['principles'] })
    onClose()
  }

  const handleCancel = () => {
    setInputValue('')
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-2 sm:p-4">
      <div className="bg-white rounded-lg w-full h-[95vh] sm:h-auto sm:max-w-2xl sm:max-h-[80vh] flex flex-col shadow-xl">
        {/* Header */}
        <div className="flex justify-between items-center p-3 sm:p-6 border-b">
          <h2 className="text-lg sm:text-xl font-bold text-gray-900">매매원칙</h2>
          <button
            onClick={handleCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-3 sm:p-6">
          {/* Input Section */}
          <div className="mb-6 space-y-3">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddPrinciple()}
                placeholder="새로운 원칙을 입력해주세요"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm sm:text-base"
              />
              <button
                onClick={handleAddPrinciple}
                disabled={createMutation.isPending || !inputValue.trim()}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed text-sm sm:text-base font-medium"
              >
                {createMutation.isPending ? '추가중...' : '추가'}
              </button>
            </div>
          </div>

          {/* Principles List */}
          <div className="space-y-2">
            {isLoading ? (
              <div className="text-center py-8 text-gray-500">
                로딩 중...
              </div>
            ) : localPrinciples && localPrinciples.length > 0 ? (
              localPrinciples.map((principle) => (
                <div
                  key={principle.id}
                  className="flex items-start justify-between p-3 sm:p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
                >
                  <p className="flex-1 text-sm sm:text-base text-gray-800 break-words">
                    • {principle.principle_text}
                  </p>
                  <button
                    onClick={() => handleDeletePrinciple(principle.id)}
                    disabled={deleteMutation.isPending}
                    className="ml-2 flex-shrink-0 text-gray-400 hover:text-red-600 transition-colors disabled:text-gray-300 disabled:cursor-not-allowed"
                    title="삭제"
                  >
                    <Trash2 className="h-4 w-4 sm:h-5 sm:w-5" />
                  </button>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                등록된 원칙이 없습니다.
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 justify-end p-3 sm:p-6 border-t bg-gray-50">
          <button
            onClick={handleCancel}
            className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors text-sm sm:text-base font-medium"
          >
            취소
          </button>
          <button
            onClick={handleConfirm}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm sm:text-base font-medium"
          >
            확인
          </button>
        </div>
      </div>
    </div>
  )
}
