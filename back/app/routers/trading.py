from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
from app.database import get_db
from app.models import Trading, User
from app.schemas import Trading as TradingSchema, TradingCreate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/trading", tags=["trading"])


@router.post("/", response_model=TradingSchema)
def create_trading(
    trading: TradingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """매매 기록 생성"""
    db_trading = Trading(
        user_id=current_user.id,
        executed_at=trading.executed_at,
        trade_type=trading.trade_type,
        order_no=trading.order_no,
        stock_name=trading.stock_name,
        stock_code=trading.stock_code,
        executed_price=trading.executed_price,
        executed_quantity=trading.executed_quantity,
        executed_amount=trading.executed_amount,
        broker=trading.broker
    )
    db.add(db_trading)
    db.commit()
    db.refresh(db_trading)
    return db_trading


@router.get("/", response_model=List[TradingSchema])
def get_trading_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0,
    trade_type: Optional[str] = None,
    stock_code: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    매매 기록 조회

    query params:
    - limit: 조회 개수 (기본값: 100)
    - offset: 페이징 오프셋 (기본값: 0)
    - trade_type: 필터 - 'buy' 또는 'sell'
    - stock_code: 필터 - 종목코드
    - start_date: 필터 - 시작 날짜
    - end_date: 필터 - 종료 날짜
    """
    query = db.query(Trading).filter(Trading.user_id == current_user.id)

    if trade_type:
        query = query.filter(Trading.trade_type == trade_type)
    if stock_code:
        query = query.filter(Trading.stock_code == stock_code)
    if start_date:
        query = query.filter(Trading.executed_at >= start_date)
    if end_date:
        query = query.filter(Trading.executed_at <= end_date)

    # 최신순으로 정렬
    records = query.order_by(Trading.executed_at.desc()).offset(offset).limit(limit).all()
    return records


@router.get("/{trading_id}", response_model=TradingSchema)
def get_trading_record(
    trading_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """특정 매매 기록 조회"""
    trading = db.query(Trading).filter(
        Trading.id == trading_id,
        Trading.user_id == current_user.id
    ).first()

    if not trading:
        raise HTTPException(status_code=404, detail="매매 기록을 찾을 수 없습니다")

    return trading


@router.put("/{trading_id}", response_model=TradingSchema)
def update_trading_record(
    trading_id: int,
    trading: TradingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """매매 기록 수정"""
    db_trading = db.query(Trading).filter(
        Trading.id == trading_id,
        Trading.user_id == current_user.id
    ).first()

    if not db_trading:
        raise HTTPException(status_code=404, detail="매매 기록을 찾을 수 없습니다")

    db_trading.executed_at = trading.executed_at
    db_trading.trade_type = trading.trade_type
    db_trading.order_no = trading.order_no
    db_trading.stock_name = trading.stock_name
    db_trading.stock_code = trading.stock_code
    db_trading.executed_price = trading.executed_price
    db_trading.executed_quantity = trading.executed_quantity
    db_trading.executed_amount = trading.executed_amount
    db_trading.broker = trading.broker
    db_trading.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_trading)
    return db_trading


@router.delete("/{trading_id}")
def delete_trading_record(
    trading_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """매매 기록 삭제"""
    trading = db.query(Trading).filter(
        Trading.id == trading_id,
        Trading.user_id == current_user.id
    ).first()

    if not trading:
        raise HTTPException(status_code=404, detail="매매 기록을 찾을 수 없습니다")

    db.delete(trading)
    db.commit()

    return {"message": "매매 기록이 삭제되었습니다"}


@router.get("/stats/summary", response_model=dict)
def get_trading_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    매매 통계 요약
    - 총 거래 수
    - 총 매수/매도 거래 수
    - 총 거래 금액
    """
    query = db.query(Trading).filter(Trading.user_id == current_user.id)

    if start_date:
        query = query.filter(Trading.executed_at >= start_date)
    if end_date:
        query = query.filter(Trading.executed_at <= end_date)

    records = query.all()

    total_trades = len(records)
    buy_trades = sum(1 for r in records if r.trade_type == 'buy')
    sell_trades = sum(1 for r in records if r.trade_type == 'sell')
    total_amount = sum(r.executed_amount for r in records)

    return {
        "total_trades": total_trades,
        "buy_trades": buy_trades,
        "sell_trades": sell_trades,
        "total_amount": total_amount
    }
