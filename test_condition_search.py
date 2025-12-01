#!/usr/bin/env python3
"""
조건 검색식 테스트: '대왕개미 단타론'과 '신고가 따라잡기'

스케줄링 시간은 무시하고 두 조건 검색식이 정상 작동하는지 테스트합니다.
"""

import sys
sys.path.insert(0, '/home/ubuntu/goni')
sys.path.insert(0, '/home/ubuntu/goni/back')

import os
import logging
from dotenv import load_dotenv
from analyze.lib.kiwoom import KiwoomAPI
from app.services.recommendation_service import RecommendationService
from app.database import SessionLocal
from app.models import Algorithm, RecStock
from datetime import date

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 환경변수 로드
load_dotenv('back/.env')

# 색상 코드
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(title):
    """헤더 출력"""
    print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
    print(f"{BOLD}{CYAN}{title.center(80)}{RESET}")
    print(f"{BOLD}{CYAN}{'='*80}{RESET}\n")


def print_section(title):
    """섹션 출력"""
    print(f"{BOLD}{YELLOW}{'-'*80}{RESET}")
    print(f"{BOLD}{YELLOW}[{title}]{RESET}")
    print(f"{BOLD}{YELLOW}{'-'*80}{RESET}")


def print_success(message):
    """성공 메시지"""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message):
    """에러 메시지"""
    print(f"{RED}✗ {message}{RESET}")


def print_info(message):
    """정보 메시지"""
    print(f"{CYAN}ℹ {message}{RESET}")


def test_kiwoom_api_connection():
    """Kiwoom API 기본 연결 테스트"""
    print_section("1. Kiwoom API 연결 테스트")

    app_key = os.getenv('KIWOOM_APP_KEY')
    secret_key = os.getenv('KIWOOM_SECRET_KEY')
    account_no = os.getenv('KIWOOM_ACCOUNT_NO')

    if not app_key or not secret_key or not account_no:
        print_error("환경변수에서 Kiwoom API 자격증명을 찾을 수 없습니다")
        print(f"  KIWOOM_APP_KEY: {bool(app_key)}")
        print(f"  KIWOOM_SECRET_KEY: {bool(secret_key)}")
        print(f"  KIWOOM_ACCOUNT_NO: {bool(account_no)}")
        return None

    try:
        api = KiwoomAPI(app_key, secret_key, account_no, use_mock=False)
        token = api.get_access_token()

        if token:
            print_success(f"Kiwoom API 토큰 발급 성공")
            return api
        else:
            print_error("Kiwoom API 토큰 발급 실패")
            return None
    except Exception as e:
        print_error(f"Kiwoom API 초기화 실패: {e}")
        return None


def test_condition_list(api):
    """조건 검색 목록 조회 테스트"""
    print_section("2. 조건 검색 목록 조회")

    try:
        conditions = api.get_condition_list()

        if conditions:
            print_success(f"조건 검색 목록 조회 성공: {len(conditions)}개")
            print("\n사용 가능한 조건들:")

            # ID별로 정렬
            conditions_sorted = sorted(conditions, key=lambda x: int(x.get('id', '0')))

            condition_5 = None
            condition_7 = None

            for condition in conditions_sorted:
                cond_id = condition.get('id')
                cond_name = condition.get('name')

                # 대왕개미 찾기
                if cond_id == '5':
                    condition_5 = condition
                    print(f"  {BOLD}ID: {cond_id:<3} | {cond_name:<30} {GREEN}[대왕개미 단타론]{RESET}")
                # 신고가 찾기
                elif cond_id == '7':
                    condition_7 = condition
                    print(f"  {BOLD}ID: {cond_id:<3} | {cond_name:<30} {GREEN}[신고가 따라잡기]{RESET}")
                else:
                    print(f"  ID: {cond_id:<3} | {cond_name:<30}")

            # 필수 조건 확인
            print()
            if condition_5:
                print_success("ID 5 (대왕개미 단타론) 찾음")
            else:
                print_error("ID 5 (대왕개미 단타론)을 찾을 수 없습니다")

            if condition_7:
                print_success("ID 7 (신고가 따라잡기) 찾음")
            else:
                print_error("ID 7 (신고가 따라잡기)을 찾을 수 없습니다")

            return conditions
        else:
            print_error("조건 검색 목록 조회 실패")
            return None

    except Exception as e:
        print_error(f"조건 검색 목록 조회 중 오류: {e}")
        return None


