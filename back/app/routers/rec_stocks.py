"""
추천 종목(rec_stocks) API 라우터

목적: 추천 알고리즘에 의해 추천되는 종목들을 관리하는 API 엔드포인트 제공
기능: CRUD 작업, 날짜별/알고리즘별 조회, 페이지네이션 지원
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List, Optional
import logging

from app.database import get_db
from app.models import RecStock, Algorithm
from app import schemas

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/rec-stocks",
    tags=["rec-stocks"]
)


@router.post("", response_model=schemas.RecStockWithAlgorithm)
def create_rec_stock(
    rec_stock: schemas.RecStockCreate,
    db: Session = Depends(get_db)
):
    """
    추천 종목 생성

    - **stock_name**: 종목명 (필수)
    - **stock_code**: 종목코드 (필수)
    - **recommendation_date**: 추천날짜 (필수)
    - **algorithm_id**: 추천 알고리즘 ID (필수)
    - **closing_price**: 당일 종가 (필수)
    - **change_rate**: 전일비 (%) (선택)
    """
    # 알고리즘 존재 여부 확인
    algorithm = db.query(Algorithm).filter(Algorithm.id == rec_stock.algorithm_id).first()
    if not algorithm:
        logger.error(f"알고리즘 ID {rec_stock.algorithm_id} 존재하지 않음")
        raise HTTPException(status_code=404, detail="Algorithm not found")

    # 추천 종목 생성
    db_rec_stock = RecStock(
        stock_name=rec_stock.stock_name,
        stock_code=rec_stock.stock_code,
        recommendation_date=rec_stock.recommendation_date,
        algorithm_id=rec_stock.algorithm_id,
        closing_price=rec_stock.closing_price,
        change_rate=rec_stock.change_rate
    )

    db.add(db_rec_stock)
    db.commit()
    db.refresh(db_rec_stock)

    logger.info(f"추천 종목 생성: {rec_stock.stock_code}({rec_stock.stock_name})")

    return db_rec_stock


# 더 구체적인 경로들을 먼저 정의 (/{id}보다 먼저)
@router.get("/latest/{days}", response_model=dict)
def get_latest_rec_stocks(
    days: int = Path(ge=1, le=30, description="최근 N일"),
    algorithm_id: Optional[int] = Query(None, description="알고리즘 ID 필터"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    최근 N일간의 추천 종목 조회

    - **days**: 최근 N일 (기본값: 7, 최대: 30)
    - **algorithm_id**: 특정 알고리즘으로 추가 필터링 (선택)
    """
    from datetime import datetime, timedelta

    start_date = date.today() - timedelta(days=days)

    query = db.query(RecStock).filter(RecStock.recommendation_date >= start_date)

    if algorithm_id:
        query = query.filter(RecStock.algorithm_id == algorithm_id)

    total = query.count()
    rec_stocks = query.order_by(RecStock.recommendation_date.desc()).offset(skip).limit(limit).all()

    logger.info(f"최근 {days}일 추천 종목 조회: 전체 {total}개, 반환 {len(rec_stocks)}개")

    return {
        "data": rec_stocks,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/algorithm/{algorithm_id}", response_model=dict)
def get_rec_stocks_by_algorithm(
    algorithm_id: int,
    recommendation_date: Optional[date] = Query(None, description="추천날짜 필터"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    특정 알고리즘으로 추천된 종목 목록 조회

    - **algorithm_id**: 알고리즘 ID (필수)
    - **recommendation_date**: 추천날짜로 추가 필터링 (선택)
    """
    # 알고리즘 존재 여부 확인
    algorithm = db.query(Algorithm).filter(Algorithm.id == algorithm_id).first()
    if not algorithm:
        logger.warning(f"알고리즘 ID {algorithm_id} 존재하지 않음")
        raise HTTPException(status_code=404, detail="Algorithm not found")

    query = db.query(RecStock).filter(RecStock.algorithm_id == algorithm_id)

    if recommendation_date:
        query = query.filter(RecStock.recommendation_date == recommendation_date)

    total = query.count()
    rec_stocks = query.order_by(RecStock.recommendation_date.desc()).offset(skip).limit(limit).all()

    logger.info(f"알고리즘 {algorithm_id} 추천 종목 조회: 전체 {total}개, 반환 {len(rec_stocks)}개")

    return {
        "data": rec_stocks,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/date/{recommendation_date}", response_model=dict)
def get_rec_stocks_by_date(
    recommendation_date: date,
    algorithm_id: Optional[int] = Query(None, description="알고리즘 ID 필터"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    특정 날짜의 추천 종목 목록 조회

    - **recommendation_date**: 추천날짜 (필수, YYYY-MM-DD 형식)
    - **algorithm_id**: 특정 알고리즘으로 추가 필터링 (선택)
    """
    query = db.query(RecStock).filter(RecStock.recommendation_date == recommendation_date)

    if algorithm_id:
        query = query.filter(RecStock.algorithm_id == algorithm_id)

    total = query.count()
    rec_stocks = query.order_by(RecStock.algorithm_id).offset(skip).limit(limit).all()

    logger.info(f"날짜 {recommendation_date} 추천 종목 조회: 전체 {total}개, 반환 {len(rec_stocks)}개")

    return {
        "data": rec_stocks,
        "total": total,
        "skip": skip,
        "limit": limit
    }


# 일반 경로들을 뒤에 정의
@router.get("/{rec_stock_id}", response_model=schemas.RecStockWithAlgorithm)
def get_rec_stock(
    rec_stock_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 추천 종목 조회

    - **rec_stock_id**: 추천 종목 ID (필수)
    """
    rec_stock = db.query(RecStock).filter(RecStock.id == rec_stock_id).first()
    if not rec_stock:
        logger.warning(f"추천 종목 ID {rec_stock_id} 존재하지 않음")
        raise HTTPException(status_code=404, detail="Recommended stock not found")

    return rec_stock


@router.get("", response_model=dict)
def get_rec_stocks(
    stock_code: Optional[str] = Query(None, description="종목코드"),
    algorithm_id: Optional[int] = Query(None, description="알고리즘 ID"),
    recommendation_date: Optional[date] = Query(None, description="추천날짜 (YYYY-MM-DD)"),
    from_date: Optional[date] = Query(None, description="추천날짜 범위 시작 (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="추천날짜 범위 종료 (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0, description="스킵 개수"),
    limit: int = Query(20, ge=1, le=100, description="조회 개수"),
    db: Session = Depends(get_db)
):
    """
    추천 종목 목록 조회 (필터링 및 페이지네이션 지원)

    **필터 조건**:
    - **stock_code**: 특정 종목코드로 조회
    - **algorithm_id**: 특정 알고리즘으로 추천된 종목 조회
    - **recommendation_date**: 특정 날짜의 추천 종목 조회
    - **from_date, to_date**: 날짜 범위로 추천 종목 조회

    **페이지네이션**:
    - **skip**: 스킵할 레코드 개수 (기본값: 0)
    - **limit**: 조회할 레코드 개수 (기본값: 20, 최대: 100)

    **응답 형식**:
    ```json
    {
        "data": [...],
        "total": 100,
        "skip": 0,
        "limit": 20
    }
    ```
    """
    query = db.query(RecStock)

    # 필터 적용
    if stock_code:
        query = query.filter(RecStock.stock_code == stock_code)

    if algorithm_id:
        query = query.filter(RecStock.algorithm_id == algorithm_id)

    if recommendation_date:
        query = query.filter(RecStock.recommendation_date == recommendation_date)

    if from_date and to_date:
        query = query.filter(RecStock.recommendation_date.between(from_date, to_date))
    elif from_date:
        query = query.filter(RecStock.recommendation_date >= from_date)
    elif to_date:
        query = query.filter(RecStock.recommendation_date <= to_date)

    # 전체 개수 조회
    total = query.count()

    # 페이지네이션 적용
    rec_stocks = query.order_by(RecStock.recommendation_date.desc()).offset(skip).limit(limit).all()

    logger.info(f"추천 종목 목록 조회: 전체 {total}개, 반환 {len(rec_stocks)}개")

    return {
        "data": rec_stocks,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.put("/{rec_stock_id}", response_model=schemas.RecStockWithAlgorithm)
def update_rec_stock(
    rec_stock_id: int,
    rec_stock_update: schemas.RecStockUpdate,
    db: Session = Depends(get_db)
):
    """
    추천 종목 수정

    수정 가능한 필드:
    - **closing_price**: 당일 종가
    - **change_rate**: 전일비 (%)
    """
    db_rec_stock = db.query(RecStock).filter(RecStock.id == rec_stock_id).first()
    if not db_rec_stock:
        logger.warning(f"추천 종목 ID {rec_stock_id} 존재하지 않음")
        raise HTTPException(status_code=404, detail="Recommended stock not found")

    # 수정 가능한 필드만 업데이트
    if rec_stock_update.closing_price is not None:
        db_rec_stock.closing_price = rec_stock_update.closing_price

    if rec_stock_update.change_rate is not None:
        db_rec_stock.change_rate = rec_stock_update.change_rate

    db_rec_stock.updated_at = datetime.utcnow()

    db.add(db_rec_stock)
    db.commit()
    db.refresh(db_rec_stock)

    logger.info(f"추천 종목 수정: ID {rec_stock_id}")

    return db_rec_stock


@router.delete("/{rec_stock_id}")
def delete_rec_stock(
    rec_stock_id: int,
    db: Session = Depends(get_db)
):
    """
    추천 종목 삭제

    - **rec_stock_id**: 추천 종목 ID (필수)
    """
    db_rec_stock = db.query(RecStock).filter(RecStock.id == rec_stock_id).first()
    if not db_rec_stock:
        logger.warning(f"추천 종목 ID {rec_stock_id} 존재하지 않음")
        raise HTTPException(status_code=404, detail="Recommended stock not found")

    stock_code = db_rec_stock.stock_code
    stock_name = db_rec_stock.stock_name

    db.delete(db_rec_stock)
    db.commit()

    logger.info(f"추천 종목 삭제: {stock_code}({stock_name})")

    return {"message": "Recommended stock deleted successfully"}
