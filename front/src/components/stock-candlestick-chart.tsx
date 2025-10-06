import TradeInfo from './trade-info'

interface ChartData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  trade_amount: number
  volume_change?: number
}

interface StockCandlestickChartProps {
  data: ChartData[]
  className?: string
  height?: number
  stockCode?: string  // 종목코드 추가 (외국인·기관 데이터 조회용)
}

// 캔들스틱 Bar 커스텀 컴포넌트
const CandlestickBar = (props: any) => {
  const { payload, x, y, width, height, chartHeight, minPrice, maxPrice } = props
  
  console.log('CandlestickBar props:', { payload, x, y, width, height, minPrice, maxPrice })
  
  if (!payload || typeof payload.open !== 'number' || typeof payload.high !== 'number' || 
      typeof payload.low !== 'number' || typeof payload.close !== 'number') {
    console.log('Invalid payload:', payload)
    return null
  }
  
  const { open, high, low, close } = payload
  const isRising = close >= open
  const color = isRising ? '#ef4444' : '#3b82f6'
  
  // 전체 차트의 가격 범위 내에서 각 가격의 위치 계산
  const totalPriceRange = maxPrice - minPrice
  if (totalPriceRange === 0) return null
  
  // 각 가격이 전체 범위에서 차지하는 비율 (0~1)
  const highRatio = (maxPrice - high) / totalPriceRange
  const lowRatio = (maxPrice - low) / totalPriceRange  
  const openRatio = (maxPrice - open) / totalPriceRange
  const closeRatio = (maxPrice - close) / totalPriceRange
  
  // 실제 픽셀 위치 계산 (차트 영역 기준)
  const chartY = 10  // 차트 margin top
  const chartH = height - 20  // margin 제외한 실제 차트 높이
  
  const highY = chartY + chartH * highRatio
  const lowY = chartY + chartH * lowRatio
  const openY = chartY + chartH * openRatio
  const closeY = chartY + chartH * closeRatio
  
  const bodyTop = Math.min(openY, closeY)
  const bodyHeight = Math.abs(closeY - openY)
  const candleWidth = Math.min(width * 0.6, 8)
  const candleX = x + (width - candleWidth) / 2
  const wickX = x + width / 2
  
  return (
    <g>
      {/* 위꼬리 */}
      <line
        x1={wickX}
        y1={highY}
        x2={wickX}
        y2={bodyTop}
        stroke={color}
        strokeWidth={1}
      />
      
      {/* 아래꼬리 */}
      <line
        x1={wickX}
        y1={bodyTop + bodyHeight}
        x2={wickX}
        y2={lowY}
        stroke={color}
        strokeWidth={1}
      />
      
      {/* 캔들 몸통 */}
      <rect
        x={candleX}
        y={bodyTop}
        width={candleWidth}
        height={Math.max(bodyHeight, 1)}
        fill={isRising ? color : '#ffffff'}
        stroke={color}
        strokeWidth={1}
      />
    </g>
  )
}

// 거래량 바 컴포넌트는 Cell로 대체

// 커스텀 툴팁
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    
    // 날짜 처리 - label이 문자열이 아닐 수 있으므로 안전하게 처리
    let formattedDate = ''
    try {
      if (typeof label === 'string' && label) {
        formattedDate = format(parseISO(label), 'yyyy-MM-dd')
      } else if (data?.date) {
        formattedDate = typeof data.date === 'string' 
          ? format(parseISO(data.date), 'yyyy-MM-dd')
          : data.date.toISOString().split('T')[0]
      } else {
        formattedDate = new Date().toISOString().split('T')[0]
      }
    } catch (error) {
      formattedDate = String(label) || '날짜 불명'
    }
    
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-lg">
        <p className="text-sm font-medium text-gray-900 mb-2">
          {formattedDate}
        </p>
        <div className="space-y-1 text-xs">
          <div className="flex justify-between gap-4">
            <span className="text-gray-600">시가:</span>
            <span className="font-medium">{data.open?.toLocaleString()}원</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-600">고가:</span>
            <span className="font-medium text-red-600">{data.high?.toLocaleString()}원</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-600">저가:</span>
            <span className="font-medium text-blue-600">{data.low?.toLocaleString()}원</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-600">종가:</span>
            <span className="font-medium">{data.close?.toLocaleString()}원</span>
          </div>
          {/* <div className="flex justify-between gap-4">
            <span className="text-gray-600">거래량:</span>
            <span className="font-medium">{data.volume?.toLocaleString()}주</span>
          </div> */}
        </div>
      </div>
    )
  }
  
  return null
}

