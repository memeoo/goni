'use client'

import { useMemo, useRef, useEffect, useState } from 'react'

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
  date: string // YYYYMMDD
  price: number
  quantity: number
  trade_type: string // '매수' 또는 '매도'
  order_no: string
  datetime: string
}

interface DailyChartProps {
  stockCode: string
  data: ChartDataPoint[]
  trades?: Trade[] | null
  onHoveredIndexChange?: (index: number | null) => void
}

// YYYYMMDD 형식을 YYYY-MM-DD로 변환
const formatTradeDate = (dateStr: string): string => {
  if (dateStr.length !== 8) return ''
  return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`
}

// 거래량을 1000 단위로 K로 표시
const formatVolume = (value: number): string => {
  if (value >= 1000000) {
    return (value / 1000000).toFixed(1) + 'M'
  } else if (value >= 1000) {
    return (value / 1000).toFixed(0) + 'K'
  }
  return value.toString()
}

// 날짜 형식 변환 (YYYY-MM-DD -> MM/DD)
const formatDateLabel = (dateStr: string): string => {
  const [, month, day] = dateStr.split('-')
  return `${parseInt(month)}/${parseInt(day)}`
}

export default function DailyChart({ stockCode, data, trades, onHoveredIndexChange }: DailyChartProps) {
  const canvasPriceRef = useRef<HTMLCanvasElement>(null)
  const canvasVolumeRef = useRef<HTMLCanvasElement>(null)
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)

  // hoveredIndex 변경 시 부모 컴포넌트에 알림
  useEffect(() => {
    onHoveredIndexChange?.(hoveredIndex)
  }, [hoveredIndex, onHoveredIndexChange])

  const chartConfig = useMemo(() => {
    if (!data || data.length === 0) {
      return null
    }

    // 최근 50개 데이터만 사용
    const recentData = data.slice(0, 50).reverse() // 오래된 순서로 정렬

    // 가격 범위 계산
    const prices = recentData.map((d) => [d.high, d.low, d.open, d.close]).flat()
    const minPrice = Math.min(...prices)
    const maxPrice = Math.max(...prices)

    // 10% 여유 추가
    const priceRange = maxPrice - minPrice
    const adjustedMin = minPrice - priceRange * 0.1
    const adjustedMax = maxPrice + priceRange * 0.1

    // 거래량 범위 계산
    const volumes = recentData.map((d) => d.volume)
    const maxVolume = Math.max(...volumes)

    return {
      data: recentData,
      priceMin: adjustedMin,
      priceMax: adjustedMax,
      maxVolume: maxVolume,
    }
  }, [data])

  // 캔들스틱 차트 그리기
  useEffect(() => {
    if (!chartConfig || !canvasPriceRef.current) return

    const canvas = canvasPriceRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const { data: chartData, priceMin, priceMax } = chartConfig
    const width = canvas.width
    const height = canvas.height
    const padding = { top: 20, right: 100, bottom: 5, left: 20 }
    const chartWidth = width - padding.left - padding.right
    const chartHeight = height - padding.top - padding.bottom

    // 배경
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, width, height)

    // 그리드 라인
    ctx.strokeStyle = '#e5e7eb'
    ctx.lineWidth = 1

    const priceRange = priceMax - priceMin
    const priceTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => priceMin + priceRange * ratio)

    // 수평선과 레이블
    priceTicks.forEach((price) => {
      const y = padding.top + chartHeight * (1 - (price - priceMin) / priceRange)

      ctx.beginPath()
      ctx.moveTo(padding.left, y)
      ctx.lineTo(width - padding.right, y)
      ctx.stroke()

      // 가격 레이블 (오른쪽에만 표시)
      ctx.fillStyle = '#6b7280'
      ctx.font = '11px sans-serif'
      ctx.textAlign = 'right'
      ctx.textBaseline = 'middle'
      ctx.fillText(Math.round(price).toLocaleString(), width - 5, y)
    })

    // 캔들 그리기
    const candleWidth = chartWidth / (chartData.length + 1)
    const candleBodyWidth = candleWidth * 0.6

    chartData.forEach((candle, index) => {
      const x = padding.left + candleWidth * (index + 0.5)

      // 가격을 Y좌표로 변환
      const yHigh = padding.top + chartHeight * (1 - (candle.high - priceMin) / priceRange)
      const yLow = padding.top + chartHeight * (1 - (candle.low - priceMin) / priceRange)
      const yOpen = padding.top + chartHeight * (1 - (candle.open - priceMin) / priceRange)
      const yClose = padding.top + chartHeight * (1 - (candle.close - priceMin) / priceRange)

      const isUp = candle.close >= candle.open
      const color = isUp ? '#ff4444' : '#4444ff'

      // 심지 그리기 (고가~저가 선)
      ctx.strokeStyle = color
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(x, yHigh)
      ctx.lineTo(x, yLow)
      ctx.stroke()

      // 몸통 그리기 (시가~종가 사각형)
      const bodyTop = Math.min(yOpen, yClose)
      const bodyBottom = Math.max(yOpen, yClose)
      const bodyHeight = Math.max(bodyBottom - bodyTop, 2)

      ctx.fillStyle = color
      ctx.fillRect(x - candleBodyWidth / 2, bodyTop, candleBodyWidth, bodyHeight)
    })

    // 이동평균선 그리기
    const drawMovingAverage = (maData: (number | null | undefined)[], color: string, lineWidth: number = 1.5) => {
      ctx.strokeStyle = color
      ctx.lineWidth = lineWidth
      ctx.beginPath()

      let isFirstPoint = true
      for (let index = 0; index < maData.length; index++) {
        const ma = maData[index]
        if (ma === null || ma === undefined) {
          if (!isFirstPoint) {
            ctx.stroke()
            ctx.beginPath()
            isFirstPoint = true
          }
          continue
        }

        const x = padding.left + candleWidth * (index + 0.5)
        const y = padding.top + chartHeight * (1 - (ma - priceMin) / priceRange)

        if (isFirstPoint) {
          ctx.moveTo(x, y)
          isFirstPoint = false
        } else {
          ctx.lineTo(x, y)
        }
      }
      ctx.stroke()
    }

    // 이동평균선별 데이터 추출
    const ma5Data = chartData.map((d) => d.ma5)
    const ma10Data = chartData.map((d) => d.ma10)
    const ma20Data = chartData.map((d) => d.ma20)
    const ma60Data = chartData.map((d) => d.ma60)

    // 이동평균선 그리기 (순서: 가장 긴 기간부터 짧은 기간으로, 겹치는 순서 최소화)
    drawMovingAverage(ma60Data, '#00AA00', 1.5) // 60일선 - 녹색
    drawMovingAverage(ma20Data, '#FFDD00', 1.5) // 20일선 - 노란색
    drawMovingAverage(ma10Data, '#00DDAA', 1.5) // 10일선 - 청녹색
    drawMovingAverage(ma5Data, '#FF69B4', 1.5) // 5일선 - 분홍색

    // 거래 마커 그리기
    if (trades && trades.length > 0) {
      trades.forEach((trade) => {
        // 거래 날짜를 YYYY-MM-DD 형식으로 변환
        const tradeDateFormatted = formatTradeDate(trade.date)

        // 차트 데이터에서 해당 날짜의 봉 찾기
        const candleIndex = chartData.findIndex((c) => c.date === tradeDateFormatted)

        if (candleIndex >= 0 && candleIndex < chartData.length) {
          // X 좌표 계산 (봉의 중심)
          const candleX = padding.left + candleWidth * (candleIndex + 0.5)

          // Y 좌표 계산 (거래 가격 위치)
          const priceY = padding.top + chartHeight * (1 - (trade.price - priceMin) / priceRange)

          // 거래 유형에 따른 색상 결정
          const isLongTrade = trade.trade_type === '매수'
          const markerColor = isLongTrade ? '#ff4444' : '#4444ff' // 매수: 빨강, 매도: 파랑
          const label = isLongTrade ? 'B' : 'S'

          // 텍스트 위치 (봉의 왼쪽에 배치 - 더 왼쪽으로)
          const textX = candleX - candleWidth * 0.65
          const textY = priceY

          // 텍스트 배경 원형 (흰색 배경 + 테두리)
          const circleRadius = 10

          // 화살표 시작점 (텍스트 테두리에 붙임)
          const arrowStartX = textX + circleRadius
          const arrowStartY = priceY
          ctx.fillStyle = 'white'
          ctx.strokeStyle = markerColor
          ctx.lineWidth = 1
          ctx.beginPath()
          ctx.arc(textX, textY, circleRadius, 0, Math.PI * 2)
          ctx.fill()
          ctx.stroke()

          // 텍스트 (B 또는 S) - 크기 25% 증대
          ctx.fillStyle = markerColor
          ctx.font = 'bold 12.5px sans-serif'
          ctx.textAlign = 'center'
          ctx.textBaseline = 'middle'
          ctx.fillText(label, textX, textY)

          // 화살표 그리기 (검은색)
          ctx.strokeStyle = '#000000'
          ctx.lineWidth = 1.5
          ctx.setLineDash([])

          // 화살표 선 (길이 1/4로 축소)
          const arrowLineLength = (candleX - 5 - arrowStartX) / 4
          ctx.beginPath()
          ctx.moveTo(arrowStartX, arrowStartY)
          ctx.lineTo(arrowStartX + arrowLineLength, priceY)
          ctx.stroke()

          // 화살표 헤드 (검은색) - 축소된 선의 끝에 위치
          const arrowHeadSize = 5
          const arrowHeadX = arrowStartX + arrowLineLength
          ctx.beginPath()
          ctx.moveTo(arrowHeadX, priceY)
          ctx.lineTo(arrowHeadX - arrowHeadSize, priceY - arrowHeadSize / 2)
          ctx.lineTo(arrowHeadX - arrowHeadSize, priceY + arrowHeadSize / 2)
          ctx.closePath()
          ctx.fillStyle = '#000000'
          ctx.fill()
        }
      })
    }

    // 마우스 hover 시 수직선 그리기
    if (hoveredIndex !== null && hoveredIndex < chartData.length) {
      const hoverX = padding.left + candleWidth * (hoveredIndex + 0.5)
      ctx.strokeStyle = '#999999'
      ctx.lineWidth = 1
      ctx.setLineDash([5, 5]) // 점선
      ctx.beginPath()
      ctx.moveTo(hoverX, padding.top)
      ctx.lineTo(hoverX, height - padding.bottom)
      ctx.stroke()
      ctx.setLineDash([]) // 실선으로 복원
    }
  }, [chartConfig, hoveredIndex, trades])

  // 거래량 차트 그리기
  useEffect(() => {
    if (!chartConfig || !canvasVolumeRef.current) return

    const canvas = canvasVolumeRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const { data: chartData, maxVolume } = chartConfig
    const width = canvas.width
    const height = canvas.height
    const padding = { top: 10, right: 100, bottom: 40, left: 20 }
    const chartWidth = width - padding.left - padding.right
    const chartHeight = height - padding.top - padding.bottom

    // 배경
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, width, height)

    // 그리드 라인
    ctx.strokeStyle = '#e5e7eb'
    ctx.lineWidth = 1

    const volumeTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => maxVolume * ratio)

    // 수평선과 레이블
    volumeTicks.forEach((volume) => {
      const y = padding.top + chartHeight * (1 - volume / maxVolume)

      ctx.beginPath()
      ctx.moveTo(padding.left, y)
      ctx.lineTo(width - padding.right, y)
      ctx.stroke()

      // 거래량 레이블 (오른쪽에만 표시)
      ctx.fillStyle = '#6b7280'
      ctx.font = '11px sans-serif'
      ctx.textAlign = 'right'
      ctx.textBaseline = 'middle'
      ctx.fillText(formatVolume(volume), width - 5, y)
    })

    // 거래량 바 그리기
    const barWidth = chartWidth / (chartData.length + 1)
    const barBodyWidth = barWidth * 0.6

    chartData.forEach((candle, index) => {
      const x = padding.left + barWidth * (index + 0.5)
      const barHeight = chartHeight * (candle.volume / maxVolume)
      const y = padding.top + chartHeight - barHeight

      // 전일 대비 거래량으로 색상 결정 (이전 캔들보다 크면 빨강, 작으면 파랑)
      let color = '#4444ff' // 기본값: 파란색 (거래량 감소 또는 첫 봉)
      if (index > 0) {
        if (candle.volume > chartData[index - 1].volume) {
          color = '#ff4444' // 빨간색 (거래량 증가)
        }
      } else {
        // 첫 번째 봉은 양봉/음봉으로 표시
        color = candle.close >= candle.open ? '#ff4444' : '#4444ff'
      }

      ctx.fillStyle = color
      ctx.fillRect(x - barBodyWidth / 2, y, barBodyWidth, barHeight)
    })

    // X축 라벨 (5일 단위 + 마지막 날짜)
    ctx.fillStyle = '#6b7280'
    ctx.font = '11px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'

    chartData.forEach((candle, index) => {
      // 5일 단위 또는 마지막 인덱스
      if (index % 5 === 0 || index === chartData.length - 1) {
        const x = padding.left + barWidth * (index + 0.5)
        const label = formatDateLabel(candle.date)
        ctx.fillText(label, x, height - padding.bottom + 5)
      }
    })

    // 마우스 hover 시 수직선 그리기
    if (hoveredIndex !== null && hoveredIndex < chartData.length) {
      const hoverX = padding.left + barWidth * (hoveredIndex + 0.5)
      ctx.strokeStyle = '#999999'
      ctx.lineWidth = 1
      ctx.setLineDash([5, 5]) // 점선
      ctx.beginPath()
      ctx.moveTo(hoverX, padding.top)
      ctx.lineTo(hoverX, height - padding.bottom)
      ctx.stroke()
      ctx.setLineDash([]) // 실선으로 복원
    }
  }, [chartConfig, hoveredIndex])

  // 마우스 좌표에 따른 봉 인덱스 계산
  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = e.currentTarget
    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const scaleX = canvas.width / rect.width

    if (!chartConfig) return

    const padding = { left: 20 }
    const chartWidth = canvas.width - padding.left - 100
    const candleWidth = chartWidth / (chartConfig.data.length + 1)
    const relativeX = x * scaleX - padding.left

    if (relativeX < 0) {
      setHoveredIndex(null)
      return
    }

    const index = Math.floor(relativeX / candleWidth - 0.5)
    if (index >= 0 && index < chartConfig.data.length) {
      setHoveredIndex(index)
    } else {
      setHoveredIndex(null)
    }
  }

  const handleCanvasMouseLeave = () => {
    setHoveredIndex(null)
  }

  if (!chartConfig) {
    return (
      <div className="w-full h-96 flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-400">차트 데이터를 불러오는 중...</p>
      </div>
    )
  }

  return (
    <div className="w-full space-y-0">
      {/* 가격 차트 */}
      <div className="bg-white border border-gray-200 rounded-t-lg p-2">
        <canvas
          ref={canvasPriceRef}
          width={1000}
          height={430}
          className="w-full block cursor-crosshair"
          onMouseMove={handleCanvasMouseMove}
          onMouseLeave={handleCanvasMouseLeave}
        />
      </div>

      {/* 거래량 차트 */}
      <div className="bg-white border border-gray-200 border-t-0 rounded-b-lg p-2">
        <canvas
          ref={canvasVolumeRef}
          width={1000}
          height={130}
          className="w-full block cursor-crosshair"
          onMouseMove={handleCanvasMouseMove}
          onMouseLeave={handleCanvasMouseLeave}
        />
      </div>
    </div>
  )
}
