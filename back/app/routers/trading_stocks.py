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
    days: int = 60
):
    """
    Kiwoom API에서 실제 매매 기록을 조회하여 trading_stocks 테이블에 동기화

    Args:
        days: 조회할 일수 (기본값: 60일)

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
            try:
                # 날짜시간 파싱
                datetime_str = trade['datetime']  # YYYYMMDDHHmmss 형식
                executed_at = datetime.strptime(datetime_str, '%Y%m%d%H%M%S')

                order_no = trade.get('order_no', '')

                # 중복 확인 로직
                # 1단계: order_no가 있으면 order_no 기준으로 중복 체크
                if order_no:
                    existing_trade = db.query(TradingHistory).filter(
                        TradingHistory.user_id == current_user.id,
                        TradingHistory.order_no == order_no,
                        TradingHistory.stock_code == trade['stock_code']
                    ).first()
                else:
                    # 2단계: order_no가 없으면 (stock_code + executed_at + price + quantity)로 중복 체크
                    # 같은 시간에 같은 가격으로 같은 수량 매매한 경우
                    existing_trade = db.query(TradingHistory).filter(
                        TradingHistory.user_id == current_user.id,
                        TradingHistory.stock_code == trade['stock_code'],
                        TradingHistory.executed_at == executed_at,
                        TradingHistory.executed_price == trade['price'],
                        TradingHistory.executed_quantity == trade['quantity']
                    ).first()

                # 중복이 아니면 저장
                if not existing_trade:
                    new_trade = TradingHistory(
                        user_id=current_user.id,
                        executed_at=executed_at,
                        trade_type=trade['trade_type'],
                        order_no=order_no,
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
                import traceback
                traceback.print_exc()
                continue

        db.commit()
        print(f"✅ TradingHistory 저장 완료: {added_trades}건 추가")

        # 2단계: trading_stocks 테이블에 종목 정보 저장 및 업데이트
        # 종목별로 가장 최근의 order_no를 추적 (datetime 기준 최신순)
        unique_stocks = {}
        for trade in kiwoom_trades:
            stock_code = trade['stock_code']
            if stock_code not in unique_stocks:
                unique_stocks[stock_code] = {
                    'stock_code': stock_code,
                    'stock_name': trade['stock_name'],
                    'latest_orderno': trade.get('order_no', ''),
                    'datetime': trade.get('datetime', '')
                }
            else:
                # 더 최근의 거래(datetime이 더 큰 값)가 있으면 업데이트
                if trade.get('datetime', '') > unique_stocks[stock_code]['datetime']:
                    unique_stocks[stock_code]['latest_orderno'] = trade.get('order_no', '')
                    unique_stocks[stock_code]['datetime'] = trade.get('datetime', '')

        added_stocks = 0
        updated_stocks = 0

        for stock_code, stock_info in unique_stocks.items():
            existing_stock = db.query(TradingStock).filter(
                TradingStock.stock_code == stock_code
            ).first()

            if existing_stock:
                # 기존 종목 - stock_name과 latest_orderno 업데이트 (is_downloaded는 유지)
                existing_stock.stock_name = stock_info['stock_name']
                existing_stock.latest_orderno = stock_info['latest_orderno']
                existing_stock.updated_at = datetime.utcnow()
                updated_stocks += 1
                print(f"  ✏️ {stock_info['stock_name']}({stock_code}) 업데이트 (latest_orderno: {stock_info['latest_orderno']})")
            else:
                # 신규 종목 추가
                new_stock = TradingStock(
                    stock_name=stock_info['stock_name'],
                    stock_code=stock_code,
                    latest_orderno=stock_info['latest_orderno'],
                    is_downloaded=False
                )
                db.add(new_stock)
                added_stocks += 1
                print(f"  ✨ {stock_info['stock_name']}({stock_code}) 추가 (latest_orderno: {stock_info['latest_orderno']})")

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


@router.get("")
@router.get("/")
def get_trading_stocks(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    현재 사용자가 거래한 매매 종목 목록 조회 (최근 거래순 정렬)

    종목들은 가장 최근 매매기록 순서대로 정렬됩니다.

    Query Parameters:
    - skip: 오프셋 (기본값: 0)
    - limit: 조회 개수 (기본값: 100)
    """
    try:
        # 현재 사용자의 거래 기록에 있는 종목만 조회 (사용자별 필터링)
        # 가장 최근 거래 시간 기준으로 정렬
        from sqlalchemy import func

        query = db.query(
            TradingStock,
            func.max(TradingHistory.executed_at).label('latest_trade_at')
        ).join(
            TradingHistory,
            TradingStock.stock_code == TradingHistory.stock_code
        ).filter(
            TradingHistory.user_id == current_user.id
        ).group_by(
            TradingStock.id
        ).order_by(
            func.max(TradingHistory.executed_at).desc()  # 최근 거래순으로 정렬
        )

        # 전체 개수 (페이징 전)
        total = query.count()

        # 페이징 적용
        stocks_with_dates = query.offset(skip).limit(limit).all()

        # TradingStock 객체만 추출
        stocks = [item[0] for item in stocks_with_dates]

        result = []
        for stock in stocks:
            # 각 종목별 최근 거래 3건 조회
            recent_trades = db.query(TradingHistory).filter(
                TradingHistory.user_id == current_user.id,
                TradingHistory.stock_code == stock.stock_code
            ).order_by(
                TradingHistory.executed_at.desc()
            ).limit(3).all()

            # 거래 정보 포맷팅
            trades_info = [
                {
                    "trade_type": trade.trade_type,
                    "executed_price": trade.executed_price,
                    "executed_quantity": trade.executed_quantity,
                    "executed_at": trade.executed_at.strftime('%Y-%m-%d') if trade.executed_at else None
                }
                for trade in recent_trades
            ]

            result.append({
                "id": stock.id,
                "stock_code": stock.stock_code,
                "stock_name": stock.stock_name,
                "is_downloaded": stock.is_downloaded,
                "avg_prc": stock.avg_prc,  # 평균단가
                "rmnd_qty": stock.rmnd_qty,  # 보유수량
                "pur_amt": stock.pur_amt,  # 매입금액
                "created_at": stock.created_at,
                "updated_at": stock.updated_at,
                "recent_trades": trades_info  # 최근 거래 3건 추가
            })

        print(f"✅ 매매 종목 조회 완료: {len(result)}건 (사용자 {current_user.id}의 거래 종목, 최근순 정렬, 전체: {total}건)")

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


