"""
naver finace 크롤링을 이용한 주식 데이터 fetch
"""

import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def get_trading_firm_data(stock_code: str) -> dict:
    """
    네이버 금융에서 특정 종목의 거래원 정보를 크롤링

    Args:
        stock_code: 종목코드 (예: '000660')

    Returns:
        dict: 거래원 정보 데이터
        {
            'stock_code': '000660',
            'stock_name': 'SK하이닉스',
            'sell_firms': [{'name': '미래에셋증권', 'volume': '586,567'}, ...],
            'buy_firms': [{'name': '미래에셋증권', 'volume': '540,929'}, ...],
            'foreign_summary': {
                'sell_volume': '1,025,165',
                'net_volume': '-160,964',
                'buy_volume': '864,201'
            }
        }
    """
    url = f"https://finance.naver.com/item/frgn.naver?code={stock_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # 종목명 추출
        stock_name = ''
        h2_tag = soup.find('h2')
        if h2_tag:
            stock_name = h2_tag.get_text().strip()

        # 거래원 정보 테이블 찾기
        trading_table = None
        tables = soup.find_all('table')
        for table in tables:
            caption = table.find('caption')
            if caption and '거래원정보' in caption.get_text():
                trading_table = table
                break

        sell_firms = []
        buy_firms = []
        foreign_summary = {}
  
        if trading_table:
            tbody = trading_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')

                # 매도/매수 상위 거래원 데이터 추출 (상위 5개)
                for i, row in enumerate(rows):
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        # 매도상위 (첫 번째, 두 번째 컬럼)
                        sell_name = cells[0].get_text().strip()
                        sell_volume = cells[1].get_text().strip()

                        # 매수상위 (세 번째, 네 번째 컬럼)
                        buy_name = cells[2].get_text().strip()
                        buy_volume = cells[3].get_text().strip()

                        # 외국계추정합 행 확인
                        if '외국계추정합' in sell_name:
                            foreign_summary = {
                                'sell_volume': sell_volume,
                                'net_volume': buy_name,  # 세 번째 컬럼이 순매매
                                'buy_volume': buy_volume
                            }
                        elif sell_name and sell_volume and sell_name != '매도상위' and len(sell_firms) < 5:
                            sell_firms.append({
                                'name': sell_name,
                                'volume': sell_volume
                            })

                        if buy_name and buy_volume and buy_name != '매수상위' and '외국계추정합' not in sell_name and len(buy_firms) < 5:
                            buy_firms.append({
                                'name': buy_name,
                                'volume': buy_volume
                            })

        result = {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'sell_firms': sell_firms,
            'buy_firms': buy_firms,
            'foreign_summary': foreign_summary
        }

        logger.info(f"거래원 정보 크롤링 완료: {stock_code} ({stock_name})")
        return result

    except Exception as e:
        logger.error(f"거래원 정보 크롤링 실패: {stock_code}, {str(e)}")
        return {
            'stock_code': stock_code,
            'stock_name': '',
            'sell_firms': [],
            'buy_firms': [],
            'foreign_summary': {},
            'error': str(e)
        }