def test_condition_search(api, condition_id, condition_name):
    """조건식 검색 테스트"""
    print_section(f"조건식 검색 - ID: {condition_id} ({condition_name})")

    try:
        print(f"검색 중... (조건ID: {condition_id}, 유형: 일반조회, 거래소: 전체)")

        results = api.search_condition(
            condition_id=condition_id,
            search_type='0',  # 일반 조회
            stock_exchange_type='%'  # 전체 거래소
        )

        if results is not None:
            stock_count = len(results) if isinstance(results, list) else 0
            print_success(f"조건식 검색 성공: {stock_count}개 종목")

            if stock_count > 0:
                print(f"\n검색된 종목 (처음 10개):")
                for i, stock in enumerate(results[:10], 1):
                    stock_code = stock.get('stock_code', 'N/A')
                    stock_name = stock.get('stock_name', 'N/A')
                    price = stock.get('current_price', 'N/A')

                    if isinstance(price, (int, float)):
                        price_str = f"{price:>10,.0f}원"
                    else:
                        price_str = f"{str(price):>15}"

                    print(f"  {i:2}. {stock_code:<6} | {stock_name:<15} | {price_str}")

                if stock_count > 10:
                    print(f"  ... 외 {stock_count - 10}개")

                return results
            else:
                print_info("검색된 종목이 없습니다 (장 외 시간일 수 있습니다)")
                return results
        else:
            print_error("조건식 검색 실패")
            return None

    except Exception as e:
        print_error(f"조건식 검색 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_recommendation_service():
    """RecommendationService 를 이용한 통합 테스트"""
    print_section("4. RecommendationService 통합 테스트")

    app_key = os.getenv('KIWOOM_APP_KEY')
    secret_key = os.getenv('KIWOOM_SECRET_KEY')
    account_no = os.getenv('KIWOOM_ACCOUNT_NO')

    if not app_key or not secret_key or not account_no:
        print_error("환경변수에서 Kiwoom API 자격증명을 찾을 수 없습니다")
        return False

    db = SessionLocal()

    try:
        # 알고리즘 확인
        algo_1 = db.query(Algorithm).filter(Algorithm.id == 1).first()
        algo_2 = db.query(Algorithm).filter(Algorithm.id == 2).first()

        if not algo_1:
            print_error("알고리즘 1 (신고가 따라잡기)이 데이터베이스에 없습니다")
            return False

        if not algo_2:
            print_error("알고리즘 2 (대왕개미 단타론)이 데이터베이스에 없습니다")
            return False

        print_success(f"알고리즘 1 찾음: {algo_1.name}")
        print_success(f"알고리즘 2 찾음: {algo_2.name}")

        # RecommendationService 생성
        service = RecommendationService(app_key, secret_key, account_no)

        print("\n[테스트 4-1] 신고가 따라잡기 (ID: 7) 검색 및 저장")
        print("-" * 80)

        success_1 = service.search_and_update_rec_stocks(
            condition_id='7',
            algorithm_id=1,
            db=db,
            stock_exchange_type='%'
        )

        if success_1:
            print_success("신고가 따라잡기 업데이트 성공")

            # 저장된 데이터 확인
            today = date.today()
            rec_stocks_1 = db.query(RecStock).filter(
                RecStock.algorithm_id == 1,
                RecStock.recommendation_date == today
            ).all()
            print_info(f"저장된 종목 수: {len(rec_stocks_1)}개")

            if rec_stocks_1:
                for i, stock in enumerate(rec_stocks_1[:5], 1):
                    print(f"  {i}. {stock.stock_code} | {stock.stock_name} | {stock.closing_price:,.0f}원")
        else:
            print_error("신고가 따라잡기 업데이트 실패")

        print("\n[테스트 4-2] 대왕개미 단타론 (ID: 5) 검색 및 저장")
        print("-" * 80)

        success_2 = service.search_and_update_rec_stocks(
            condition_id='5',
            algorithm_id=2,
            db=db,
            stock_exchange_type='%'
        )

        if success_2:
            print_success("대왕개미 단타론 업데이트 성공")

            # 저장된 데이터 확인
            rec_stocks_2 = db.query(RecStock).filter(
                RecStock.algorithm_id == 2,
                RecStock.recommendation_date == today
            ).all()
            print_info(f"저장된 종목 수: {len(rec_stocks_2)}개")

            if rec_stocks_2:
                for i, stock in enumerate(rec_stocks_2[:5], 1):
                    print(f"  {i}. {stock.stock_code} | {stock.stock_name} | {stock.closing_price:,.0f}원")
        else:
            print_error("대왕개미 단타론 업데이트 실패")

        return success_1 and success_2

    except Exception as e:
        print_error(f"RecommendationService 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """메인 테스트 함수"""
    print_header("조건 검색식 테스트")
    print("두 조건 검색식이 정상 작동하는지 검증합니다:")
    print("1. 대왕개미 단타론 (조건ID: 5)")
    print("2. 신고가 따라잡기 (조건ID: 7)")

    # 1단계: Kiwoom API 연결
    api = test_kiwoom_api_connection()
    if not api:
        print_header("테스트 실패")
        print_error("Kiwoom API 연결 실패로 테스트를 계속할 수 없습니다")
        return False

    # 2단계: 조건 검색 목록 조회
    conditions = test_condition_list(api)
    if not conditions:
        print_header("테스트 실패")
        print_error("조건 검색 목록 조회 실패로 테스트를 계속할 수 없습니다")
        return False

    # 3단계: 각 조건식으로 검색
    print_section("3. 조건식별 종목 검색")

    results_5 = test_condition_search(api, '5', '대왕개미 단타론')
    print()
    results_7 = test_condition_search(api, '7', '신고가 따라잡기')

    # 4단계: RecommendationService 통합 테스트
    success = test_recommendation_service()

    # 최종 결과
    print_header("테스트 결과 요약")

    test_results = {
        "Kiwoom API 연결": api is not None,
        "조건 검색 목록 조회": conditions is not None,
        "ID 5 (대왕개미 단타론) 검색": results_5 is not None,
        "ID 7 (신고가 따라잡기) 검색": results_7 is not None,
        "RecommendationService 통합": success
    }

    all_passed = all(test_results.values())

    for test_name, passed in test_results.items():
        if passed:
            print_success(test_name)
        else:
            print_error(test_name)

    print()
    if all_passed:
        print(f"{GREEN}{BOLD}모든 테스트 통과{RESET}")
        return True
    else:
        print(f"{YELLOW}{BOLD}일부 테스트 실패{RESET}")
        return False


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{RED}테스트가 사용자에 의해 중단되었습니다{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}예상치 못한 오류: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