export default function StockCandlestickChart({ 
  data, 
  className = '', 
  height = 450,
  stockCode 
}: StockCandlestickChartProps) {
  
  
  if (!data || data.length === 0) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ height }}>
        <p className="text-gray-500 text-sm">차트 데이터가 없습니다</p>
      </div>
    )
  }
  
  // 데이터 검증 및 정제
  const validData = data.filter(d => 
    d && 
    typeof d.open === 'number' && 
    typeof d.high === 'number' && 
    typeof d.low === 'number' && 
    typeof d.close === 'number' &&
    typeof d.volume === 'number' &&
    d.date
  ).map(d => ({
    ...d,
    date: typeof d.date === 'string' ? d.date : String(d.date)
  }))
  
  if (validData.length === 0) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ height }}>
        <p className="text-gray-500 text-sm">유효한 차트 데이터가 없습니다</p>
      </div>
    )
  }
  
  // 가격 범위 계산
  const prices = validData.flatMap(d => [d.open, d.high, d.low, d.close])
  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)
  const priceMargin = (maxPrice - minPrice) * 0.1
  
  
  // 최신 가격 표시 제거
  
  return (
    <div className={`${className}`}>
      {/* 캔들스틱 차트 */}
      <div className="relative" style={{ height: height * 0.72 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={validData}
            margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
          >
            <XAxis 
              dataKey="date" 
              type="category"
              hide 
            />
            <YAxis 
              type="number"
              domain={[minPrice - priceMargin, maxPrice + priceMargin]} 
              hide 
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* 투명한 Bar로 영역 잡기 */}
            <Bar dataKey="high" fill="transparent" />
          </ComposedChart>
        </ResponsiveContainer>
        
        {/* 캔들스틱을 SVG로 직접 그리기 */}
        <svg 
          className="absolute inset-0 pointer-events-none w-full h-full"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
        >
          {validData.map((item, index) => {
            const { open, high, low, close } = item
            const isRising = close >= open
            const color = isRising ? '#ef4444' : '#3b82f6'
            
            // X 위치 계산 - 좌우 여백을 두고 배치 (5% 여백)
            const chartWidth = 90  // 실제 차트 너비 (90%)
            const startX = 5  // 시작 위치 (5% 여백)
            const barWidth = chartWidth / validData.length  // 각 바의 너비 (%)
            const x = startX + index * barWidth + barWidth / 2  // 중앙 위치
            const candleWidth = Math.min(barWidth * 0.7, 4)  // 캔들 너비 (더 넓게)
            
            // Y 위치 계산 (가격 비례) - 상하 여백 3%씩으로 줄임
            const priceRange = (maxPrice + priceMargin) - (minPrice - priceMargin)
            if (priceRange === 0) return null
            
            const chartHeight = 94  // 실제 차트 높이 (94%)
            const startY = 3  // 시작 위치 (3% 여백)
            
            const highY = startY + ((maxPrice + priceMargin) - high) / priceRange * chartHeight
            const lowY = startY + ((maxPrice + priceMargin) - low) / priceRange * chartHeight
            const openY = startY + ((maxPrice + priceMargin) - open) / priceRange * chartHeight
            const closeY = startY + ((maxPrice + priceMargin) - close) / priceRange * chartHeight
            
            const bodyTop = Math.min(openY, closeY)
            const bodyHeight = Math.abs(closeY - openY)
            
            
            return (
              <g key={`candle-${index}-${item.date}`}>
                {/* 위꼬리 */}
                <line
                  x1={x}
                  y1={highY}
                  x2={x}
                  y2={bodyTop}
                  stroke={color}
                  strokeWidth="0.4"
                  vectorEffect="non-scaling-stroke"
                />
                
                {/* 아래꼬리 */}
                <line
                  x1={x}
                  y1={bodyTop + bodyHeight}
                  x2={x}
                  y2={lowY}
                  stroke={color}
                  strokeWidth="0.4"
                  vectorEffect="non-scaling-stroke"
                />
                
                {/* 캔들 몸통 */}
                <rect
                  x={x - candleWidth/2}
                  y={bodyTop}
                  width={candleWidth}
                  height={Math.max(bodyHeight, 0.8)}
                  fill={isRising ? color : '#ffffff'}
                  stroke={color}
                  strokeWidth="0.4"
                  vectorEffect="non-scaling-stroke"
                />
              </g>
            )
          })}
        </svg>
        
      </div>
      
      {/* 차트 사이 간격 */}
      <div className="py-2"></div>
      
      {/* 거래량 차트 */}
      <div style={{ height: height * 0.23 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={validData}
            margin={{ top: 5, right: 30, left: 10, bottom: 10 }}
            barCategoryGap="0%"
          >
            {/* 캔들 차트와 동일한 X축 설정으로 정렬 */}
            <XAxis 
              dataKey="date" 
              type="category"
              hide 
              axisLine={false}
              tickLine={false}
              scale="point"
              padding={{ left: 0.05, right: 0.05 }}
            />
            <YAxis 
              hide 
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              formatter={(value) => [
                `${Number(value).toLocaleString()}주`,
                '거래량'
              ]}
              labelFormatter={(value) => {
                try {
                  if (typeof value === 'string' && value) {
                    return format(parseISO(value), 'yyyy-MM-dd')
                  } else {
                    return String(value) || '날짜 불명'
                  }
                } catch (error) {
                  return String(value) || '날짜 불명'
                }
              }}
            />
            
            <Bar 
              dataKey="volume"
              radius={[1, 1, 0, 0]}
              maxBarSize={40}
              stroke="#ffffff"
              strokeWidth={0.5}
            >
              {validData.map((entry, index) => (
                <Cell
                  key={`volume-cell-${index}`}
                  fill={(entry.volume_change ?? 0) >= 0 ? '#ef4444' : '#3b82f6'}
                  stroke="#e5e7eb"
                  strokeWidth={0.5}
                />
              ))}
            </Bar>
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      
      {/* 거래량 및 외국인·기관 수급 정보 */}
      <TradeInfo 
        stockCode={stockCode}
        latestVolume={validData.length > 0 ? validData[validData.length - 1].volume : undefined}
      />
    </div>
  )
}