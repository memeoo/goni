"""
정기 작업 스케줄러

APScheduler를 사용하여 백그라운드 작업을 관리합니다.
- 종목정보 자동 업데이트 (월~금 아침 7:30)
"""

import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

# 환경변수에서 키움 API 인증정보 로드
KIWOOM_APP_KEY = os.getenv("KIWOOM_APP_KEY", "")
KIWOOM_SECRET_KEY = os.getenv("KIWOOM_SECRET_KEY", "")

# 전역 스케줄러 인스턴스
scheduler = BackgroundScheduler(daemon=True)


def sync_stocks_info_job():
    """
    종목정보 동기화 작업
    - 코스피 (market_code='0')
    - 코스닥 (market_code='10')
    """
    import sys

    # 부모 디렉토리를 path에 추가 (analyze 모듈 임포트를 위해)
    if '/home/ubuntu/goni' not in sys.path:
        sys.path.insert(0, '/home/ubuntu/goni')

    from app.database import SessionLocal
    from sqlalchemy import text
    from analyze.lib.kiwoom import KiwoomAPI

    logger.info("=" * 80)
    logger.info(f"시작: 종목정보 자동 동기화 작업 ({datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')})")
    logger.info("=" * 80)

    # 키움 API 인증정보 확인
    if not KIWOOM_APP_KEY or not KIWOOM_SECRET_KEY:
        logger.error("키움 API 인증정보가 설정되지 않았습니다. 환경변수를 확인해주세요.")
        logger.error("  - KIWOOM_APP_KEY")
        logger.error("  - KIWOOM_SECRET_KEY")
        return

    db = SessionLocal()

    try:
        # 키움 API 인스턴스 생성 (환경변수에서 로드)
        kiwoom_api = KiwoomAPI(
            app_key=KIWOOM_APP_KEY,
            secret_key=KIWOOM_SECRET_KEY,
            account_no="",
            use_mock=False
        )

        # 동기화할 시장 목록
        markets = [
            ("0", "코스피"),
            ("10", "코스닥"),
        ]

        for market_code, market_name in markets:
            logger.info(f"\n[{market_name}] 종목정보 조회 중...")

            try:
                # ka10099 API 호출
                result = kiwoom_api.get_stocks_info(mrkt_tp=market_code)

                if not result:
                    logger.error(f"[{market_name}] 키움 API 호출 실패")
                    continue

                # 응답 데이터 파싱
                stocks_list = result.get("list", [])
                logger.info(f"[{market_name}] 조회 종목 수: {len(stocks_list)}")

                if not stocks_list:
                    logger.warning(f"[{market_name}] 조회된 종목이 없습니다")
                    continue

                # DB에 저장/업데이트
                added_count = 0
                updated_count = 0

                for stock_data in stocks_list:
                    try:
                        code = stock_data.get("code", "").strip()

                        if not code:
                            continue

                        # 기존 데이터 확인
                        existing = db.execute(
                            text(
                                "SELECT id FROM stocks_info WHERE code = :code"
                            ),
                            {"code": code},
                        ).first()

                        if existing:
                            # 기존 데이터 업데이트
                            db.execute(
                                text(
                                    """
                                    UPDATE stocks_info SET
                                        name = :name,
                                        list_count = :list_count,
                                        audit_info = :audit_info,
                                        reg_day = :reg_day,
                                        last_price = :last_price,
                                        state = :state,
                                        market_code = :market_code,
                                        market_name = :market_name,
                                        up_name = :up_name,
                                        up_size_name = :up_size_name,
                                        company_class_name = :company_class_name,
                                        order_warning = :order_warning,
                                        nxt_enable = :nxt_enable,
                                        updated_at = NOW()
                                    WHERE code = :code
                                    """
                                ),
                                {
                                    "code": code,
                                    "name": stock_data.get("name", ""),
                                    "list_count": stock_data.get("listCount", ""),
                                    "audit_info": stock_data.get("auditInfo", ""),
                                    "reg_day": stock_data.get("regDay", ""),
                                    "last_price": stock_data.get("lastPrice", ""),
                                    "state": stock_data.get("state", ""),
                                    "market_code": stock_data.get("marketCode", ""),
                                    "market_name": stock_data.get("marketName", ""),
                                    "up_name": stock_data.get("upName", ""),
                                    "up_size_name": stock_data.get("upSizeName", ""),
                                    "company_class_name": stock_data.get(
                                        "companyClassName", ""
                                    ),
                                    "order_warning": stock_data.get("orderWarning", ""),
                                    "nxt_enable": stock_data.get("nxtEnable", ""),
                                },
                            )

                            updated_count += 1
                        else:
                            # 새 데이터 추가
                            db.execute(
                                text(
                                    """
                                    INSERT INTO stocks_info
                                    (code, name, list_count, audit_info, reg_day, last_price, state,
                                     market_code, market_name, up_name, up_size_name, company_class_name,
                                     order_warning, nxt_enable, created_at, updated_at)
                                    VALUES
                                    (:code, :name, :list_count, :audit_info, :reg_day, :last_price, :state,
                                     :market_code, :market_name, :up_name, :up_size_name, :company_class_name,
                                     :order_warning, :nxt_enable, NOW(), NOW())
                                    """
                                ),
                                {
                                    "code": code,
                                    "name": stock_data.get("name", ""),
                                    "list_count": stock_data.get("listCount", ""),
                                    "audit_info": stock_data.get("auditInfo", ""),
                                    "reg_day": stock_data.get("regDay", ""),
                                    "last_price": stock_data.get("lastPrice", ""),
                                    "state": stock_data.get("state", ""),
                                    "market_code": stock_data.get("marketCode", ""),
                                    "market_name": stock_data.get("marketName", ""),
                                    "up_name": stock_data.get("upName", ""),
                                    "up_size_name": stock_data.get("upSizeName", ""),
                                    "company_class_name": stock_data.get(
                                        "companyClassName", ""
                                    ),
                                    "order_warning": stock_data.get("orderWarning", ""),
                                    "nxt_enable": stock_data.get("nxtEnable", ""),
                                },
                            )

                            added_count += 1

                    except Exception as e:
                        logger.error(f"종목정보 저장 실패: {stock_data}, Error: {e}")
                        continue

                # DB 커밋
                db.commit()

                logger.info(
                    f"[{market_name}] 동기화 완료: "
                    f"추가={added_count}, 업데이트={updated_count}, "
                    f"합계={added_count + updated_count}"
                )

            except Exception as e:
                logger.error(f"[{market_name}] 동기화 중 오류 발생: {e}", exc_info=True)
                db.rollback()
                continue

    except Exception as e:
        logger.error(f"종목정보 동기화 작업 중 오류 발생: {e}", exc_info=True)
        db.rollback()

    finally:
        db.close()
        logger.info("=" * 80)
        logger.info("완료: 종목정보 자동 동기화 작업")
        logger.info("=" * 80)


def start_scheduler():
    """스케줄러 시작"""
    if scheduler.running:
        logger.warning("스케줄러가 이미 실행 중입니다")
        return

    # 종목정보 동기화: 월~금 아침 7:30 (KST)
    scheduler.add_job(
        sync_stocks_info_job,
        trigger=CronTrigger(
            hour=7,
            minute=30,
            day_of_week="0-4",  # 월(0)~금(4)
            timezone=pytz.timezone("Asia/Seoul"),
        ),
        id="sync_stocks_info",
        name="종목정보 자동 동기화",
        replace_existing=True,
    )

    # 스케줄러 시작
    scheduler.start()

    logger.info("스케줄러 시작 완료")
    logger.info("등록된 작업:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name} (ID: {job.id}, Trigger: {job.trigger})")


def stop_scheduler():
    """스케줄러 종료"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("스케줄러 종료 완료")
    else:
        logger.warning("스케줄러가 실행 중이 아닙니다")


def get_scheduler_jobs():
    """등록된 작업 목록 조회"""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append(
            {
                "id": job.id,
                "name": job.name,
                "trigger": str(job.trigger),
                "next_run_time": job.next_run_time.isoformat()
                if job.next_run_time
                else None,
            }
        )
    return jobs
