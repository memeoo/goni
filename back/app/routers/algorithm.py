from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models

router = APIRouter(tags=["algorithms"])


@router.get("/api/algorithms", tags=["algorithms"])
def get_algorithms(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    알고리즘 목록 조회

    Args:
        skip (int): 스킵할 레코드 수 (기본값: 0)
        limit (int): 조회할 레코드 수 (기본값: 100)

    Returns:
        dict: 알고리즘 목록 및 메타데이터
    """
    try:
        # 전체 알고리즘 개수
        total = db.query(models.Algorithm).count()

        # 알고리즘 목록 조회 (최신순)
        algorithms = db.query(models.Algorithm).order_by(
            models.Algorithm.created_at.desc()
        ).offset(skip).limit(limit).all()

        result = []
        for algo in algorithms:
            result.append({
                "id": algo.id,
                "name": algo.name,
                "description": algo.description,
                "created_at": algo.created_at,
                "updated_at": algo.updated_at
            })

        print(f"✅ 알고리즘 목록 조회 완료: {len(result)}개 (전체: {total}개)")

        return {
            "data": result,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    except Exception as e:
        print(f"❌ 알고리즘 목록 조회 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"알고리즘 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )
