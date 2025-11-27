"""
추천 종목 서비스

조건 검색 API를 이용해 추천 종목을 조회하고 DB에 저장하는 서비스
"""

import logging
import sys
from datetime import date
from typing import Optional, List
from sqlalchemy.orm import Session

# 프로젝트 경로 추가 (analyze 패키지 임포트용)
sys.path.insert(0, '/home/ubuntu/goni')

from analyze.lib.kiwoom import KiwoomAPI
from app.models import RecStock, Algorithm
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class RecommendationService:
    """추천 종목 관리 서비스"""

    def __init__(self, app_key: str, secret_key: str, account_no: str):
        """
        Args:
            app_key: 키움증권 앱 키
            secret_key: 키움증권 시크릿 키
            account_no: 계좌번호
        """
        self.kiwoom_api = KiwoomAPI(
            app_key=app_key,
            secret_key=secret_key,
            account_no=account_no,
            use_mock=False  # 실전투자
        )

    def get_condition_by_name(self, condition_name: str) -> Optional[str]:
        """
        조건명으로 조건 ID를 조회합니다.

        Args:
            condition_name: 조건명 (예: '신고가 돌파')

        Returns:
            str: 조건 ID, 찾지 못하면 None
        """
        try:
            conditions = self.kiwoom_api.get_condition_list()
            if not conditions:
                logger.error("조건 검색 목록을 가져올 수 없습니다")
                return None

            for condition in conditions:
                if condition.get('name') == condition_name:
                    logger.info(f"조건 '{condition_name}' 찾음: ID={condition.get('id')}")
                    return condition.get('id')

            logger.warning(f"조건 '{condition_name}'을(를) 찾을 수 없습니다")
            logger.info(f"사용 가능한 조건: {[c.get('name') for c in conditions]}")
            return None

        except Exception as e:
            logger.error(f"조건 조회 중 오류: {e}")
            return None

    def search_and_update_rec_stocks(
        self,
        condition_name: str,
        algorithm_id: int,
        db: Session,
        stock_exchange_type: str = '%'  # '%': 전체, 'K': 코스피, 'Q': 코스닥
    ) -> bool:
        """
        조건식으로 종목을 검색하고 rec_stocks 테이블에 저장합니다.

        Args:
            condition_name: 조건명 (예: '신고가 돌파')
            algorithm_id: 알고리즘 ID (rec_stocks의 algorithm_id)
            db: SQLAlchemy 세션
            stock_exchange_type: 거래소 구분 (기본: '%' 전체)

        Returns:
            bool: 성공 여부
        """
        try:
            # 1. 알고리즘 존재 확인
            algorithm = db.query(Algorithm).filter(Algorithm.id == algorithm_id).first()
            if not algorithm:
                logger.error(f"알고리즘 ID {algorithm_id}이 존재하지 않습니다")
                return False

            logger.info(f"알고리즘 '{algorithm.name}' (ID: {algorithm_id})으로 추천 종목 업데이트 시작")

            # 2. 조건명으로 조건 ID 조회
            condition_id = self.get_condition_by_name(condition_name)
            if not condition_id:
                logger.error(f"조건 '{condition_name}'을(를) 찾을 수 없습니다")
                return False

            # 3. 조건식으로 종목 검색
            logger.info(f"조건식 '{condition_name}' (ID: {condition_id})으로 종목 검색 중...")
            search_results = self.kiwoom_api.search_condition(
                condition_id=condition_id,
                search_type='0',  # 일반 조회
                stock_exchange_type=stock_exchange_type
            )

            if search_results is None:
                logger.error("종목 검색 실패")
                return False

            if len(search_results) == 0:
                logger.warning(f"검색 결과가 없습니다 (조건: {condition_name})")
                return True  # 결과 없음도 성공으로 처리

            logger.info(f"검색 결과: {len(search_results)}개 종목")

            # 4. 기존 데이터 삭제 (같은 알고리즘, 오늘 날짜)
            today = date.today()
            deleted_count = db.query(RecStock).filter(
                RecStock.algorithm_id == algorithm_id,
                RecStock.recommendation_date == today
            ).delete()

            if deleted_count > 0:
                logger.info(f"기존 추천 종목 {deleted_count}개 삭제")

            # 5. 새 추천 종목 저장
            saved_count = 0
            for stock in search_results:
                try:
                    stock_code = stock.get('stock_code', '')
                    stock_name = stock.get('stock_name', '')
                    current_price = stock.get('current_price', 0)

                    if not stock_code or not stock_name:
                        logger.warning(f"필수 정보 누락: {stock}")
                        continue

                    # rec_stock 생성
                    rec_stock = RecStock(
                        stock_name=stock_name,
                        stock_code=stock_code,
                        recommendation_date=today,
                        algorithm_id=algorithm_id,
                        closing_price=current_price,
                        change_rate=None  # 키움 API에서 제공되지 않으므로 None
                    )

                    db.add(rec_stock)
                    saved_count += 1

                except Exception as e:
                    logger.warning(f"종목 저장 실패: {stock.get('stock_name')} ({stock.get('stock_code')}), {e}")
                    continue

            # 6. 변경사항 저장
            db.commit()
            logger.info(f"✅ 추천 종목 저장 완료: {saved_count}개")

            return True

        except Exception as e:
            db.rollback()
            logger.error(f"추천 종목 업데이트 실패: {e}")
            return False


