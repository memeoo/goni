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


@router.post("/sync-dashboard-trades")
async def sync_dashboard_trades(
    stock_codes: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    대시보드에 표시된 종목들의 거래 기록을 조회하여 Trading 테이블에 추가
    - 이미 존재하는 기록(order_no 기반)은 제외하고 새로운 기록만 추가

    Args:
        stock_codes: 종목코드 리스트 (예: ['005930', '000660'])

    Returns:
        {
            "status": "success",
            "message": "3건의 새로운 거래 기록이 추가되었습니다.",
            "synced_count": 3,
            "duplicate_count": 2,
            "failed_count": 0
        }
    """
    import os
    from dotenv import load_dotenv

    try:
        # .env 파일 경로 설정
        analyze_env_path = os.path.join(os.path.dirname(__file__), '../../../analyze/.env')
        load_dotenv(analyze_env_path)

        # KiwoomAPI를 통해 종목별 거래 기록 조회
        from lib.kiwoom import KiwoomAPI

        app_key = os.getenv('KIWOOM_APP_KEY')
        secret_key = os.getenv('KIWOOM_SECRET_KEY')
        account_no = os.getenv('KIWOOM_ACCOUNT_NO')

        if not all([app_key, secret_key, account_no]):
            return {
                "status": "warning",
                "message": "키움증권 API 설정이 완료되지 않았습니다",
                "synced_count": 0,
                "duplicate_count": 0,
                "failed_count": len(stock_codes)
            }

        api = KiwoomAPI(
            app_key=app_key,
            secret_key=secret_key,
            account_no=account_no,
            use_mock=False
        )

        # 최근 거래 기록 조회 (90일)
        all_trades = api.get_recent_trades(days=90)

        # 기존 거래 기록 조회 (중복 체크용)
        existing_order_nos = set(
            record.order_no for record in
            db.query(Trading).filter(Trading.user_id == current_user.id).all()
            if record.order_no
        )

        synced_count = 0
        duplicate_count = 0
        failed_count = 0

        # 각 종목별로 거래 기록 처리
        for stock_code in stock_codes:
            try:
                # 해당 종목의 거래 필터링
                stock_trades = [
                    trade for trade in all_trades
                    if trade['stock_code'] == stock_code
                ]

                for trade in stock_trades:
                    # order_no 기반 중복 체크
                    if trade['order_no'] and trade['order_no'] in existing_order_nos:
                        duplicate_count += 1
                        continue

                    # 거래 기록 생성
                    try:
                        # datetime 형식 변환 (YYYYMMDDHHmmss -> datetime)
                        datetime_str = trade['datetime']
                        if isinstance(datetime_str, str) and len(datetime_str) == 14:
                            from datetime import datetime as dt
                            executed_at = dt.strptime(datetime_str, '%Y%m%d%H%M%S')
                        else:
                            executed_at = trade.get('executed_at', datetime.utcnow())

                        # trade_type 변환
                        trade_type = 'buy' if trade['trade_type'] == '매수' else 'sell'

                        # executed_amount 계산
                        executed_amount = trade.get('executed_amount', trade['price'] * trade['quantity'])

                        # Trading 레코드 생성
                        new_trading = Trading(
                            user_id=current_user.id,
                            executed_at=executed_at,
                            trade_type=trade_type,
                            order_no=trade.get('order_no'),
                            stock_name=trade['stock_name'],
                            stock_code=stock_code,
                            executed_price=trade['price'],
                            executed_quantity=trade['quantity'],
                            executed_amount=executed_amount,
                            broker='kiwoom'
                        )

                        db.add(new_trading)
                        synced_count += 1

                        # order_no가 있으면 기록
                        if trade['order_no']:
                            existing_order_nos.add(trade['order_no'])

                    except Exception as e:
                        print(f"❌ 거래 기록 생성 실패 (주문번호: {trade.get('order_no')}): {e}")
                        failed_count += 1
                        continue

            except Exception as e:
                print(f"❌ 종목 {stock_code} 거래 기록 조회 실패: {e}")
                failed_count += 1
                continue

        # 데이터베이스에 커밋
        db.commit()

        print(f"✅ 거래 기록 동기화 완료 - 추가: {synced_count}건, 중복: {duplicate_count}건, 실패: {failed_count}건")

        return {
            "status": "success",
            "message": f"{synced_count}건의 새로운 거래 기록이 추가되었습니다.",
            "synced_count": synced_count,
            "duplicate_count": duplicate_count,
            "failed_count": failed_count
        }

    except ImportError as e:
        print(f"❌ 키움증권 API 모듈 import 오류: {e}")
        return {
            "status": "error",
            "message": f"키움증권 API 모듈을 불러올 수 없습니다: {str(e)}",
            "synced_count": 0,
            "duplicate_count": 0,
            "failed_count": len(stock_codes)
        }
    except Exception as e:
        print(f"❌ 거래 기록 동기화 중 오류: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return {
            "status": "error",
            "message": f"거래 기록 동기화 중 오류가 발생했습니다: {str(e)}",
            "synced_count": 0,
            "duplicate_count": 0,
            "failed_count": len(stock_codes)
        }
