from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
from app.database import get_db
from app.models import TradingHistory, User, TradingStock
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
    db_trading = TradingHistory(
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


@router.get("/{stock_code}/trades")
def get_stock_trades(
    stock_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    """
    특정 종목의 사용자 거래 기록 조회 (Trading 테이블에서)

    Args:
        stock_code: 종목코드 (6자리, 예: '005930')
        limit: 조회 개수 (기본값: 100)
        offset: 시작 위치 (기본값: 0)

    Returns:
        {
            "stock_code": "005930",
            "trades": [
                {
                    "date": "2025-11-01",
                    "price": 70500,
                    "quantity": 10,
                    "trade_type": "매수",  # '매수' 또는 '매도'
                    "order_no": "12345678",
                    "datetime": "20251101143000"
                },
                ...
            ],
            "total_records": 5
        }
    """
    try:
        # 현재 사용자의 해당 종목 거래 기록 조회
        query = db.query(TradingHistory).filter(
            TradingHistory.user_id == current_user.id,
            TradingHistory.stock_code == stock_code
        ).order_by(TradingHistory.executed_at.desc())

        total_records = query.count()
        trades = query.offset(offset).limit(limit).all()

        # 응답 데이터 포맷 변환
        result_trades = []
        for trade in trades:
            # trade_type 변환: 'buy' -> '매수', 'sell' -> '매도'
            trade_type_display = '매수' if trade.trade_type == 'buy' else '매도'

            # datetime을 YYYYMMDDHHmmss 형식으로 변환
            datetime_str = trade.executed_at.strftime('%Y%m%d%H%M%S')
            # date를 YYYYMMDD 형식으로 변환 (차트에서 날짜 매칭을 위해)
            date_str = trade.executed_at.strftime('%Y%m%d')

            result_trades.append({
                'date': date_str,
                'price': trade.executed_price,
                'quantity': trade.executed_quantity,
                'trade_type': trade_type_display,
                'order_no': trade.order_no or '',
                'datetime': datetime_str,
            })

        print(f"✅ 종목 {stock_code}의 거래 기록 조회 완료: {len(result_trades)}건 (사용자: {current_user.id})")

        return {
            'stock_code': stock_code,
            'trades': result_trades,
            'total_records': total_records
        }

    except Exception as e:
        print(f"❌ 거래 기록 조회 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"거래 기록 조회 중 오류가 발생했습니다: {str(e)}"
        )


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
    query = db.query(TradingHistory).filter(TradingHistory.user_id == current_user.id)

    if trade_type:
        query = query.filter(TradingHistory.trade_type == trade_type)
    if stock_code:
        query = query.filter(TradingHistory.stock_code == stock_code)
    if start_date:
        query = query.filter(TradingHistory.executed_at >= start_date)
    if end_date:
        query = query.filter(TradingHistory.executed_at <= end_date)

    # 최신순으로 정렬
    records = query.order_by(TradingHistory.executed_at.desc()).offset(offset).limit(limit).all()
    return records


@router.get("/{trading_id}", response_model=TradingSchema)
def get_trading_record(
    trading_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """특정 매매 기록 조회"""
    trading = db.query(TradingHistory).filter(
        TradingHistory.id == trading_id,
        TradingHistory.user_id == current_user.id
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
    db_trading = db.query(TradingHistory).filter(
        TradingHistory.id == trading_id,
        TradingHistory.user_id == current_user.id
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
    trading = db.query(TradingHistory).filter(
        TradingHistory.id == trading_id,
        TradingHistory.user_id == current_user.id
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
    query = db.query(TradingHistory).filter(TradingHistory.user_id == current_user.id)

    if start_date:
        query = query.filter(TradingHistory.executed_at >= start_date)
    if end_date:
        query = query.filter(TradingHistory.executed_at <= end_date)

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


@router.post("/sync-stocks")
def sync_traded_stocks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    매매 기록에 있는 종목들을 trading_stocks 테이블에 동기화
    중복된 종목은 is_downloaded 상태만 유지
    """
    try:
        # 현재 사용자의 모든 거래 기록에서 고유한 종목 조회
        trades = db.query(TradingHistory).filter(
            TradingHistory.user_id == current_user.id
        ).all()

        # 고유한 종목 추출 (stock_code 기준)
        unique_stocks = {}
        for trade in trades:
            if trade.stock_code not in unique_stocks:
                unique_stocks[trade.stock_code] = {
                    'stock_code': trade.stock_code,
                    'stock_name': trade.stock_name
                }

        # trading_stocks 테이블에 업데이트
        added_count = 0
        updated_count = 0

        for stock_code, stock_info in unique_stocks.items():
            # 기존 종목 확인
            existing_stock = db.query(TradingStock).filter(
                TradingStock.stock_code == stock_code
            ).first()

            if existing_stock:
                # 기존 종목 - stock_name 업데이트 (is_downloaded는 유지)
                existing_stock.stock_name = stock_info['stock_name']
                existing_stock.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # 신규 종목 추가
                new_stock = TradingStock(
                    stock_name=stock_info['stock_name'],
                    stock_code=stock_code,
                    is_downloaded=False
                )
                db.add(new_stock)
                added_count += 1

        db.commit()

        print(f"✅ 매매 종목 동기화 완료: {added_count}건 추가, {updated_count}건 업데이트 (사용자: {current_user.id})")

        return {
            "message": "종목 동기화 완료",
            "added": added_count,
            "updated": updated_count,
            "total": len(unique_stocks)
        }

    except Exception as e:
        print(f"❌ 종목 동기화 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"종목 동기화 중 오류가 발생했습니다: {str(e)}"
        )