def update_recommendation_stocks(
    condition_name: str,
    algorithm_id: int,
    app_key: str = None,
    secret_key: str = None,
    account_no: str = None
) -> bool:
    """
    추천 종목을 업데이트합니다 (스탠드얼론 함수).

    환경변수에서 키움 API 자격증명을 읽고, 조건식으로 종목을 검색하여 저장합니다.

    Args:
        condition_name: 조건명 (예: '신고가 돌파')
        algorithm_id: 알고리즘 ID
        app_key: 키움 앱 키 (기본: 환경변수에서 읽음)
        secret_key: 키움 시크릿 키 (기본: 환경변수에서 읽음)
        account_no: 계좌번호 (기본: 환경변수에서 읽음)

    Returns:
        bool: 성공 여부

    Example:
        >>> success = update_recommendation_stocks(
        ...     condition_name='신고가 돌파',
        ...     algorithm_id=1,
        ...     app_key='your_app_key',
        ...     secret_key='your_secret_key',
        ...     account_no='your_account_no'
        ... )
        >>> if success:
        ...     print("추천 종목 업데이트 완료")
    """
    import os

    # 기본값: 환경변수에서 읽음
    if app_key is None:
        app_key = os.getenv('KIWOOM_APP_KEY', '')
    if secret_key is None:
        secret_key = os.getenv('KIWOOM_SECRET_KEY', '')
    if account_no is None:
        account_no = os.getenv('KIWOOM_ACCOUNT_NO', '')

    if not app_key or not secret_key or not account_no:
        logger.error("키움 API 자격증명이 설정되지 않았습니다")
        return False

    # 데이터베이스 세션 생성
    db = SessionLocal()

    try:
        service = RecommendationService(app_key, secret_key, account_no)
        return service.search_and_update_rec_stocks(condition_name, algorithm_id, db)

    finally:
        db.close()


if __name__ == '__main__':
    # 테스트 코드
    import os
    from dotenv import load_dotenv

    # 환경변수 로드
    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 키움 API 자격증명
    APP_KEY = os.getenv('KIWOOM_APP_KEY')
    SECRET_KEY = os.getenv('KIWOOM_SECRET_KEY')
    ACCOUNT_NO = os.getenv('KIWOOM_ACCOUNT_NO')

    if not APP_KEY or not SECRET_KEY or not ACCOUNT_NO:
        print("❌ 환경변수에서 키움 API 자격증명을 찾을 수 없습니다")
        print("   KIWOOM_APP_KEY, KIWOOM_SECRET_KEY, KIWOOM_ACCOUNT_NO를 설정하세요")
        sys.exit(1)

    print("=" * 70)
    print("추천 종목 업데이트 테스트")
    print("=" * 70)

    # 1. 조건 목록 조회
    print("\n[1단계] 조건 목록 조회")
    print("-" * 70)
    service = RecommendationService(APP_KEY, SECRET_KEY, ACCOUNT_NO)
    conditions = service.kiwoom_api.get_condition_list()

    if conditions:
        print(f"✅ 조건 목록 조회 완료: {len(conditions)}개")
        for condition in conditions:
            print(f"   - {condition['name']} (ID: {condition['id']})")
    else:
        print("❌ 조건 목록 조회 실패")
        sys.exit(1)

    # 2. '신고가 돌파' 조건으로 종목 검색
    print("\n[2단계] '신고가 돌파' 조건으로 종목 검색")
    print("-" * 70)
    search_results = service.kiwoom_api.search_condition('0')  # 첫 번째 조건 사용

    if search_results is not None:
        print(f"✅ 종목 검색 완료: {len(search_results)}개")
        for stock in search_results[:5]:  # 최초 5개만 출력
            print(f"   - {stock['stock_name']}({stock['stock_code']}): {stock['current_price']:,.0f}원")
        if len(search_results) > 5:
            print(f"   ... 외 {len(search_results) - 5}개")
    else:
        print("❌ 종목 검색 실패")
        sys.exit(1)

    # 3. rec_stocks 업데이트
    print("\n[3단계] rec_stocks 업데이트")
    print("-" * 70)
    success = update_recommendation_stocks(
        condition_name='신고가 돌파',
        algorithm_id=1,
        app_key=APP_KEY,
        secret_key=SECRET_KEY,
        account_no=ACCOUNT_NO
    )

    if success:
        print("✅ 추천 종목 업데이트 완료")
    else:
        print("❌ 추천 종목 업데이트 실패")
        sys.exit(1)

    print("\n" + "=" * 70)
