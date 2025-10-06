'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  formatCurrency,
  formatPercent,
  formatDateTime,
  getStatusColor,
  calculateProfit,
  cn,
} from '@/lib/utils'
import { TrendingUp, TrendingDown, Edit, Trash2 } from 'lucide-react'
import { TradingPlan } from '@/types'

interface TradingPlanCardProps {
  plan: TradingPlan
  onEdit?: () => void
  onDelete?: () => void
  onExecute?: () => void
}

export function TradingPlanCard({
  plan,
  onEdit,
  onDelete,
  onExecute,
}: TradingPlanCardProps) {
  const isBuy = plan.plan_type === 'buy'
  const planTypeColor = isBuy ? 'text-red-500' : 'text-blue-500'
  const PlanIcon = isBuy ? TrendingUp : TrendingDown
  const planTypeText = isBuy ? '매수' : '매도'

  const profit =
    plan.executed_price && plan.executed_quantity
      ? calculateProfit(
          isBuy ? plan.target_price : plan.executed_price,
          isBuy ? plan.executed_price : plan.target_price,
          plan.executed_quantity
        )
      : null

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">
            {plan.stock.name}
          </CardTitle>
          <div className="flex items-center space-x-2">
            <Badge
              className={cn('text-xs', planTypeColor)}
              variant="outline"
            >
              <PlanIcon className="mr-1 h-3 w-3" />
              {planTypeText}
            </Badge>
            <Badge className={getStatusColor(plan.status)}>
              {plan.status === 'planned' && '계획됨'}
              {plan.status === 'executed' && '실행됨'}
              {plan.status === 'reviewed' && '복기완료'}
            </Badge>
          </div>
        </div>
        <p className="text-sm text-gray-500">
          {plan.stock.symbol} • {plan.stock.market}
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 계획 정보 */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">목표가</span>
            <p className="font-semibold">{formatCurrency(plan.target_price)}</p>
          </div>
          <div>
            <span className="text-gray-500">수량</span>
            <p className="font-semibold">{plan.quantity.toLocaleString()}주</p>
          </div>
        </div>

        {/* 실행 정보 (있는 경우) */}
        {plan.executed_price && plan.executed_quantity && (
          <div className="border-t pt-3">
            <h4 className="font-semibold text-sm mb-2">실행 결과</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">실행가</span>
                <p className="font-semibold">
                  {formatCurrency(plan.executed_price)}
                </p>
              </div>
              <div>
                <span className="text-gray-500">실행수량</span>
                <p className="font-semibold">
                  {plan.executed_quantity.toLocaleString()}주
                </p>
              </div>
            </div>
            
            {profit && (
              <div className="mt-2 p-2 bg-gray-50 rounded">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">수익/손실</span>
                  <div
                    className={cn(
                      'font-semibold',
                      profit.profit >= 0 ? 'text-red-500' : 'text-blue-500'
                    )}
                  >
                    <span>{formatCurrency(profit.profit)}</span>
                    <span className="ml-1 text-sm">
                      ({formatPercent(profit.profitRate)})
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 매매 이유 */}
        <div>
          <span className="text-gray-500 text-sm">매매 이유</span>
          <p className="text-sm mt-1 p-2 bg-gray-50 rounded">{plan.reason}</p>
        </div>

        {/* 복기 (있는 경우) */}
        {plan.review && (
          <div>
            <span className="text-gray-500 text-sm">복기</span>
            <p className="text-sm mt-1 p-2 bg-gray-50 rounded">{plan.review}</p>
          </div>
        )}

        {/* 날짜 정보 */}
        <div className="text-xs text-gray-400 space-y-1">
          <div>계획일: {formatDateTime(plan.created_at)}</div>
          {plan.executed_at && (
            <div>실행일: {formatDateTime(plan.executed_at)}</div>
          )}
          {plan.updated_at !== plan.created_at && (
            <div>수정일: {formatDateTime(plan.updated_at)}</div>
          )}
        </div>

        {/* 액션 버튼들 */}
        <div className="flex justify-end space-x-2 pt-2 border-t">
          {plan.status === 'planned' && onExecute && (
            <Button size="sm" onClick={onExecute}>
              실행 기록
            </Button>
          )}
          {onEdit && (
            <Button size="sm" variant="outline" onClick={onEdit}>
              <Edit className="h-4 w-4 mr-1" />
              수정
            </Button>
          )}
          {onDelete && (
            <Button size="sm" variant="destructive" onClick={onDelete}>
              <Trash2 className="h-4 w-4 mr-1" />
              삭제
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}