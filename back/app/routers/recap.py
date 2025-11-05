from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import schemas, models
from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter(
    prefix="/api/recap",
    tags=["recap"]
)


# ===== GET 메서드 (읽기) - 가장 구체적인 경로부터 정의 =====

@router.get("/by-trading/{trading_id}", response_model=schemas.Recap)
def get_recap_by_trading(
    trading_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """trading_id로 복기 조회"""
    recap = db.query(models.Recap).filter(
        models.Recap.trading_id == trading_id,
        models.Recap.user_id == current_user.id
    ).first()

    if not recap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recap not found"
        )

    return recap


@router.get("/by-order/{order_no}", response_model=schemas.Recap)
def get_recap_by_order(
    order_no: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """order_no로 복기 조회"""
    recap = db.query(models.Recap).filter(
        models.Recap.order_no == order_no,
        models.Recap.user_id == current_user.id
    ).first()

    if not recap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recap not found"
        )

    return recap


@router.get("/{trading_plan_id}", response_model=schemas.Recap)
def get_recap(
    trading_plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """특정 trading plan의 복기 조회"""
    recap = db.query(models.Recap).filter(
        models.Recap.trading_plan_id == trading_plan_id,
        models.Recap.user_id == current_user.id
    ).first()

    if not recap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recap not found"
        )

    return recap


@router.get("/", response_model=List[schemas.Recap])
def get_my_recaps(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """현재 유저의 모든 복기 조회"""
    recaps = db.query(models.Recap).filter(
        models.Recap.user_id == current_user.id
    ).offset(skip).limit(limit).all()

    return recaps


# ===== POST 메서드 (생성) =====

@router.post("", response_model=schemas.Recap)
@router.post("/", response_model=schemas.Recap)
def create_recap(
    recap: schemas.RecapCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """복기 내용 생성"""
    print(f"[RECAP] Creating recap for user_id={current_user.id}, trading_id={recap.trading_id}, order_no={recap.order_no}, trading_plan_id={recap.trading_plan_id}")

    # trading_id가 있으면 trading_id 기반으로 우선 처리
    if recap.trading_id:
        # trading_id로 거래 기록 확인
        trading = db.query(models.Trading).filter(
            models.Trading.id == recap.trading_id,
            models.Trading.user_id == current_user.id
        ).first()

        if not trading:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trading record not found or access denied"
            )

        # trading_id로 기존 복기 확인
        existing_recap = db.query(models.Recap).filter(
            models.Recap.trading_id == recap.trading_id,
            models.Recap.user_id == current_user.id
        ).first()

        if existing_recap:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recap already exists for this trading record"
            )

        # trading_id 기반 복기 생성
        db_recap = models.Recap(
            user_id=current_user.id,
            trading_id=recap.trading_id,
            trading_plan_id=recap.trading_plan_id,  # 있으면 함께 저장
            order_no=None,  # trading_id 기반일 때는 order_no 불필요
            catalyst=recap.catalyst,
            market_condition=recap.market_condition,
            price_chart=recap.price_chart,
            volume=recap.volume,
            supply_demand=recap.supply_demand,
            emotion=recap.emotion,
            evaluation=recap.evaluation,
            evaluation_reason=recap.evaluation_reason,
            etc=recap.etc
        )
    # order_no가 있으면 order_no 기반으로
    elif recap.order_no:
        # order_no로 기존 복기 확인
        existing_recap = db.query(models.Recap).filter(
            models.Recap.order_no == recap.order_no,
            models.Recap.user_id == current_user.id
        ).first()

        if existing_recap:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recap already exists for this order"
            )

        # order_no 기반 복기 생성
        db_recap = models.Recap(
            user_id=current_user.id,
            trading_plan_id=None,
            order_no=recap.order_no,
            catalyst=recap.catalyst,
            market_condition=recap.market_condition,
            price_chart=recap.price_chart,
            volume=recap.volume,
            supply_demand=recap.supply_demand,
            emotion=recap.emotion,
            evaluation=recap.evaluation,
            evaluation_reason=recap.evaluation_reason,
            etc=recap.etc
        )
    else:
        # trading_plan_id 기반 (기존 로직)
        trading_plan = db.query(models.TradingPlan).filter(
            models.TradingPlan.id == recap.trading_plan_id,
            models.TradingPlan.user_id == current_user.id
        ).first()

        if not trading_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trading plan not found or access denied"
            )

        # 이미 복기가 존재하는지 확인
        existing_recap = db.query(models.Recap).filter(
            models.Recap.trading_plan_id == recap.trading_plan_id
        ).first()

        if existing_recap:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recap already exists for this trading plan"
            )

        # 복기 생성
        db_recap = models.Recap(
            user_id=current_user.id,
            trading_plan_id=recap.trading_plan_id,
            order_no=recap.order_no,
            catalyst=recap.catalyst,
            market_condition=recap.market_condition,
            price_chart=recap.price_chart,
            volume=recap.volume,
            supply_demand=recap.supply_demand,
            emotion=recap.emotion,
            evaluation=recap.evaluation,
            evaluation_reason=recap.evaluation_reason,
            etc=recap.etc
        )

    db.add(db_recap)
    db.commit()
    db.refresh(db_recap)

    return db_recap


# ===== PUT 메서드 (수정) - 가장 구체적인 경로부터 정의 =====

@router.put("/by-trading/{trading_id}", response_model=schemas.Recap)
def update_recap_by_trading(
    trading_id: int,
    recap_update: schemas.RecapUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """trading_id로 복기 내용 수정"""
    recap = db.query(models.Recap).filter(
        models.Recap.trading_id == trading_id,
        models.Recap.user_id == current_user.id
    ).first()

    if not recap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recap not found"
        )

    # 업데이트
    update_data = recap_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(recap, field, value)

    db.commit()
    db.refresh(recap)

    return recap


@router.put("/by-order/{order_no}", response_model=schemas.Recap)
def update_recap_by_order(
    order_no: str,
    recap_update: schemas.RecapUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """order_no로 복기 내용 수정"""
    recap = db.query(models.Recap).filter(
        models.Recap.order_no == order_no,
        models.Recap.user_id == current_user.id
    ).first()

    if not recap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recap not found"
        )

    # 업데이트
    update_data = recap_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(recap, field, value)

    db.commit()
    db.refresh(recap)

    return recap


@router.put("/{trading_plan_id}", response_model=schemas.Recap)
def update_recap(
    trading_plan_id: int,
    recap_update: schemas.RecapUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """복기 내용 수정"""
    recap = db.query(models.Recap).filter(
        models.Recap.trading_plan_id == trading_plan_id,
        models.Recap.user_id == current_user.id
    ).first()

    if not recap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recap not found"
        )

    # 업데이트
    update_data = recap_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(recap, field, value)

    db.commit()
    db.refresh(recap)

    return recap


# ===== DELETE 메서드 =====

@router.delete("/{trading_plan_id}")
def delete_recap(
    trading_plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """복기 삭제"""
    recap = db.query(models.Recap).filter(
        models.Recap.trading_plan_id == trading_plan_id,
        models.Recap.user_id == current_user.id
    ).first()

    if not recap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recap not found"
        )

    db.delete(recap)
    db.commit()

    return {"message": "Recap deleted successfully"}
