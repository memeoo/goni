"""
추천 종목 정기 업데이트 스케줄러

매일 토일 제외하고 18:10에 신고가 돌파 조건으로 추천 종목을 업데이트합니다.
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import sys

# 프로젝트 경로 추가
sys.path.insert(0, '/home/ubuntu/goni')

from app.database import SessionLocal
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)

# 스케줄러 인스턴스
scheduler = BackgroundScheduler()


def update_rec_stocks_job():
    """
    신고가 돌파 조건으로 추천 종목을 검색하고 업데이트합니다.

    매일 18:10에 실행되며, 토요일과 일요일은 제외됩니다.
    기존 데이터는 삭제하지 않고 누적되며, recommendation_date로 구분됩니다.
    """
    try:
        logger.info(f"[스케줄러] 추천 종목 업데이트 작업 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 키움 API 자격증명 확인
        app_key = os.getenv('KIWOOM_APP_KEY')
        secret_key = os.getenv('KIWOOM_SECRET_KEY')
        account_no = os.getenv('KIWOOM_ACCOUNT_NO')

        if not app_key or not secret_key or not account_no:
            logger.error("[스케줄러] 키움 API 자격증명이 설정되지 않았습니다")
            return False

        # 데이터베이스 세션 생성
        db = SessionLocal()

        try:
            # RecommendationService 생성
            service = RecommendationService(app_key, secret_key, account_no)

            # 신고가 돌파 조건으로 알고리즘 1 업데이트
            success = service.search_and_update_rec_stocks(
                condition_name='신고가 돌파',
                algorithm_id=1,
                db=db,
                stock_exchange_type='%'  # 전체
            )

            if success:
                logger.info("[스케줄러] ✅ 추천 종목 업데이트 완료")
                return True
            else:
                logger.error("[스케줄러] ❌ 추천 종목 업데이트 실패")
                return False

        finally:
            db.close()

    except Exception as e:
        logger.error(f"[스케줄러] 추천 종목 업데이트 중 오류: {e}", exc_info=True)
        return False


def start_scheduler():
    """스케줄러를 시작합니다."""
    try:
        # 이미 실행 중인 스케줄러는 재시작하지 않음
        if scheduler.running:
            logger.warning("[스케줄러] 스케줄러가 이미 실행 중입니다")
            return

        # 매일 월-금요일 18:10에 실행 (0=월, 1=화, 2=수, 3=목, 4=금)
        # day_of_week='0-4'는 월-금요일을 의미 (토일 제외)
        scheduler.add_job(
            update_rec_stocks_job,
            trigger=CronTrigger(
                hour=18,
                minute=10,
                day_of_week='0-4',  # 월-금요일만 (토일 제외)
                timezone='Asia/Seoul'
            ),
            id='update_rec_stocks_job',
            name='신고가 돌파 추천 종목 업데이트',
            replace_existing=True
        )

        scheduler.start()
        logger.info("[스케줄러] ✅ 스케줄러 시작 (매일 18:10, 토일 제외)")
        logger.info("[스케줄러] 등록된 작업:")
        for job in scheduler.get_jobs():
            logger.info(f"  - ID: {job.id}, 이름: {job.name}, 트리거: {job.trigger}")

    except Exception as e:
        logger.error(f"[스케줄러] 스케줄러 시작 중 오류: {e}", exc_info=True)


def stop_scheduler():
    """스케줄러를 중지합니다."""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("[스케줄러] 스케줄러 중지됨")
    except Exception as e:
        logger.error(f"[스케줄러] 스케줄러 중지 중 오류: {e}")


def get_scheduler_jobs():
    """스케줄러 작업 목록을 반환합니다 (호환성 함수)."""
    return scheduler.get_jobs()


# 호환성 함수
def sync_stocks_info_job():
    """stocks_info 동기화 작업 (호환성을 위한 함수)"""
    logger.debug("[스케줄러] sync_stocks_info_job 호출됨")
    pass
