"""
키움 API TR ID: ka10172, ka10173 호출 테스트 (개선 버전 v3)
- 모든 조건식으로 순회 테스트
- 각 조건식별 ka10172, ka10173 호출 시도
- 성공/실패 통계
"""

import sys
import json
import logging
import asyncio
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent / 'analyze' / 'lib'))

from kiwoom import KiwoomAPI, KiwoomWebSocketClient

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API 설정
APP_KEY = 'KY7QbSwIVVmjqBM5jIZHbcGOle2O8nQL7dFUNtVmTKU'
SECRET_KEY = 'KUwnffZOR2dP4nwEZCIgTAhu-FquHEa2Xx9mCKE9ak0'
ACCOUNT_NO = '52958566'


def print_section(title: str):
    """섹션 구분선 출력"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def test_condition_search(condition_id: str, search_type: str, token: str, timeout_sec: int = 20):
    """
    특정 조건식과 search_type으로 CNSRREQ 요청 테스트

    Args:
        condition_id: 조건식 ID
        search_type: '0' (일반/ka10172) 또는 '1' (실시간/ka10173)
        token: 접근 토큰
        timeout_sec: 응답 대기 시간 (초)

    Returns:
        dict: 응답 데이터 또는 None
    """
    try:
        ws_client = KiwoomWebSocketClient(access_token=token, use_mock=False)

        # 연결
        await ws_client.connect()
        await asyncio.sleep(0.5)

        # 요청 파라미터
        if search_type == '0':  # ka10172
            request_param = {
                'trnm': 'CNSRREQ',
                'seq': condition_id,
                'search_type': '0',
                'stex_tp': 'K',
                'cont_yn': 'N',
                'next_key': ''
            }
        else:  # ka10173
            request_param = {
                'trnm': 'CNSRREQ',
                'seq': condition_id,
                'search_type': '1'
            }

        # 메시지 수신 태스크 시작
        receive_task = asyncio.create_task(ws_client.receive_messages())

        # 요청 전송
        await ws_client.send_message(request_param)

        # 응답 대기
        max_wait = int(timeout_sec * 10)  # timeout_sec초를 0.1초 단위로 변환

        for i in range(max_wait):
            if condition_id in ws_client.response_queue:
                response = ws_client.response_queue[condition_id]
                del ws_client.response_queue[condition_id]

                await ws_client.disconnect()
                return response

            await asyncio.sleep(0.1)

        # 타임아웃
        await ws_client.disconnect()
        return None

    except Exception as e:
        logger.error(f"조건식 검색 실패 (ID={condition_id}, search_type={search_type}): {e}")
        return None


async def main():
    """메인 테스트 함수"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  키움 API 조건검색 TR ID 전수 테스트 (v3)".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")

    api = KiwoomAPI(
        app_key=APP_KEY,
        secret_key=SECRET_KEY,
        account_no=ACCOUNT_NO,
        use_mock=False
    )

    print("\n[초기화] 접근 토큰 발급...")
    token = api.get_access_token()
    if not token:
        print("✗ 토큰 발급 실패")
        return
    print(f"✓ 토큰 발급 성공")

    # 조건식 목록 조회
    print_section("Step 1: 조건식 목록 조회")

    ws_client = KiwoomWebSocketClient(access_token=token, use_mock=False)
    condition_list = await ws_client.request_condition_list()

    if not condition_list:
        print("✗ 조건식 목록 조회 실패")
        return

    print(f"✓ 조건식 목록 조회 성공: {len(condition_list)}개\n")

    for i, cond in enumerate(condition_list, 1):
        print(f"   {i}. ID={cond[0]}, 이름={cond[1]}")

    # Step 2: 각 조건식별 ka10172, ka10173 테스트
    print_section(f"Step 2: 조건식별 ka10172/ka10173 테스트 (총 {len(condition_list)} x 2 = {len(condition_list) * 2}건)")

    results = {
        'ka10172': {'success': 0, 'failed': 0, 'timeout': 0, 'details': []},
        'ka10173': {'success': 0, 'failed': 0, 'timeout': 0, 'details': []}
    }

    for idx, condition in enumerate(condition_list, 1):
        condition_id = condition[0]
        condition_name = condition[1]

        print(f"\n[{idx}/{len(condition_list)}] 조건식: {condition_name} (ID={condition_id})")

        # ka10172 테스트 (일반 조회)
        print(f"  └─ ka10172 (일반 조회) 테스트 중...", end="", flush=True)
        response_ka10172 = await test_condition_search(condition_id, '0', token, timeout_sec=15)

        if response_ka10172:
            return_code = response_ka10172.get('return_code', -1)
            data_count = len(response_ka10172.get('data', []))

            if return_code == 0:
                print(f" ✓ 성공 ({data_count}개 종목)")
                results['ka10172']['success'] += 1
                results['ka10172']['details'].append({
                    'condition_id': condition_id,
                    'condition_name': condition_name,
                    'status': 'success',
                    'data_count': data_count
                })
            else:
                print(f" ✗ 실패 (오류 코드: {return_code})")
                results['ka10172']['failed'] += 1
                results['ka10172']['details'].append({
                    'condition_id': condition_id,
                    'condition_name': condition_name,
                    'status': 'error',
                    'return_code': return_code
                })
        else:
            print(f" ✗ 타임아웃 (15초)")
            results['ka10172']['timeout'] += 1
            results['ka10172']['details'].append({
                'condition_id': condition_id,
                'condition_name': condition_name,
                'status': 'timeout'
            })

        # ka10173 테스트 (실시간 조회)
        print(f"  └─ ka10173 (실시간 조회) 테스트 중...", end="", flush=True)
        response_ka10173 = await test_condition_search(condition_id, '1', token, timeout_sec=15)

        if response_ka10173:
            return_code = response_ka10173.get('return_code', -1)
            data_count = len(response_ka10173.get('data', []))

            if return_code == 0:
                print(f" ✓ 성공 ({data_count}개 종목)")
                results['ka10173']['success'] += 1
                results['ka10173']['details'].append({
                    'condition_id': condition_id,
                    'condition_name': condition_name,
                    'status': 'success',
                    'data_count': data_count
                })
            else:
                print(f" ✗ 실패 (오류 코드: {return_code})")
                results['ka10173']['failed'] += 1
                results['ka10173']['details'].append({
                    'condition_id': condition_id,
                    'condition_name': condition_name,
                    'status': 'error',
                    'return_code': return_code
                })
        else:
            print(f" ✗ 타임아웃 (15초)")
            results['ka10173']['timeout'] += 1
            results['ka10173']['details'].append({
                'condition_id': condition_id,
                'condition_name': condition_name,
                'status': 'timeout'
            })

    # Step 3: 최종 결과
    print_section("Step 3: 최종 테스트 결과")

    print("\n📊 통계:")
    print(f"\nka10172 (일반 조회):")
    print(f"  ✓ 성공: {results['ka10172']['success']}건")
    print(f"  ✗ 실패: {results['ka10172']['failed']}건")
    print(f"  ⏱ 타임아웃: {results['ka10172']['timeout']}건")

    print(f"\nka10173 (실시간 조회):")
    print(f"  ✓ 성공: {results['ka10173']['success']}건")
    print(f"  ✗ 실패: {results['ka10173']['failed']}건")
    print(f"  ⏱ 타임아웃: {results['ka10173']['timeout']}건")

    # 성공한 조건식 출력
    if results['ka10172']['success'] > 0:
        print(f"\n✓ ka10172 성공한 조건식:")
        for detail in results['ka10172']['details']:
            if detail['status'] == 'success':
                print(f"  - {detail['condition_name']} (ID={detail['condition_id']}, "
                      f"{detail['data_count']}개 종목)")

    if results['ka10173']['success'] > 0:
        print(f"\n✓ ka10173 성공한 조건식:")
        for detail in results['ka10173']['details']:
            if detail['status'] == 'success':
                print(f"  - {detail['condition_name']} (ID={detail['condition_id']}, "
                      f"{detail['data_count']}개 종목)")

    # 최종 판정
    print("\n" + "=" * 70)
    total_success = results['ka10172']['success'] + results['ka10173']['success']
    total_tests = len(condition_list) * 2

    if total_success > 0:
        print(f"🎉 테스트 부분 성공! ({total_success}/{total_tests})")
        print(f"   성공률: {(total_success/total_tests)*100:.1f}%")
    else:
        print(f"⚠️  모든 테스트가 실패했습니다. ({total_success}/{total_tests})")
        print(f"   원인: 응답 타임아웃 또는 서버 오류")

    print("=" * 70 + "\n")


if __name__ == '__main__':
    asyncio.run(main())
