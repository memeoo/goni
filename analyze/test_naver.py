#!/usr/bin/env python3
"""
네이버 크롤링 함수 테스트 스크립트
"""

import sys
import os
import logging

# 현재 디렉토리를 Python path에 추가
sys.path.append(os.path.dirname(__file__))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_foreign_institutional_data():
    """외국인·기관 순매매 데이터 테스트"""
    try:
        from lib.naver import get_foreign_institutional_data
        
        # SK하이닉스로 테스트
        print("="*60)
        print("외국인·기관 순매매 데이터 테스트")
        print("="*60)
        
        stock_code = '000660'  # SK하이닉스
        print(f"종목코드: {stock_code}")
        
        result = get_foreign_institutional_data(stock_code)
        
        if 'error' in result:
            print(f"❌ 오류: {result['error']}")
        else:
            print(f"✅ 성공!")
            print(f"종목명: {result['stock_name']}")
            print(f"날짜: {result['date']}")
            print(f"기관 순매매: {result['institutional_net']:,}주")
            print(f"외국인 순매매: {result['foreign_net']:,}주")
            print(f"개인 순매매: {result['individual_net']:,}주")
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_foreign_institutional_data()