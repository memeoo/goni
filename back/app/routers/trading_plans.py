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


@router.post("/trades/sync")
async def sync_recent_trades(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    최근 거래 기록을 키움증권 API에서 조회하여 Trading 테이블에 동기화

    - 새로운 매매 기록만 추가 (중복 체크: order_no 기반)
    - 기존 기록은 업데이트하지 않음

    Args:
        limit (int): 조회할 거래 건수 (기본값: 20건)

    Returns:
        Dict: 동기화 결과 (추가된 건수, 중복 건수 등)
    """
    try:
        # 사용자의 키움 API 설정 확인
        if not current_user.app_key or not current_user.app_secret:
            return {
                "status": "warning",
                "message": "키움증권 API 정보가 설정되지 않았습니다. 프로필 페이지에서 설정해주세요.",
                "synced_count": 0,
                "duplicate_count": 0,
                "total_count": 0
            }

        kiwoom_app_key = current_user.app_key
        kiwoom_secret_key = current_user.app_secret

        # .env 파일에서 계좌번호와 Mock 설정만 로드
        from dotenv import load_dotenv
        analyze_env_path = os.path.join(os.path.dirname(__file__), '../../../analyze/.env')
        load_dotenv(analyze_env_path)

        kiwoom_account_no = os.getenv('KIWOOM_ACCOUNT_NO')
        kiwoom_use_mock = os.getenv('KIWOOM_USE_MOCK', 'false').lower() == 'true'

        if not kiwoom_account_no:
            raise HTTPException(
                status_code=500,
                detail="계좌번호가 설정되지 않았습니다."
            )

        try:
            # kiwoom.py 모듈 import 및 API 인스턴스 생성
            from lib.kiwoom import KiwoomAPI

            print(f"🔍 매매기록 동기화 시작: 최근 {limit}건")

            api = KiwoomAPI(
                app_key=kiwoom_app_key,
                secret_key=kiwoom_secret_key,
                account_no=kiwoom_account_no,
                use_mock=kiwoom_use_mock
            )

            # 매매 내역 조회 (최근 30일에서 limit 개수만큼 조회)
            trades = api.get_recent_trades(days=30)

            if not trades:
                print(f"⚠️ 조회된 매매내역이 없습니다.")
                return {
                    "status": "success",
                    "message": "조회된 매매내역이 없습니다.",
                    "synced_count": 0,
                    "duplicate_count": 0,
                    "total_count": 0
                }

            # 최근 순서로 limit 개만 선택 (매매 기록은 최신순으로 정렬되어 있음)
            trades = trades[:limit]
            print(f"✅ 매매내역 조회 완료: {len(trades)}건")

            synced_count = 0  # 새로 추가된 건수
            duplicate_count = 0  # 중복 건수

            # 트레이딩 레코드 동기화
            for trade in trades:
                order_no = trade.get('order_no', '')

                # 1. order_no가 있으면 중복 체크
                if order_no:
                    existing = db.query(models.Trading).filter(
                        models.Trading.order_no == order_no,
                        models.Trading.user_id == current_user.id
                    ).first()

                    if existing:
                        print(f"⏭️ 중복 기록 스킵: {order_no}")
                        duplicate_count += 1
                        continue

                # 2. 새로운 레코드 생성
                try:
                    # 날짜 시간 변환 (YYYYMMDDHHmmss -> datetime)
                    datetime_str = trade.get('datetime', '')
                    if len(datetime_str) == 14:
                        from datetime import datetime as dt
                        executed_at = dt.strptime(datetime_str, '%Y%m%d%H%M%S')
                    else:
                        from datetime import datetime as dt
                        executed_at = dt.now()

                    # trade_type 변환 ('매수' -> 'buy', '매도' -> 'sell')
                    trade_type_raw = trade.get('trade_type', '').strip()
                    if '매수' in trade_type_raw:
                        trade_type = 'buy'
                    elif '매도' in trade_type_raw:
                        trade_type = 'sell'
                    else:
                        trade_type = 'buy'  # 기본값

                    # 새 거래 레코드 생성
                    new_trading = models.Trading(
                        user_id=current_user.id,
                        executed_at=executed_at,
                        trade_type=trade_type,
                        order_no=order_no if order_no else None,
                        stock_name=trade.get('stock_name', ''),
                        stock_code=trade.get('stock_code', ''),
                        executed_price=float(trade.get('price', 0)),
                        executed_quantity=int(trade.get('quantity', 0)),
                        executed_amount=int(float(trade.get('price', 0)) * int(trade.get('quantity', 0))),
                        broker='kiwoom'
                    )

                    db.add(new_trading)
                    synced_count += 1
                    print(f"✅ 새 거래 추가: {trade['stock_name']} {trade_type} {order_no}")

                except Exception as record_error:
                    print(f"❌ 레코드 생성 오류: {record_error}")
                    continue

            # 모든 변경사항 커밋
            db.commit()

            print(f"✅ 동기화 완료: {synced_count}건 추가, {duplicate_count}건 중복")

            return {
                "status": "success",
                "message": f"{synced_count}건의 새로운 매매기록이 추가되었습니다.",
                "synced_count": synced_count,
                "duplicate_count": duplicate_count,
                "total_count": len(trades)
            }

        except ImportError as import_error:
            print(f"❌ 모듈 import 오류: {import_error}")
            raise HTTPException(
                status_code=500,
                detail=f"키움증권 API 모듈을 불러올 수 없습니다: {str(import_error)}"
            )
        except HTTPException:
            raise
        except Exception as api_error:
            print(f"❌ 키움증권 API 오류: {api_error}")
            import traceback
            traceback.print_exc()
            db.rollback()
            return {
                "status": "error",
                "message": f"매매기록 동기화 중 오류가 발생했습니다: {str(api_error)}",
                "synced_count": 0,
                "duplicate_count": 0,
                "total_count": 0
            }

    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return {
            "status": "error",
            "message": f"매매기록 동기화 중 예상치 못한 오류가 발생했습니다: {str(e)}",
            "synced_count": 0,
            "duplicate_count": 0,
            "total_count": 0
        }


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