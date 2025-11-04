from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from app.database import get_db
from app.models import TradingStock, TradingHistory, User
from app.routers.auth import get_current_user
import sys
import os

# analyze 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../analyze'))
from lib.kiwoom import KiwoomAPI

router = APIRouter(prefix="/api/trading-stocks", tags=["trading-stocks"])


@router.post("/sync-from-kiwoom")
def sync_trading_stocks_from_kiwoom(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = 30
):
    """
    Kiwoom API에서 실제 매매 기록을 조회하여 trading_stocks 테이블에 동기화

    Args:
        days: 조회할 일수 (기본값: 5일)

    Returns:
        dict: 동기화 결과
    """
    try:
        # 사용자의 Kiwoom 계정 정보 확인
        if not current_user.app_key or not current_user.app_secret:
            raise HTTPException(
                status_code=400,
                detail="Kiwoom 계정 정보가 등록되지 않았습니다. 설정에서 계정 정보를 등록해주세요."
            )

        print(f"🔄 Kiwoom API에서 최근 {days}일 거래 데이터 조회 중... (사용자: {current_user.id})")

        # Kiwoom API 인스턴스 생성
        kiwoom_api = KiwoomAPI(
            app_key=current_user.app_key,
            secret_key=current_user.app_secret,
            account_no="",  # 계정번호는 API 응답에서 자동 처리
            use_mock=False
        )

        # Kiwoom API의 get_recent_trades()를 사용하여 최근 N일간의 거래 데이터 조회
        print(f"  {days}일간의 거래 기록 조회 중...")
        kiwoom_trades = kiwoom_api.get_recent_trades(days=days)

        if not kiwoom_trades:
            print("⚠️ Kiwoom API에서 조회된 거래 기록이 없습니다")
            return {
                "message": "조회된 거래 기록이 없습니다",
                "added_trades": 0,
                "added_stocks": 0,
                "updated_stocks": 0
            }

        print(f"✅ Kiwoom API에서 {len(kiwoom_trades)}건의 거래 기록 조회 완료")
        for trade in kiwoom_trades[:10]:  # 최근 10건만 로그에 출력
            print(f"  - {trade['stock_name']}({trade['stock_code']}) {trade['trade_type']} {trade['quantity']}주 @ {trade['price']} ({trade['datetime']})")
        if len(kiwoom_trades) > 10:
            print(f"  ... 외 {len(kiwoom_trades) - 10}건")

        # 1단계: TradingHistory 테이블에 매매 기록 저장
        added_trades = 0
        for trade in kiwoom_trades:
            # 중복 확인 (order_no 기준)
            existing_trade = db.query(TradingHistory).filter(
                TradingHistory.user_id == current_user.id,
                TradingHistory.order_no == trade.get('order_no', ''),
                TradingHistory.stock_code == trade['stock_code']
            ).first()

            if not existing_trade and trade.get('order_no'):  # order_no가 있는 경우만 중복 체크
                try:
                    # 날짜시간 파싱
                    datetime_str = trade['datetime']  # YYYYMMDDHHmmss 형식
                    executed_at = datetime.strptime(datetime_str, '%Y%m%d%H%M%S')

                    new_trade = TradingHistory(
                        user_id=current_user.id,
                        executed_at=executed_at,
                        trade_type=trade['trade_type'],
                        order_no=trade.get('order_no', ''),
                        stock_name=trade['stock_name'],
                        stock_code=trade['stock_code'],
                        executed_price=trade['price'],
                        executed_quantity=trade['quantity'],
                        executed_amount=int(trade['price'] * trade['quantity']),
                        broker='kiwoom'
                    )
                    db.add(new_trade)
                    added_trades += 1

                except Exception as e:
                    print(f"⚠️ 매매 기록 저장 실패: {trade.get('stock_name')} - {e}")
                    continue

        db.commit()
        print(f"✅ TradingHistory 저장 완료: {added_trades}건 추가")

        # 2단계: trading_stocks 테이블에 종목 정보 저장 및 업데이트
        unique_stocks = {}
        for trade in kiwoom_trades:
            stock_code = trade['stock_code']
            if stock_code not in unique_stocks:
                unique_stocks[stock_code] = {
                    'stock_code': stock_code,
                    'stock_name': trade['stock_name']
                }

        added_stocks = 0
        updated_stocks = 0

        for stock_code, stock_info in unique_stocks.items():
            existing_stock = db.query(TradingStock).filter(
                TradingStock.stock_code == stock_code
            ).first()

            if existing_stock:
                # 기존 종목 - stock_name 업데이트 (is_downloaded는 유지)
                existing_stock.stock_name = stock_info['stock_name']
                existing_stock.updated_at = datetime.utcnow()
                updated_stocks += 1
                print(f"  ✏️ {stock_info['stock_name']}({stock_code}) 업데이트")
            else:
                # 신규 종목 추가
                new_stock = TradingStock(
                    stock_name=stock_info['stock_name'],
                    stock_code=stock_code,
                    is_downloaded=False
                )
                db.add(new_stock)
                added_stocks += 1
                print(f"  ✨ {stock_info['stock_name']}({stock_code}) 추가")

        db.commit()
        print(f"✅ trading_stocks 업데이트 완료: {added_stocks}건 추가, {updated_stocks}건 업데이트")

        return {
            "message": "Kiwoom 매매 기록 동기화 완료",
            "added_trades": added_trades,
            "added_stocks": added_stocks,
            "updated_stocks": updated_stocks,
            "total_stocks": len(unique_stocks)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Kiwoom 동기화 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Kiwoom 동기화 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/")
def get_trading_stocks(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    매매 종목 목록 조회

    Query Parameters:
    - skip: 오프셋 (기본값: 0)
    - limit: 조회 개수 (기본값: 100)
    """
    try:
        # 전체 trading_stocks 조회 (사용자별 제한 없음 - 시스템 전역 종목)
        stocks = db.query(TradingStock).offset(skip).limit(limit).all()
        total = db.query(TradingStock).count()

        result = [
            {
                "id": stock.id,
                "stock_code": stock.stock_code,
                "stock_name": stock.stock_name,
                "is_downloaded": stock.is_downloaded,
                "created_at": stock.created_at,
                "updated_at": stock.updated_at,
            }
            for stock in stocks
        ]

        print(f"✅ 매매 종목 조회 완료: {len(result)}건 (전체: {total}건)")

        return {
            "data": result,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    except Exception as e:
        print(f"❌ 매매 종목 조회 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"매매 종목 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{stock_code}")
def get_trading_stock(
    stock_code: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """특정 매매 종목 조회"""
    stock = db.query(TradingStock).filter(
        TradingStock.stock_code == stock_code
    ).first()

    if not stock:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다")

    return {
        "id": stock.id,
        "stock_code": stock.stock_code,
        "stock_name": stock.stock_name,
        "is_downloaded": stock.is_downloaded,
        "created_at": stock.created_at,
        "updated_at": stock.updated_at,
    }