def get_financial_summary(stock_code: str) -> dict:
    """
    네이버 금융에서 특정 종목의 분기별 재무 데이터를 크롤링

    Args:
        stock_code: 종목코드 (예: '005930')

    Returns:
        dict: 분기별 재무 데이터
        {
            'stock_code': '005930',
            'stock_name': '삼성전자',
            'annual_data': [
                {
                    'period': '2024.12',
                    'revenue': 3008709,      # 매출액 (백만원)
                    'operating_income': 327260,  # 영업이익 (백만원)
                    'net_income': 344514,    # 당기순이익 (백만원)
                    'operating_margin': 10.88,   # 영업이익률 (%)
                    'net_margin': 11.45,     # 순이익률 (%)
                    'eps': 4950,             # EPS (원)
                    'per': 10.75,            # PER (배)
                    'bps': 57981,            # BPS (원)
                    'pbr': 0.92              # PBR (배)
                },
                ...
            ],
            'quarterly_data': [
                {
                    'period': '2024.09',
                    'revenue': 790987,
                    'operating_income': 91834,
                    'net_income': 101009,
                    'operating_margin': 11.61,
                    'net_margin': 12.77,
                    'eps': 1440,
                    'per': 13.03,
                    'bps': 55376,
                    'pbr': 1.11
                },
                ...
            ]
        }
    """
    url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # 종목명 추출
        stock_name = ''
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text()
            if ':' in title_text:
                stock_name = title_text.split(':')[0].strip()

        # 기업실적분석 테이블 찾기
        target_table = soup.find('table', summary=lambda x: x and '기업실적분석' in x)

        if not target_table:
            logger.error(f"기업실적분석 테이블을 찾을 수 없습니다: {stock_code}")
            return {'error': '기업실적분석 테이블을 찾을 수 없습니다'}

        rows = target_table.find_all('tr')
        if len(rows) < 13:  # 최소한의 행이 있는지 확인
            logger.error(f"테이블 데이터가 부족합니다: {stock_code}")
            return {'error': '테이블 데이터가 부족합니다'}

        # 헤더 행 파싱 (기간 정보)
        header_row = rows[1]  # 두 번째 행이 기간 정보
        header_cells = header_row.find_all(['th', 'td'])
        periods = [cell.get_text().strip() for cell in header_cells[1:]]  # 첫 번째 셀 제외

        # 연간 데이터와 분기 데이터 구분
        annual_periods = []
        quarterly_periods = []

        for i, period in enumerate(periods):
            # 연간 데이터: .12로 끝나는 것 (12월 결산)
            if period.replace('(E)', '').endswith('.12'):
                annual_periods.append((i, period))
            # 분기 데이터: .03, .06, .09로 끝나는 것
            elif any(period.replace('(E)', '').endswith(suffix) for suffix in ['.03', '.06', '.09']):
                quarterly_periods.append((i, period))
            # 기타 (예상치 등)
            else:
                if '(E)' in period:
                    quarterly_periods.append((i, period))  # 예상치는 분기로 분류

        def safe_float(value, default=0.0):
            """안전한 float 변환"""
            try:
                if not value or value == '-' or value == '':
                    return default
                # 쉼표 제거하고 숫자만 추출
                clean_value = value.replace(',', '').replace('%', '')
                return float(clean_value)
            except (ValueError, TypeError):
                return default

        def parse_financial_data(period_indices, period_names):
            """재무 데이터 파싱"""
            data = []

            for idx, period_name in zip(period_indices, period_names):
                try:
                    # 각 행에서 해당 기간의 데이터 추출
                    revenue = safe_float(rows[3].find_all(['th', 'td'])[idx + 1].get_text().strip())  # 매출액
                    operating_income = safe_float(rows[4].find_all(['th', 'td'])[idx + 1].get_text().strip())  # 영업이익
                    net_income = safe_float(rows[5].find_all(['th', 'td'])[idx + 1].get_text().strip())  # 당기순이익
                    operating_margin = safe_float(rows[6].find_all(['th', 'td'])[idx + 1].get_text().strip())  # 영업이익률
                    net_margin = safe_float(rows[7].find_all(['th', 'td'])[idx + 1].get_text().strip())  # 순이익률
                    eps = safe_float(rows[12].find_all(['th', 'td'])[idx + 1].get_text().strip())  # EPS
                    per = safe_float(rows[13].find_all(['th', 'td'])[idx + 1].get_text().strip())  # PER
                    bps = safe_float(rows[14].find_all(['th', 'td'])[idx + 1].get_text().strip())  # BPS
                    pbr = safe_float(rows[15].find_all(['th', 'td'])[idx + 1].get_text().strip())  # PBR

                    data.append({
                        'period': period_name.replace('(E)', ''),  # (E) 제거
                        'revenue': int(revenue) if revenue else 0,
                        'operating_income': int(operating_income) if operating_income else 0,
                        'net_income': int(net_income) if net_income else 0,
                        'operating_margin': round(operating_margin, 2),
                        'net_margin': round(net_margin, 2),
                        'eps': int(eps) if eps else 0,
                        'per': round(per, 2),
                        'bps': int(bps) if bps else 0,
                        'pbr': round(pbr, 2)
                    })
                except Exception as e:
                    logger.warning(f"기간 {period_name} 데이터 파싱 실패: {e}")
                    continue

            return data

        # 연간 데이터 파싱 (최근 4년)
        annual_indices = [idx for idx, _ in annual_periods[:4]]
        annual_names = [name for _, name in annual_periods[:4]]
        annual_data = parse_financial_data(annual_indices, annual_names)

        # 분기 데이터 파싱 (최근 4분기)
        quarterly_indices = [idx for idx, _ in quarterly_periods[:4]]
        quarterly_names = [name for _, name in quarterly_periods[:4]]
        quarterly_data = parse_financial_data(quarterly_indices, quarterly_names)

        result = {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'annual_data': annual_data,
            'quarterly_data': quarterly_data
        }

        logger.info(f"재무 데이터 크롤링 성공: {stock_code} ({stock_name})")
        return result

    except Exception as e:
        logger.error(f"재무 데이터 크롤링 실패: {e}")
        return {
            'error': str(e)
        }


