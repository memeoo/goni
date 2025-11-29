#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ubuntu/goni')
from analyze.lib.kiwoom import KiwoomAPI
import os
from dotenv import load_dotenv

load_dotenv('back/.env')

api = KiwoomAPI(
    app_key=os.getenv('KIWOOM_APP_KEY'),
    secret_key=os.getenv('KIWOOM_SECRET_KEY'),
    account_no=os.getenv('KIWOOM_ACCOUNT_NO'),
    use_mock=False
)

conditions = api.get_condition_list()
if conditions:
    print("\n=== 사용 가능한 조건식 목록 ===\n")
    for i, cond in enumerate(conditions, 1):
        print(f"{i}. 이름: {cond['name']:<30} | ID: {cond['id']}")
else:
    print("조건식 목록을 가져올 수 없습니다")
