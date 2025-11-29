#!/usr/bin/env python3
"""키움 API 직접 테스트 - WebSocket 연결 상태 확인"""

import sys
sys.path.insert(0, '/home/ubuntu/goni')
from analyze.lib.kiwoom import KiwoomAPI
import os
from dotenv import load_dotenv
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv('back/.env')

print("\n" + "="*70)
print("키움 API WebSocket 연결 테스트")
print("="*70 + "\n")

api = KiwoomAPI(
    app_key=os.getenv('KIWOOM_APP_KEY'),
    secret_key=os.getenv('KIWOOM_SECRET_KEY'),
    account_no=os.getenv('KIWOOM_ACCOUNT_NO'),
    use_mock=False
)

print("[1단계] 조건 검색 목록 조회")
print("-"*70)
conditions = api.get_condition_list()

if conditions:
    print(f"✅ 조건 목록 조회 성공: {len(conditions)}개\n")
    for i, cond in enumerate(conditions, 1):
        print(f"   {i}. {cond['name']:<30} (ID: {cond['id']})")
else:
    print("❌ 조건 목록 조회 실패\n")
    sys.exit(1)

print("\n[2단계] 신고가 돌파 조건(ID: 7)으로 종목 검색")
print("-"*70)
results_new = api.search_condition(
    condition_id='7',
    search_type='0',
    stock_exchange_type='%'
)

if results_new is not None:
    print(f"✅ 검색 성공: {len(results_new)}개 종목\n")
    if results_new:
        for i, stock in enumerate(results_new[:5], 1):
            print(f"   {i}. {stock['stock_name']:<15} ({stock['stock_code']}): {stock['current_price']:>10,.0f}원")
        if len(results_new) > 5:
            print(f"   ... 외 {len(results_new) - 5}개")
else:
    print("❌ 검색 실패\n")

print("\n[3단계] 대왕개미단타 조건(ID: 5)으로 종목 검색")
print("-"*70)
results_dae = api.search_condition(
    condition_id='5',
    search_type='0',
    stock_exchange_type='%'
)

if results_dae is not None:
    print(f"✅ 검색 성공: {len(results_dae)}개 종목\n")
    if results_dae:
        for i, stock in enumerate(results_dae[:5], 1):
            print(f"   {i}. {stock['stock_name']:<15} ({stock['stock_code']}): {stock['current_price']:>10,.0f}원")
        if len(results_dae) > 5:
            print(f"   ... 외 {len(results_dae) - 5}개")
else:
    print("❌ 검색 실패\n")

print("\n" + "="*70)
print("테스트 완료")
print("="*70 + "\n")