@router.post("/{stock_code}/sync-history")
def sync_stock_trading_history(
    stock_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    특정 종목의 거래기록을 스마트하게 동기화 (증분 동기화)

    동기화 전략:
    1. TradingHistory에서 해당 종목의 가장 최근 order_no 조회
    2. TradingStock의 latest_orderno와 비교
    3. 같으면: 이미 최신 상태 → 동기화 스킵
    4. 다르면:
       - is_downloaded = false: 60일 전체 조회 (첫 다운로드)
       - is_downloaded = true: 최근 거래만 조회 (증분 동기화)

    Args:
        stock_code: 종목코드 (6자리)

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

        print(f"🔄 종목 {stock_code} 동기화 시작... (사용자: {current_user.id})")

        # 1단계: TradingStock 조회
        trading_stock = db.query(TradingStock).filter(
            TradingStock.stock_code == stock_code
        ).first()

        if not trading_stock:
            raise HTTPException(
                status_code=404,
                detail=f"종목 {stock_code}을 찾을 수 없습니다"
            )

        # 2단계: TradingHistory에서 해당 종목의 가장 최근 order_no 조회
        latest_db_trade = db.query(TradingHistory).filter(
            TradingHistory.user_id == current_user.id,
            TradingHistory.stock_code == stock_code
        ).order_by(TradingHistory.executed_at.desc()).first()

        latest_db_orderno = latest_db_trade.order_no if latest_db_trade else None
        latest_stock_orderno = trading_stock.latest_orderno

        print(f"  DB latest_orderno: {latest_db_orderno}")
        print(f"  Stock latest_orderno: {latest_stock_orderno}")
        print(f"  is_downloaded: {trading_stock.is_downloaded}")

        # 3단계: 동기화 필요 여부 판단
        if latest_db_orderno == latest_stock_orderno and latest_stock_orderno:
            print(f"✅ {stock_code}는 이미 최신 상태입니다. 동기화 스킵")
            return {
                "message": f"{stock_code}는 이미 최신 상태입니다",
                "stock_code": stock_code,
                "sync_type": "skipped",
                "added_trades": 0
            }

        # 4단계: Kiwoom API로 거래기록 조회
        kiwoom_api = KiwoomAPI(
            app_key=current_user.app_key,
            secret_key=current_user.app_secret,
            account_no="",
            use_mock=False
        )

        # is_downloaded 상태에 따라 조회 기간 결정
        if trading_stock.is_downloaded:
            # 기존에 다운로드됨 → 최근 거래만 조회 (7일)
            sync_type = "incremental"
            days_to_fetch = 7
            print(f"  증분 동기화 실행 (최근 7일)")
        else:
            # 처음 다운로드 → 전체 기간 조회 (60일)
            sync_type = "full"
            days_to_fetch = 60
            print(f"  전체 다운로드 실행 (최근 60일)")

        kiwoom_trades = kiwoom_api.get_recent_trades(days=days_to_fetch)

        if not kiwoom_trades:
            print(f"⚠️ {stock_code}의 거래기록이 없습니다")
            return {
                "message": f"{stock_code} 종목의 조회된 거래기록이 없습니다",
                "stock_code": stock_code,
                "sync_type": sync_type,
                "added_trades": 0
            }

        # 해당 stock_code의 거래기록만 필터링
        filtered_trades = [t for t in kiwoom_trades if t['stock_code'] == stock_code]
        print(f"✅ Kiwoom API에서 {stock_code}의 거래기록 조회 완료: {len(filtered_trades)}건")

        if not filtered_trades:
            return {
                "message": f"{stock_code} 종목의 거래기록이 없습니다",
                "stock_code": stock_code,
                "sync_type": sync_type,
                "added_trades": 0
            }

        # 5단계: TradingHistory에 거래기록 저장
        added_trades = 0
        for trade in filtered_trades:
            try:
                # 날짜시간 파싱
                datetime_str = trade['datetime']  # YYYYMMDDHHmmss 형식
                executed_at = datetime.strptime(datetime_str, '%Y%m%d%H%M%S')
                order_no = trade.get('order_no', '')

                # 중복 확인 로직
                if order_no:
                    existing_trade = db.query(TradingHistory).filter(
                        TradingHistory.user_id == current_user.id,
                        TradingHistory.order_no == order_no,
                        TradingHistory.stock_code == trade['stock_code']
                    ).first()
                else:
                    existing_trade = db.query(TradingHistory).filter(
                        TradingHistory.user_id == current_user.id,
                        TradingHistory.stock_code == trade['stock_code'],
                        TradingHistory.executed_at == executed_at,
                        TradingHistory.executed_price == trade['price'],
                        TradingHistory.executed_quantity == trade['quantity']
                    ).first()

                # 중복이 아니면 저장
                if not existing_trade:
                    new_trade = TradingHistory(
                        user_id=current_user.id,
                        executed_at=executed_at,
                        trade_type=trade['trade_type'],
                        order_no=order_no,
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
                print(f"⚠️ 거래기록 저장 실패: {trade.get('stock_name')} - {e}")
                import traceback
                traceback.print_exc()
                continue

        db.commit()
        print(f"✅ {stock_code} 거래기록 저장 완료: {added_trades}건 추가")

        # 6단계: TradingStock 업데이트
        # 해당 종목의 가장 최근 order_no 찾기
        latest_trade = None
        latest_datetime = ''
        for trade in filtered_trades:
            trade_datetime = trade.get('datetime', '')
            if trade_datetime > latest_datetime:
                latest_datetime = trade_datetime
                latest_trade = trade

        if latest_trade:
            trading_stock.latest_orderno = latest_trade.get('order_no', '')
            trading_stock.is_downloaded = True
            trading_stock.updated_at = datetime.utcnow()
            db.commit()
            print(f"✅ {stock_code} TradingStock 업데이트")
            print(f"  - latest_orderno: {trading_stock.latest_orderno}")
            print(f"  - is_downloaded: True")

        return {
            "message": f"{stock_code} 종목의 거래기록 동기화 완료",
            "stock_code": stock_code,
            "sync_type": sync_type,
            "added_trades": added_trades
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 종목별 거래기록 동기화 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"거래기록 동기화 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/sync-account-evaluation")
def sync_account_evaluation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    계좌평가현황을 조회하여 trading_stocks 테이블의 평균단가, 보유수량, 매입금액을 업데이트합니다.

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

        print(f"🔄 계좌평가현황 조회 중... (사용자: {current_user.id})")

        # Kiwoom API 인스턴스 생성
        kiwoom_api = KiwoomAPI(
            app_key=current_user.app_key,
            secret_key=current_user.app_secret,
            account_no="",  # 계정번호는 API 응답에서 자동 처리
            use_mock=False
        )

        # 계좌평가현황 조회
        account_eval = kiwoom_api.get_account_evaluation(qry_tp='0', dmst_stex_tp='KRX')

        if not account_eval:
            print("⚠️ 계좌평가현황 조회 실패")
            return {
                "message": "계좌평가현황 조회 실패",
                "updated_count": 0
            }

        # 보유 종목 정보 추출
        stocks_info = account_eval.get('stk_acnt_evlt_prst', [])
        print(f"✅ 계좌평가현황 조회 완료: {len(stocks_info)}개 종목")

        # trading_stocks 테이블 업데이트
        updated_count = 0
        for stock_info in stocks_info:
            stock_code = stock_info.get('stk_cd', '')
            if not stock_code:
                continue

            # 기존 종목 조회
            existing_stock = db.query(TradingStock).filter(
                TradingStock.stock_code == stock_code
            ).first()

            if existing_stock:
                # 계좌평가현황의 정보로 업데이트
                existing_stock.avg_prc = stock_info.get('avg_prc')  # 평균단가
                existing_stock.rmnd_qty = int(stock_info.get('rmnd_qty', 0))  # 보유수량
                existing_stock.pur_amt = int(stock_info.get('pur_amt', 0))  # 매입금액
                existing_stock.updated_at = datetime.utcnow()
                updated_count += 1
                print(f"  ✏️ {stock_info.get('stk_nm')}({stock_code}) 업데이트 "
                      f"(평균단가: {existing_stock.avg_prc}원, 보유수량: {existing_stock.rmnd_qty}주)")
            else:
                # 새로운 종목 추가 (필요시)
                # trading_stocks에 없는 종목은 계좌평가현황에서도 보유하지 않으므로 스킵
                pass

        db.commit()
        print(f"✅ 계좌평가현황 동기화 완료: {updated_count}개 종목 업데이트")

        return {
            "message": "계좌평가현황 동기화 완료",
            "updated_count": updated_count,
            "total_stocks": len(stocks_info)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 계좌평가현황 동기화 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"계좌평가현황 동기화 중 오류가 발생했습니다: {str(e)}"
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
        "avg_prc": stock.avg_prc,
        "rmnd_qty": stock.rmnd_qty,
        "pur_amt": stock.pur_amt,
        "created_at": stock.created_at,
        "updated_at": stock.updated_at,
    }