def get_foreign_institutional_data(stock_code: str) -> dict:
    """
    네이버 금융에서 외국인ㆍ기관 순매매 거래량 데이터를 크롤링
    
    Args:
        stock_code: 종목코드 (예: '005930')
        
    Returns:
        dict: 외국인·기관 순매매 데이터
    """
    url = f"https://finance.naver.com/item/frgn.naver?code={stock_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        stock_name = soup.find('h2').get_text().strip() if soup.find('h2') else ''

        target_table = soup.find('table', summary=lambda s: s and '외국인 기관 순매매' in s)

        if not target_table:
            logger.warning(f"순매매 테이블을 찾을 수 없음: {stock_code}")
            return {'stock_code': stock_code, 'stock_name': stock_name, 'error': '순매매 테이블을 찾을 수 없음'}

        # tbody가 없는 경우도 있으므로 테이블에서 직접 tr 검색
        rows = target_table.find_all('tr')
        if len(rows) < 2: # 헤더와 데이터 행이 최소 1개씩은 있어야 함
            logger.warning(f"테이블에 데이터 행이 부족함: {stock_code}")
            return {'stock_code': stock_code, 'stock_name': stock_name, 'error': '데이터 행 부족'}

        header_row = None
        header_idx = -1
        for i, row in enumerate(rows):
            if row.find_all('th'):
                header_row = row
                header_idx = i
                break
        
        if not header_row:
            logger.warning(f"테이블에서 헤더 행을 찾을 수 없음: {stock_code}")
            return {'stock_code': stock_code, 'stock_name': stock_name, 'error': '헤더 행 없음'}

        data_row = None
        for i in range(header_idx + 1, len(rows)):
            if rows[i].find_all('td'):
                data_row = rows[i]
                break

        if not data_row:
            logger.warning(f"테이블에서 데이터 행을 찾을 수 없음: {stock_code}")
            return {'stock_code': stock_code, 'stock_name': stock_name, 'error': '데이터 행 없음'}

        headers = [th.get_text().strip() for th in header_row.find_all('th')]
        
        try:
            date_idx = headers.index('날짜')
            inst_idx = headers.index('기관')
            foreign_idx = headers.index('외국인')
            ind_idx = headers.index('개인')
        except ValueError as e:
            logger.error(f"테이블 헤더에서 컬럼을 찾을 수 없습니다: {headers}, 오류: {e}")
            return {'stock_code': stock_code, 'stock_name': stock_name, 'error': f'필수 컬럼 없음: {e}'}

        cells = data_row.find_all('td')
        if len(cells) < len(headers):
            logger.warning(f"데이터 셀 개수가 헤더와 불일치: {stock_code}")
            return {'stock_code': stock_code, 'stock_name': stock_name, 'error': '데이터 셀 불일치'}

        def parse_volume(text: str) -> int:
            try:
                return int(text.strip().replace(',', ''))
            except (ValueError, TypeError):
                return 0

        date = cells[date_idx].get_text().strip()
        institutional_net = parse_volume(cells[inst_idx].get_text())
        foreign_net = parse_volume(cells[foreign_idx].get_text())
        individual_net = parse_volume(cells[ind_idx].get_text())

        result = {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'date': date,
            'institutional_net': institutional_net,
            'foreign_net': foreign_net,
            'individual_net': individual_net
        }
        
        logger.info(f"외국인·기관 순매매 데이터 크롤링 완료: {stock_code} ({stock_name})")
        return result
        
    except Exception as e:
        logger.error(f"외국인·기관 순매매 데이터 크롤링 실패: {stock_code}, {str(e)}")
        return {
            'stock_code': stock_code,
            'stock_name': '',
            'error': str(e)
        }


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    # SK하이닉스 거래원 정보 테스트
    result = get_trading_firm_data('000660')
    print("=== 거래원 정보 ===")
    print(f"종목: {result['stock_name']} ({result['stock_code']})")

    print("\n매도상위:")
    for i, firm in enumerate(result['sell_firms'], 1):
        print(f"{i}. {firm['name']}: {firm['volume']}")

    print("\n매수상위:")
    for i, firm in enumerate(result['buy_firms'], 1):
        print(f"{i}. {firm['name']}: {firm['volume']}")

    if result['foreign_summary']:
        print(f"\n외국계추정합:")
        print(f"매도: {result['foreign_summary']['sell_volume']}")
        print(f"순매매: {result['foreign_summary']['net_volume']}")
        print(f"매수: {result['foreign_summary']['buy_volume']}")
    
    # 외국인·기관 순매매 데이터 테스트  
    print("\n" + "="*50)
    
    # 삼성전자 테스트
    fi_result = get_foreign_institutional_data('005930')
    print("=== 외국인·기관 순매매 데이터 ===")
    print(f"종목: {fi_result['stock_name']} ({fi_result['stock_code']})")
    if 'error' not in fi_result:
        print(f"날짜: {fi_result['date']}")
        print(f"기관 순매매: {fi_result['institutional_net']:,}주")
        print(f"외국인 순매매: {fi_result['foreign_net']:,}주") 
        print(f"개인 순매매: {fi_result['individual_net']:,}주")
    else:
        print(f"오류: {fi_result['error']}")
