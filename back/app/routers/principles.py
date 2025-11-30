from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
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


@router.get("")
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

        return JSONResponse(
            status_code=200,
            content={
                "data": [
                    {
                        "id": p.id,
                        "user_id": p.user_id,
                        "principle_text": p.principle_text,
                        "created_at": p.created_at.isoformat() if p.created_at else None,
                        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                    }
                    for p in principles
                ],
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
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

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "id": new_principle.id,
                    "user_id": new_principle.user_id,
                    "principle_text": new_principle.principle_text,
                    "created_at": new_principle.created_at.isoformat() if new_principle.created_at else None,
                    "updated_at": new_principle.updated_at.isoformat() if new_principle.updated_at else None,
                },
                "message": "원칙이 저장되었습니다."
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{principle_id}")
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

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "원칙이 삭제되었습니다."
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
