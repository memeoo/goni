# 25.09.22 개발 사항 
- 내가 만들어 놓은 hantu.py 파일에, 한국투자증권(KIS) Open API를 활용한 wrapper functions 들을 만들어줘. 
- API 접속 정보는 analyze/.env 파일에 한국투자증권 Open API 설정 부분을 참고해.
- 내가 필요한 함수들은 해당 종목의 
 1. 오늘 부터 n일전 까지의 OHLC(시가, 고가, 저가, 종가) 데이터를 가져오는 함수와,
 2. 마찬가지로 오늘 부터 n일전 까지의 거래량 데이터를 가져오는 함수
 이 두개가 필요해.

# 25.10.04 개발 사항
- 키움증권 open api 접속시 필요한 정보:  
secret_key: KUwnffZOR2dP4nwEZCIgTAhu-FquHEa2Xx9mCKE9ak0
app_key: KY7QbSwIVVmjqBM5jIZHbcGOle2O8nQL7dFUNtVmTKU
domain: https://api.kiwoom.com
API Guide 페이지: https://openapi.kiwoom.com/guide/apiguide?dummyVal=0
