'use client'

import { Lightbulb } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface Algorithm {
  id: number
  name: string
  description: string | null
  created_at?: string
  updated_at?: string
  issue_time?: string
}

interface AlgorithmCardProps {
  algorithm: Algorithm
  onClick?: (algorithm: Algorithm) => void
}

export default function AlgorithmCard({ algorithm, onClick }: AlgorithmCardProps) {
  const router = useRouter()

  const handleClick = () => {
    if (onClick) {
      onClick(algorithm)
    } else {
      // 기본 동작: 상세 페이지로 이동
      router.push(`/recommendation/${algorithm.id}`)
    }
  }

  return (
    <div
      className="bg-white border-2 border-gray-200 rounded-lg p-3 sm:p-4 md:p-6 hover:shadow-md transition-shadow cursor-pointer flex flex-col h-full group hover:border-blue-400"
      onClick={handleClick}
    >
      {/* Icon */}
      <div className="mb-2 sm:mb-3">
        <Lightbulb className="h-8 w-8 sm:h-10 sm:w-10 text-blue-600 group-hover:text-blue-700 transition-colors" />
      </div>

      {/* Algorithm Name */}
      <h3 className="text-sm sm:text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors mb-2 line-clamp-2">
        {algorithm.name}
      </h3>

      {/* Algorithm Description */}
      {algorithm.description && (
        <p className="text-xs sm:text-sm text-gray-600 line-clamp-3 flex-grow">
          {algorithm.description}
        </p>
      )}

      {/* Created Date */}
      {algorithm.created_at && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-2xs sm:text-xs text-gray-400">
            발행 시간: {algorithm.issue_time}
          </p>
        </div>
      )}
    </div>
  )
}
