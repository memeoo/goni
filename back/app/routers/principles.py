from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Principle
from app.routers.auth import get_current_user
from pydantic import BaseModel
from typing import List

router = APIRouter(tags=["principles"])


class PrincipleCreate(BaseModel):
    principle_text: str


class PrincipleResponse(BaseModel):
    id: int
    user_id: int
    principle_text: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=dict)
def get_principles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all principles for current user"""
    try:
        principles = (
            db.query(Principle)
            .filter(Principle.user_id == current_user.id)
            .order_by(Principle.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        total = (
            db.query(Principle)
            .filter(Principle.user_id == current_user.id)
            .count()
        )

        return {
            "data": principles,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=dict)
def create_principle(
    principle: PrincipleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new principle for current user"""
    try:
        new_principle = Principle(
            user_id=current_user.id,
            principle_text=principle.principle_text
        )
        db.add(new_principle)
        db.commit()
        db.refresh(new_principle)

        return {
            "status": "success",
            "data": new_principle,
            "message": "원칙이 저장되었습니다."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{principle_id}", response_model=dict)
def delete_principle(
    principle_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete principle by ID"""
    try:
        principle = (
            db.query(Principle)
            .filter(
                Principle.id == principle_id,
                Principle.user_id == current_user.id
            )
            .first()
        )

        if not principle:
            raise HTTPException(status_code=404, detail="원칙을 찾을 수 없습니다.")

        db.delete(principle)
        db.commit()

        return {
            "status": "success",
            "message": "원칙이 삭제되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
