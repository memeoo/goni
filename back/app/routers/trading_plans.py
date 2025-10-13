from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import sys
import os

from app.database import get_database
from app import schemas
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
async def get_recent_trades(days: int = 10) -> Dict[str, Any]:
    """
    최근 N일간의 실제 매매 내역 조회 (키움증권 API)

    Args:
        days (int): 조회할 일수 (기본값: 10일)

    Returns:
        Dict: 매매 내역 리스트
    """
    try:
        # .env 파일 경로 설정
        from dotenv import load_dotenv
        analyze_env_path = os.path.join(os.path.dirname(__file__), '../../../analyze/.env')
        load_dotenv(analyze_env_path)

        # 환경변수에서 키움 API 설정 로드
        kiwoom_app_key = os.getenv('KIWOOM_APP_KEY')
        kiwoom_secret_key = os.getenv('KIWOOM_SECRET_KEY')
        kiwoom_account_no = os.getenv('KIWOOM_ACCOUNT_NO')
        kiwoom_use_mock = os.getenv('KIWOOM_USE_MOCK', 'false').lower() == 'true'

        if not all([kiwoom_app_key, kiwoom_secret_key, kiwoom_account_no]):
            raise HTTPException(
                status_code=500,
                detail="키움증권 API 설정이 없습니다. .env 파일을 확인해주세요."
            )

        try:
            # kiwoom.py 모듈 import 및 API 인스턴스 생성
            from lib.kiwoom import KiwoomAPI

            print(f"🔍 키움증권 매매내역 조회 시작: 최근 {days}일")

            api = KiwoomAPI(
                app_key=kiwoom_app_key,
                secret_key=kiwoom_secret_key,
                account_no=kiwoom_account_no,
                use_mock=kiwoom_use_mock
            )

            # 매매 내역 조회
            trades = api.get_recent_trades(days=days)

            if not trades:
                print(f"⚠️ 조회된 매매내역이 없습니다 (최근 {days}일)")
                return {
                    "days": days,
                    "data": [],
                    "total_records": 0
                }

            print(f"✅ 매매내역 조회 완료: {len(trades)}건")

            # 응답 데이터 포맷팅
            formatted_trades = []
            for trade in trades:
                formatted_trades.append({
                    'stock_code': trade['stock_code'],
                    'stock_name': trade['stock_name'],
                    'trade_type': trade['trade_type'],  # '매수' 또는 '매도'
                    'price': float(trade['price']),
                    'quantity': int(trade['quantity']),
                    'datetime': trade['datetime'],  # YYYYMMDDHHmmss
                    'order_no': trade.get('order_no', '')
                })

            return {
                "days": days,
                "data": formatted_trades,
                "total_records": len(formatted_trades)
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
            raise HTTPException(
                status_code=500,
                detail=f"매매내역 조회 중 오류가 발생했습니다: {str(api_error)}"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"매매내역 조회 중 오류가 발생했습니다: {str(e)}"
        )