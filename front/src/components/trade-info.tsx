'use client'

import React from 'react'
import { useForeignInstitutionalData } from '@/lib/hooks/use-foreign-institutional-data'

// ChartData 인터페이스는 여러 곳에서 사용될 수 있으므로, 필요하다면 별도 types 파일로 이동 가능
export interface ChartData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  trade_amount: number
  volume_change?: number
}

interface TradeInfoProps {
  stockCode?: string;
  // validData에서 마지막 거래량만 받도록 수정
  latestVolume?: number;
}

export default function TradeInfo({ stockCode, latestVolume }: TradeInfoProps) {
  // 외국인·기관 순매매 데이터 조회 훅을 컴포넌트 내부로 이동
  const { data: fiData, isLoading: fiLoading, error: fiError } = useForeignInstitutionalData(stockCode || '');

  return (
    <div className="mt-3 px-2">
      <div className="flex justify-between items-center text-xs">
        {/* 왼쪽: 거래량 정보 */}
        <div className="flex items-center gap-1 text-gray-600">
          <span>거래량:</span>
          <span className="font-medium">
            {latestVolume !== undefined ? latestVolume.toLocaleString() : '-'}
          </span>
        </div>
        
        {/* 오른쪽: 외국인·기관 수급 정보 */}
        {stockCode && (
          <div>
            {fiLoading ? (
              <span className="text-gray-400 animate-pulse">수급 로딩...</span>
            ) : fiError ? (
              <span className="text-gray-400" title={`수급 데이터 로드 실패: ${fiError.message}`}>
                API 연결 실패
              </span>
            ) : fiData && fiData.date ? (
              <div className="flex items-center gap-3">
                <div className="flex gap-2">
                  <div className="flex items-center gap-1">
                    <span className="text-gray-600">기관:</span>
                    <span className={`font-medium ${
                      fiData.institutional_net >= 0 ? 'text-red-600' : 'text-blue-600'
                    }`}>
                      {fiData.institutional_net >= 0 ? '+' : ''}{fiData.institutional_net.toLocaleString()}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-1">
                    <span className="text-gray-600">외국인:</span>
                    <span className={`font-medium ${
                      fiData.foreign_net >= 0 ? 'text-red-600' : 'text-blue-600'
                    }`}>
                      {fiData.foreign_net >= 0 ? '+' : ''}{fiData.foreign_net.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <span className="text-gray-400">데이터 없음</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
