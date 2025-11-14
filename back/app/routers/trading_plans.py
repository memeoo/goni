from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
import sys
import os

from app.database import get_database, get_db
from app import schemas, models
from app.routers.auth import get_current_user

# analyze 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..', 'analyze'))

router = APIRouter()


@router.get("/plan-mode", tags=["trading-plans"])
def get_plan_mode_stocks(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    계획 모드용 종목 목록 조회 (매매 계획이 있는 종목)

    현재 사용자가 계획을 세운 종목들을 최신순으로 정렬하여 반환합니다.
    각 종목별로 계획의 개수를 포함합니다.
    """
    try:
        # 현재 사용자의 trading_plans에서 종목별로 그룹화하여 카운트 및 최신 시간 조회
        subquery = db.query(
            models.TradingPlan.stock_code,
            models.TradingPlan.stock_name,
            func.count(models.TradingPlan.id).label('plan_count'),
            func.max(models.TradingPlan.created_at).label('latest_created_at'),
            func.max(models.TradingPlan.id).label('latest_plan_id')
        ).filter(
            models.TradingPlan.user_id == current_user.id
        ).group_by(
            models.TradingPlan.stock_code,
            models.TradingPlan.stock_name
        ).subquery()

        # 전체 개수
        total = db.query(subquery).count()

        # 페이징 적용하여 종목 정보 조회
        stock_groups = db.query(
            subquery.c.stock_code,
            subquery.c.stock_name,
            subquery.c.plan_count,
            subquery.c.latest_created_at,
            subquery.c.latest_plan_id
        ).order_by(
            subquery.c.latest_created_at.desc()
        ).offset(skip).limit(limit).all()

        result = []

        for stock_code, stock_name, plan_count, latest_created_at, latest_plan_id in stock_groups:
            result.append({
                "id": latest_plan_id,  # TradingPlan ID (삭제용)
                "stock_code": stock_code,
                "stock_name": stock_name,
                "plan_count": plan_count,  # 해당 종목의 계획 개수
                "created_at": latest_created_at,
            })

        print(f"✅ 계획 모드 종목 조회 완료: {len(result)}건 (사용자 {current_user.id}의 계획 종목, 전체: {total}건)")

        return {
            "data": result,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    except Exception as e:
        print(f"❌ 계획 모드 종목 조회 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"계획 모드 종목 조회 중 오류가 발생했습니다: {str(e)}"
        )


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


@router.get("/by-stock/{stock_code}", tags=["trading-plans"])
def get_trading_plans_by_stock(
    stock_code: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    특정 종목의 모든 매매 계획 조회 (상세 정보 포함)

    TradingPlan과 TradingPlanHistory를 조인하여 모든 계획의 상세 정보를 반환합니다.
    """
    try:
        # TradingPlan 조회
        trading_plan = db.query(models.TradingPlan).filter(
            models.TradingPlan.user_id == current_user.id,
            models.TradingPlan.stock_code == stock_code
        ).first()

        if not trading_plan:
            return {
                "stock_code": stock_code,
                "plans": [],
                "total": 0
            }

        # TradingPlanHistory 조회 (최신순)
        plan_histories = db.query(models.TradingPlanHistory).filter(
            models.TradingPlanHistory.trading_plan_id == trading_plan.id
        ).order_by(models.TradingPlanHistory.created_at.desc()).all()

        plans = []
        for history in plan_histories:
            plans.append({
                "id": history.id,
                "stock_code": stock_code,
                "stock_name": trading_plan.stock_name,
                "trading_type": history.trading_type,
                "condition": history.condition,
                "target_price": history.target_price,
                "amount": history.amount,
                "reason": history.reason,
                "proportion": history.proportion,
                "sp_condition": history.sp_condition,
                "sp_price": history.sp_price,
                "sp_ratio": history.sp_ratio,
                "sl_condition": history.sl_condition,
                "sl_price": history.sl_price,
                "sl_ratio": history.sl_ratio,
                "created_at": history.created_at
            })

        print(f"✅ {stock_code}의 매매 계획 조회 완료: {len(plans)}건 (사용자 {current_user.id})")

        return {
            "stock_code": stock_code,
            "stock_name": trading_plan.stock_name,
            "plans": plans,
            "total": len(plans)
        }

    except Exception as e:
        print(f"❌ 매매 계획 조회 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"매매 계획 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{plan_id}", response_model=schemas.TradingPlan)
async def get_trading_plan(
    plan_id: int,
    current_user: schemas.TokenData = Depends(get_current_user),
    db = Depends(get_database)
):
    """특정 매매 계획 조회"""
    # 실제 구현에서는 데이터베이스에서 특정 매매 계획 조회
    return {"message": "Trading plan get endpoint - implementation needed"}


@router.post("/add-from-owned")
def add_trading_plan_from_owned(
    stock_codes: List[str] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    보유 종목으로부터 매매 계획 생성

    Args:
        stock_codes: 종목코드 리스트 (예: ['005930', '000660'])

    Returns:
        dict: 생성된 계획 정보
    """
    try:
        created_plans = []

        for stock_code in stock_codes:
            # 1단계: 기존 TradingPlan이 있는지 확인
            existing_plan = db.query(models.TradingPlan).filter(
                models.TradingPlan.user_id == current_user.id,
                models.TradingPlan.stock_code == stock_code
            ).first()

            if existing_plan:
                print(f"⚠️ {stock_code}는 이미 계획 모드에 추가되어 있습니다")
                continue

            # 2단계: TradingStock에서 종목 정보 조회
            trading_stock = db.query(models.TradingStock).filter(
                models.TradingStock.stock_code == stock_code
            ).first()

            # TradingStock이 없으면 StocksInfo 테이블에서 조회
            stock_name = None

            if trading_stock:
                stock_name = trading_stock.stock_name
            else:
                # StocksInfo 테이블에서 조회
                stock_info = db.query(models.StocksInfo).filter(
                    models.StocksInfo.code == stock_code
                ).first()

                if stock_info:
                    stock_name = stock_info.name
                    print(f"ℹ️ StocksInfo 테이블에서 {stock_name}({stock_code}) 조회됨")
                else:
                    print(f"⚠️ 종목 {stock_code}을 찾을 수 없습니다 (TradingStock, StocksInfo 모두 미존재)")
                    continue

            # 3단계: TradingPlan 생성 (계획 모드 종목 목록용)
            trading_plan = models.TradingPlan(
                user_id=current_user.id,
                stock_code=stock_code,
                stock_name=stock_name
            )

            db.add(trading_plan)
            db.flush()

            created_plans.append({
                "id": trading_plan.id,
                "stock_code": stock_code,
                "stock_name": stock_name
            })

            print(f"✨ TradingPlan 생성: {stock_name}({stock_code})")

        db.commit()

        print(f"✅ {len(created_plans)}개의 매매 계획 생성 완료")

        return {
            "message": f"{len(created_plans)}개의 매매 계획이 생성되었습니다",
            "created_plans": created_plans,
            "total": len(created_plans)
        }

    except Exception as e:
        db.rollback()
        print(f"❌ 매매 계획 생성 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"매매 계획 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/", response_model=schemas.TradingPlanHistory)
async def create_trading_plan(
    plan_data: Dict[str, Any] = Body(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    새 매매 계획 생성 (TradingPlan + TradingPlanHistory)

    Args:
        plan_data: 계획 데이터 (stock_code, stock_name, trading_type, condition, target_price, amount, reason, proportion, sp_*, sl_*)
    """
    try:
        # 필수 필드 확인
        if not plan_data.get('stock_code'):
            raise HTTPException(
                status_code=400,
                detail="stock_code는 필수 필드입니다"
            )
        if not plan_data.get('trading_type'):
            raise HTTPException(
                status_code=400,
                detail="trading_type은 필수 필드입니다"
            )

        stock_code = plan_data.get('stock_code')
        stock_name = plan_data.get('stock_name', '')

        # 1단계: TradingPlan이 없으면 생성 (또는 기존 것 사용)
        trading_plan = db.query(models.TradingPlan).filter(
            models.TradingPlan.user_id == current_user.id,
            models.TradingPlan.stock_code == stock_code
        ).first()

        if not trading_plan:
            trading_plan = models.TradingPlan(
                user_id=current_user.id,
                stock_code=stock_code,
                stock_name=stock_name
            )
            db.add(trading_plan)
            db.flush()
            print(f"✨ TradingPlan 생성: {stock_name}({stock_code})")
        else:
            print(f"ℹ️ 기존 TradingPlan 사용: {stock_name}({stock_code})")

        # 2단계: TradingPlanHistory 생성 (실제 계획 데이터)
        trading_plan_history = models.TradingPlanHistory(
            trading_plan_id=trading_plan.id,
            trading_type=plan_data.get('trading_type'),
            condition=plan_data.get('condition'),
            target_price=plan_data.get('target_price'),
            amount=plan_data.get('amount'),
            reason=plan_data.get('reason'),
            proportion=plan_data.get('proportion'),
            sp_condition=plan_data.get('sp_condition'),
            sp_price=plan_data.get('sp_price'),
            sp_ratio=plan_data.get('sp_ratio'),
            sl_condition=plan_data.get('sl_condition'),
            sl_price=plan_data.get('sl_price'),
            sl_ratio=plan_data.get('sl_ratio'),
        )

        db.add(trading_plan_history)
        db.commit()
        db.refresh(trading_plan_history)

        print(f"✅ 매매 계획 저장 완료: {stock_name}({stock_code}) - {plan_data.get('trading_type')}")

        return trading_plan_history

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ 매매 계획 저장 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"매매 계획 저장 중 오류가 발생했습니다: {str(e)}"
        )


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
    db: Session = Depends(get_db)
):
    """
    계획 모드 종목 삭제

    TradingPlan을 삭제하면 associated TradingPlanHistory도 CASCADE로 함께 삭제됩니다.
    """
    try:
        # 1단계: TradingPlan 조회
        trading_plan = db.query(models.TradingPlan).filter(
            models.TradingPlan.id == plan_id,
            models.TradingPlan.user_id == current_user.id
        ).first()

        if not trading_plan:
            raise HTTPException(
                status_code=404,
                detail="해당 계획 모드 종목을 찾을 수 없습니다."
            )

        stock_code = trading_plan.stock_code
        stock_name = trading_plan.stock_name

        # 2단계: 매매 계획 삭제 (관련 TradingPlanHistory는 CASCADE로 자동 삭제)
        db.delete(trading_plan)
        db.commit()

        print(f"✅ 계획 모드 종목 삭제 완료: {stock_name}({stock_code})")

        return {
            "message": "계획 모드 종목이 삭제되었습니다.",
            "deleted_plan_id": plan_id,
            "stock_code": stock_code,
            "stock_name": stock_name
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ 계획 모드 종목 삭제 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"계획 모드 종목 삭제 중 오류가 발생했습니다: {str(e)}"
        )