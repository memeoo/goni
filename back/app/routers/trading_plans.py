from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import sys
import os

from app.database import get_database, get_db
from app import schemas, models
from app.routers.auth import get_current_user

# analyze 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..', 'analyze'))

router = APIRouter()


@router.get("/", response_model=List[schemas.TradingPlan])
async def get_trading_plans(
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.TokenData = Depends(get_current_user),
    db = Depends(get_database)
):
    """매매 계획 목록 조회"""
    # 실제 구현에서는 현재 유저의 매매 계획 조회
    return []


@router.get("/{plan_id}", response_model=schemas.TradingPlan)
async def get_trading_plan(
    plan_id: int,
    current_user: schemas.TokenData = Depends(get_current_user),
    db = Depends(get_database)
):
    """특정 매매 계획 조회"""
    # 실제 구현에서는 데이터베이스에서 특정 매매 계획 조회
    return {"message": "Trading plan get endpoint - implementation needed"}


@router.post("/", response_model=schemas.TradingPlan)
async def create_trading_plan(
    plan: schemas.TradingPlanCreate,
    current_user: schemas.TokenData = Depends(get_current_user),
    db = Depends(get_database)
):
    """새 매매 계획 생성"""
    # 실제 구현에서는 데이터베이스에 매매 계획 저장
    return {"message": "Trading plan creation endpoint - implementation needed"}


@router.put("/{plan_id}", response_model=schemas.TradingPlan)
async def update_trading_plan(
    plan_id: int,
    plan_update: schemas.TradingPlanUpdate,
    current_user: schemas.TokenData = Depends(get_current_user),
    db = Depends(get_database)
):
    """매매 계획 업데이트 (매매 실행 결과 및 복기 추가)"""
    # 실제 구현에서는 데이터베이스의 매매 계획 업데이트
    return {"message": "Trading plan update endpoint - implementation needed"}


@router.delete("/{plan_id}")
async def delete_trading_plan(
    plan_id: int,
    current_user: schemas.TokenData = Depends(get_current_user),
    db = Depends(get_database)
):
    """매매 계획 삭제"""
    # 실제 구현에서는 데이터베이스에서 매매 계획 삭제
    return {"message": "Trading plan deleted"}


@router.get("/trades/recent")
async def get_recent_trades(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Trading 테이블에서 최근 매매 내역 조회 (DB 기반)

    Args:
        limit (int): 조회할 거래 건수 (기본값: 20건)

    Returns:
        Dict: 매매 내역 리스트
    """
    try:
        print(f"🔍 DB에서 최근 매매내역 조회 시작: 최근 {limit}건")

        # Trading 테이블에서 사용자의 최근 거래 조회 (최신순)
        trading_records = db.query(models.Trading).filter(
            models.Trading.user_id == current_user.id
        ).order_by(models.Trading.executed_at.desc()).limit(limit).all()

        if not trading_records:
            print(f"⚠️ 조회된 매매내역이 없습니다.")
            return {
                "limit": limit,
                "data": [],
                "total_records": 0
            }

        print(f"✅ 매매내역 조회 완료: {len(trading_records)}건")

        # 응답 데이터 포맷팅 (복기 여부 추가)
        formatted_trades = []
        for trade in trading_records:
            # 복기 존재 여부 확인
            has_recap = False
            if trade.order_no:
                recap = db.query(models.Recap).filter(
                    models.Recap.order_no == trade.order_no,
                    models.Recap.user_id == current_user.id
                ).first()
                has_recap = recap is not None

            # trade_type 변환: 'buy' -> '매수', 'sell' -> '매도' (프론트 호환성)
            trade_type_display = '매수' if trade.trade_type == 'buy' else '매도'

            # datetime 형식 변환: datetime -> YYYYMMDDHHmmss
            datetime_str = trade.executed_at.strftime('%Y%m%d%H%M%S')

            formatted_trades.append({
                'stock_code': trade.stock_code,
                'stock_name': trade.stock_name,
                'trade_type': trade_type_display,  # '매수' 또는 '매도'
                'price': float(trade.executed_price),
                'quantity': int(trade.executed_quantity),
                'datetime': datetime_str,  # YYYYMMDDHHmmss
                'order_no': trade.order_no or '',
                'has_recap': has_recap
            })

        return {
            "limit": limit,
            "data": formatted_trades,
            "total_records": len(formatted_trades)
        }

    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return {
            "limit": limit,
            "data": [],
            "total_records": 0,
            "message": f"매매내역 조회 중 예상치 못한 오류가 발생했습니다: {str(e)}",
            "error": True
        }