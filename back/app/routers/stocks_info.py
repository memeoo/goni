"""
종목정보 조회 API (ka10099)

키움증권 Open REST API의 ka10099 TR을 사용하여 종목정보를 조회하고
stocks_info 테이블에 저장/조회합니다.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import StocksInfo, User
from app.schemas import StocksInfo as StocksInfoSchema, StocksInfoCreate
from app.routers.auth import get_current_user

# 부모 디렉토리를 path에 추가 (analyze 모듈 임포트를 위해)
sys.path.insert(0, '/home/ubuntu/goni')

from analyze.lib.kiwoom import KiwoomAPI

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stocks-info", tags=["stocks-info"])


@router.get("/")
def get_stocks_info(
    market_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    DB에 저장된 종목정보 조회

    Args:
        market_code: 마켓코드로 필터링 (선택)
                    '0': 코스피
                    '10': 코스닥
                    등등...
        skip: 시작 위치 (페이징)
        limit: 조회 개수 (페이징)

    Returns:
        list: 종목정보 리스트
        {
            "data": [
                {
                    "id": 1,
                    "code": "005930",
                    "name": "삼성전자",
                    "list_count": "0000000123759593",
                    "audit_info": "정상",
                    "reg_day": "20091204",
                    "last_price": "00000197",
                    "state": "증거금100%",
                    "market_code": "0",
                    "market_name": "코스피",
                    "up_name": "",
                    "up_size_name": "",
                    "company_class_name": "",
                    "order_warning": "0",
                    "nxt_enable": "Y",
                    "created_at": "2025-11-09T12:30:00",
                    "updated_at": "2025-11-09T12:30:00"
                },
                ...
            ],
            "total": 10,
            "skip": 0,
            "limit": 100
        }
    """
    query = db.query(StocksInfo)

    # market_code로 필터링
    if market_code:
        query = query.filter(StocksInfo.market_code == market_code)

    total = query.count()
    stocks = query.offset(skip).limit(limit).all()

    return {
        "data": [StocksInfoSchema.from_orm(stock) for stock in stocks],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/sync/{market_code}")
def sync_stocks_info(
    market_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    키움 API ka10099를 사용하여 종목정보 조회 및 DB에 저장

    Args:
        market_code: 시장구분
                    '0': 코스피 (기본값)
                    '10': 코스닥
                    '3': ELW
                    '8': ETF
                    '30': K-OTC
                    '50': 코넥스
                    '5': 신주인수권
                    '4': 뮤추얼펀드
                    '6': 리츠
                    '9': 하이일드

    Returns:
        dict: 동기화 결과
        {
            "status": "success",
            "message": "10개의 종목이 저장되었습니다.",
            "added": 5,
            "updated": 3,
            "duplicated": 2,
            "total": 10
        }
    """
    # 사용자의 키움 API 인증정보 확인
    if not current_user.app_key or not current_user.app_secret:
        raise HTTPException(
            status_code=400,
            detail="키움증권 API 인증정보가 설정되지 않았습니다. 프로필 페이지에서 APP KEY와 APP SECRET을 등록해주세요."
        )

    try:
        # 키움 API 인스턴스 생성
        kiwoom_api = KiwoomAPI(
            app_key=current_user.app_key,
            secret_key=current_user.app_secret,
            account_no="",  # 종목정보 조회에는 계좌번호 불필요
            use_mock=False
        )

        # ka10099 API 호출
        logger.info(f"키움 API ka10099 호출: market_code={market_code}")
        result = kiwoom_api.get_stocks_info(mrkt_tp=market_code)

        if not result:
            raise HTTPException(
                status_code=400,
                detail=f"키움 API 호출 실패: market_code={market_code}"
            )

        # 응답 데이터 파싱
        stocks_list = result.get('list', [])

        added_count = 0
        updated_count = 0
        duplicated_count = 0

        # DB에 저장/업데이트
        for stock_data in stocks_list:
            try:
                code = stock_data.get('code', '').strip()

                if not code:
                    logger.warning(f"종목코드가 없는 데이터 스킵: {stock_data}")
                    continue

                # 기존 데이터 확인
                existing_stock = db.query(StocksInfo).filter(
                    StocksInfo.code == code
                ).first()

                if existing_stock:
                    # 기존 데이터 업데이트
                    existing_stock.name = stock_data.get('name', '')
                    existing_stock.list_count = stock_data.get('listCount', '')
                    existing_stock.audit_info = stock_data.get('auditInfo', '')
                    existing_stock.reg_day = stock_data.get('regDay', '')
                    existing_stock.last_price = stock_data.get('lastPrice', '')
                    existing_stock.state = stock_data.get('state', '')
                    existing_stock.market_code = stock_data.get('marketCode', '')
                    existing_stock.market_name = stock_data.get('marketName', '')
                    existing_stock.up_name = stock_data.get('upName', '')
                    existing_stock.up_size_name = stock_data.get('upSizeName', '')
                    existing_stock.company_class_name = stock_data.get('companyClassName', '')
                    existing_stock.order_warning = stock_data.get('orderWarning', '')
                    existing_stock.nxt_enable = stock_data.get('nxtEnable', '')
                    existing_stock.updated_at = datetime.utcnow()

                    updated_count += 1
                    logger.debug(f"종목정보 업데이트: {code} ({existing_stock.name})")
                else:
                    # 새 데이터 추가
                    new_stock = StocksInfo(
                        code=code,
                        name=stock_data.get('name', ''),
                        list_count=stock_data.get('listCount', ''),
                        audit_info=stock_data.get('auditInfo', ''),
                        reg_day=stock_data.get('regDay', ''),
                        last_price=stock_data.get('lastPrice', ''),
                        state=stock_data.get('state', ''),
                        market_code=stock_data.get('marketCode', ''),
                        market_name=stock_data.get('marketName', ''),
                        up_name=stock_data.get('upName', ''),
                        up_size_name=stock_data.get('upSizeName', ''),
                        company_class_name=stock_data.get('companyClassName', ''),
                        order_warning=stock_data.get('orderWarning', ''),
                        nxt_enable=stock_data.get('nxtEnable', ''),
                    )
                    db.add(new_stock)
                    added_count += 1
                    logger.debug(f"종목정보 추가: {code} ({stock_data.get('name', '')})")

            except Exception as e:
                logger.error(f"종목정보 저장 실패: {stock_data}, Error: {e}")
                duplicated_count += 1

        # DB 커밋
        db.commit()

        total_count = len(stocks_list)
        logger.info(
            f"키움 API 동기화 완료: "
            f"시장={market_code}, "
            f"추가={added_count}, "
            f"업데이트={updated_count}, "
            f"총 조회={total_count}"
        )

        return {
            "status": "success",
            "message": f"{total_count}개의 종목정보가 처리되었습니다.",
            "added": added_count,
            "updated": updated_count,
            "duplicated": duplicated_count,
            "total": total_count
        }

    except Exception as e:
        logger.error(f"종목정보 동기화 실패: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"종목정보 동기화 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/search")
def search_stocks_info(
    q: Optional[str] = None,
    market_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    종목정보 검색 (종목코드 또는 종목명)

    Args:
        q: 검색 키워드 (종목코드 또는 종목명)
        market_code: 마켓코드로 필터링 (선택)
        skip: 시작 위치 (페이징)
        limit: 조회 개수 (페이징)

    Returns:
        dict: 검색 결과
        {
            "data": [...],
            "total": 5,
            "skip": 0,
            "limit": 50
        }
    """
    query = db.query(StocksInfo)

    # 검색어로 필터링 (종목코드 또는 종목명)
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            (StocksInfo.code.ilike(search_term)) |
            (StocksInfo.name.ilike(search_term))
        )

    # market_code로 필터링
    if market_code:
        query = query.filter(StocksInfo.market_code == market_code)

    total = query.count()
    stocks = query.offset(skip).limit(limit).all()

    return {
        "data": [StocksInfoSchema.from_orm(stock) for stock in stocks],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{code}")
def get_stock_info_by_code(
    code: str,
    db: Session = Depends(get_db)
):
    """
    종목코드로 종목정보 조회

    Args:
        code: 종목코드

    Returns:
        dict: 종목정보 데이터
    """
    stock = db.query(StocksInfo).filter(StocksInfo.code == code).first()

    if not stock:
        raise HTTPException(
            status_code=404,
            detail=f"종목정보를 찾을 수 없습니다: {code}"
        )

    return StocksInfoSchema.from_orm(stock)
