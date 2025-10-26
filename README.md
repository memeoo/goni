# Goni - 주식 매매 계획 및 복기 일지

타짜급 트레이더로 성장하기 위한 매매 계획 수립과 복기 시스템

## 프로젝트 구조

```
goni/
├── back/           # FastAPI 백엔드
├── front/          # Next.js 15 프론트엔드  
├── analyze/        # Python 3.13 분석 서비스
├── init.sql
└── README.md
```

## 기술 스택

- **백엔드**: FastAPI (latest)
- **프론트엔드**: Next.js 15+
- **분석**: Python 3.13
- **데이터베이스**: PostgreSQL

## 주요 기능

### 1. 실시간 모니터링
- 관심 종목 차트, 수급, 뉴스 모니터링
- 실시간 가격 알림
- 시장 지수 추적

### 2. 매매 계획
- 체계적인 진입/청산 계획 수립
- 리스크 관리 도구
- 목표가 및 손절가 설정

### 3. 매매 복기
- 실행 결과 기록
- 수익/손실 분석
- 개선점 도출

### 4. 기술적 분석
- RSI, MACD, 볼린저 밴드
- 이동평균선 분석
- 지지/저항선 계산

### 5. 뉴스 감정 분석
- 종목별 뉴스 수집
- 감정 점수 계산
- 시장 분위기 분석

## 시작하기

### 1. 환경 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd goni

# 환경 변수 설정
cp back/.env.example back/.env
cp front/.env.example front/.env
cp analyze/.env.example analyze/.env
```

### 3. 개발 환경에서 실행

#### 백엔드 (FastAPI)
```bash
cd back
pip install -r requirements.txt
uvicorn main:app --reload
```

#### 프론트엔드 (Next.js)
```bash
cd front
npm install
npm run dev
```

#### 분석 서비스 (Python)
```bash
cd analyze
pip install -r requirements.txt
python main.py
```

## 서비스 접속

- **웹 애플리케이션**: http://localhost:3000
- **API 문서**: http://localhost:8000/docs

## 데이터베이스

### 접속 정보
- Host: localhost
- Port: 5432
- Database: goni
- User: goniadmin
- Password: shsbsy70

### 주요 테이블
- `users`: 사용자 정보
- `stocks`: 주식 종목 정보
- `trading_plans`: 매매 계획 및 복기

## ADDED or MODIFIED

### 2025-10-25: 복기 모달에 일봉 차트 시각화 추가

#### 1. DailyChart 컴포넌트 개발 (front/src/components/daily-chart.tsx)
- **파일**: `front/src/components/daily-chart.tsx` (신규)
- **기능**:
  - Canvas API를 사용한 고성능 차트 렌더링
  - 최근 50일 일봉 캔들스틱 차트 표시
    - 양봉: 빨간색 (#ff4444), 음봉: 파란색 (#4444ff)
    - 심지(High-Low)와 몸통(Open-Close) 렌더링
  - 거래량 바 차트 (일봉 차트 아래)
    - 양봉 색상은 빨강, 음봉 색상은 파랑
  - 가격 축 (오른쪽):
    - 최저가에서 10% 낮은 값부터 최고가에서 10% 높은 값까지
    - 5등분하여 표시 (최소값, 최대값 포함)
  - 거래량 축 (오른쪽):
    - 0부터 최대 거래량까지 5등분
    - 1000단위는 'K', 백만 단위는 'M'으로 표시
  - X축 (날짜):
    - 5일 단위로 표시 (월/일 형식, 년도 제외)
  - 높이 비율: 가격 차트 330px : 거래량 차트 100px (약 3.3:1)

#### 2. RecapModal 컴포넌트 개선 (front/src/components/recap-modal.tsx)
- **파일**: `front/src/components/recap-modal.tsx`
- **변경 사항**:
  - DailyChart 컴포넌트 임포트 및 통합
  - stockCode prop 추가
  - 일봉 차트 데이터 조회 useQuery 추가:
    - 엔드포인트: `/api/stocks/{stock_code}/daily-chart`
    - 주식 선택 시 자동으로 50일간의 일봉 데이터 로딩
  - 모달 내 차트 배치:
    - 모달 상단에 일봉 차트 표시
    - 입력 필드는 차트 아래에 배치
  - 차트 로딩 상태 표시

#### 3. Dashboard 페이지 수정 (front/src/app/dashboard/page.tsx)
- **파일**: `front/src/app/dashboard/page.tsx`
- **변경 사항**:
  - selectedStockCode 상태 추가
  - handleStockCardClick에서 stockCode 저장
  - RecapModal에 stockCode prop 전달

#### 4. API 스키마 추가 (back/app/schemas.py)
- **파일**: `back/app/schemas.py`
- **추가 스키마**:
  - ChartDataPoint: 일봉 차트 데이터 포인트
  - DailyChartResponse: 일봉 차트 조회 응답

### 2025-10-25: 키움증권 API ka10081을 이용한 일봉 차트 조회 기능 추가

#### 1. KiwoomAPI 클래스 확장 (analyze/lib/kiwoom.py)
- **파일**: `analyze/lib/kiwoom.py`
- **추가된 메서드**: `get_daily_chart()`
  - 키움증권 Open REST API ka10081 TR 사용
  - 주식 일봉 차트 데이터 조회 (OHLC, 거래량, 거래대금)
  - 파라미터:
    - `stock_code` (str): 종목코드 (6자리, 예: '005930')
    - `base_dt` (str): 기준일자 YYYYMMDD (공백: 금일데이터)
    - `upd_stkpc_tp` (str): 수정주가구분 ('0': 미수정, '1': 수정, 기본값: '1')
  - 반환 데이터: 일봉 차트 데이터 리스트

#### 2. 백엔드 API 엔드포인트 추가 (back/app/routers/stocks.py)
- **파일**: `back/app/routers/stocks.py`
- **새로운 엔드포인트**: `GET /api/stocks/{stock_code}/daily-chart`
  - 쿼리 파라미터:
    - `stock_code`: 종목코드 (필수)
    - `base_dt`: 기준일자 (선택, 기본값: 금일)
    - `upd_stkpc_tp`: 수정주가구분 (선택, 기본값: '1')
  - 응답 포맷:
    ```json
    {
      "stock_code": "005930",
      "data": [
        {
          "date": "2025-09-08",
          "open": 69800,
          "high": 70500,
          "low": 69600,
          "close": 70100,
          "volume": 9263135,
          "trade_amount": 648525
        },
        ...
      ],
      "total_records": 100
    }
    ```
  - 기능:
    - 환경변수에서 키움증권 API 자격증명 자동 로드
    - 키움증권 API 호출 및 에러 처리
    - 응답 데이터 포맷 변환 (YYYYMMDD -> YYYY-MM-DD, 문자열 -> 숫자)
    - 상세 로깅 및 디버깅 정보 제공

#### 3. 환경변수 설정 필요
- `KIWOOM_APP_KEY`: 키움증권 앱 키
- `KIWOOM_SECRET_KEY`: 키움증권 시크릿 키
- `KIWOOM_ACCOUNT_NO`: 키움증권 계좌번호
- `KIWOOM_USE_MOCK`: 모의투자 여부 (True/False, 기본값: False)

### 2025-10-25: 복기 모달 UI 레이아웃 개선

#### 복기 상세 팝업 (recap-modal.tsx)
- **파일**: `front/src/components/recap-modal.tsx`
- **변경 사항**:
  - 모달 폭을 전체 화면의 80%로 확장 (`w-[80%]`)
  - 마진 및 불필요한 제약 제거로 최적 레이아웃 구현
  - 입력 필드를 2열 그리드로 재배치하여 한 행에 2개씩 배치:
    - Row 1: 재료 & 시황
    - Row 2: 가격(차트) & 거래량
    - Row 3: 수급(외국인/기관) & 심리(매매 당시의 감정)
    - Row 4: 평가 (라디오 버튼, 전체 폭)
    - Row 5: 평가이유 & 기타(자유 기술)
  - 더 나은 공간 활용과 시각적 일관성 제공

### 2025-10-22: 프로젝트 초기 구축 완료

#### 1. 백엔드 (FastAPI) - 완전 구현

##### 인증 시스템 (`/api/auth`)
- **파일**: `back/app/routers/auth.py`
- **기능**:
  - `POST /api/auth/token`: OAuth2 폼 기반 로그인
  - `POST /api/auth/login`: JSON 기반 로그인
  - `POST /api/auth/register`: 회원가입 (이메일/사용자명 중복 검사)
  - `GET /api/auth/me`: 현재 사용자 프로필 조회
  - `PUT /api/auth/update-kiwoom`: 키움증권 API 인증정보 업데이트
- **보안**: JWT 토큰 (HS256 알고리즘), bcrypt 비밀번호 해싱, 8시간 토큰 만료

##### 주식 데이터 API (`/api/stocks`)
- **파일**: `back/app/routers/stocks.py`
- **데이터 소스**: KIS API (한국투자증권), Naver Finance (웹 스크래핑)
- **엔드포인트**:
  - `GET /api/stocks/`: 주요 종목 목록 및 실시간 가격 조회
  - `GET /api/stocks/{stock_code}/chart-data`: OHLC + 거래량 + 이동평균선 (60일)
  - `GET /api/stocks/{stock_code}/ohlc`: OHLC 데이터
  - `GET /api/stocks/{stock_code}/volume`: 거래량 데이터 (전일 대비 변화율 포함)
  - `GET /api/stocks/{stock_code}/current-price`: 현재가 및 변동률
  - `GET /api/stocks/{stock_code}/foreign-institutional`: 외국인/기관 수급 정보
- **통합 모듈**: `analyze/lib/hantu.py` (KIS API), `analyze/lib/naver.py` (네이버 증권)

##### 매매 내역 API (`/api/trading-plans`)
- **파일**: `back/app/routers/trading_plans.py`
- **구현 완료**:
  - `GET /api/trading-plans/trades/recent`: 키움증권 API를 통한 최근 실제 매매 내역 조회 (10일)
    - Mock/실제 거래 지원
    - 사용자별 키움 API 인증정보 사용
    - 반환 데이터: 종목코드, 종목명, 매수/매도, 체결가, 수량, 체결시각, 주문번호, 복기 작성 여부
- **통합 모듈**: `analyze/lib/kiwoom.py`
- **미구현**: CRUD 엔드포인트는 스텁 상태

##### 복기(Recap) API (`/api/recap`)
- **파일**: `back/app/routers/recap.py`
- **완전 구현**:
  - `POST /api/recap/`: 복기 생성 (trading_plan_id 또는 order_no 지원)
  - `GET /api/recap/{trading_plan_id}`: 매매 계획 ID로 복기 조회
  - `GET /api/recap/by-order/{order_no}`: 주문번호로 복기 조회
  - `GET /api/recap/`: 사용자의 전체 복기 목록 (페이징 지원)
  - `PUT /api/recap/{trading_plan_id}`: 복기 수정
  - `PUT /api/recap/by-order/{order_no}`: 주문번호 기반 복기 수정
  - `DELETE /api/recap/{trading_plan_id}`: 복기 삭제

##### 데이터베이스 모델
- **파일**: `back/app/models.py`
- **테이블**:
  - `users`: 사용자 정보 (JWT 인증, 키움 API 인증정보 저장)
  - `stocks`: 종목 정보 (종목코드, 종목명, 시장구분, 가격정보)
  - `trading_plans`: 매매 계획 및 실행 기록
  - `recap`: 상세 매매 복기 데이터 (재료, 시황, 차트, 거래량, 수급, 심리, 평가 등)

#### 2. 프론트엔드 (Next.js 15) - 핵심 기능 구현

##### 페이지
- **파일 위치**: `front/src/app/`
- **구현 완료**:
  - `/page.tsx`: 홈 (로그인 상태에 따라 /dashboard 또는 /login으로 리다이렉트)
  - `/login/page.tsx`: 로그인 (Zod 유효성 검사, 비밀번호 표시/숨김 토글)
  - `/register/page.tsx`: 회원가입 (이메일/사용자명/비밀번호 검증, 비밀번호 확인)
  - `/dashboard/page.tsx`: 메인 대시보드
    - **계획 모드**: 관심 종목 모니터링 (미구현)
    - **복기 모드**: 최근 매매 내역 표시 및 복기 작성 (구현 완료)
    - 4열 그리드 레이아웃 (반응형)
    - React Query 기반 데이터 페칭 (자동 갱신: 복기 모드 5분)
    - 로딩/에러 상태 처리
  - `/profile/page.tsx`: 사용자 프로필 및 설정
    - 이메일/사용자명 표시 (읽기 전용)
    - 키움증권 API 인증정보 입력 및 저장
    - 비밀번호 가시성 토글

##### 컴포넌트
- **파일 위치**: `front/src/components/`
- **구현 완료**:
  - `header.tsx`: 헤더 (앱 타이틀, 계획/복기 모드 토글, 날짜, 프로필, 로그아웃 버튼)
  - `trade-card.tsx`: 매매 내역 카드
    - 종목명, 종목코드, 매수/매도 표시 (색상 구분)
    - 체결가, 수량, 거래금액, 체결시각
    - 복기 완료 여부 표시 (초록색 테두리 + 체크마크)
  - `recap-modal.tsx`: 복기 작성/수정 모달
    - 9개 입력 필드: 재료, 시황, 가격(차트), 거래량, 수급, 심리, 평가, 평가이유, 기타
    - 평가: 라디오 버튼 (Good/So-So/Bad)
    - 생성/수정 기능
    - React Query 뮤테이션 + 캐시 무효화
  - `stock-candlestick-chart.tsx`: 캔들스틱 차트 (Recharts, 부분 구현)
  - UI 컴포넌트 (`ui/`): button, input, card, badge (Shadcn UI 스타일)

##### API 통합
- **파일**: `front/src/lib/api.ts`
- **기능**:
  - Axios 인스턴스 (baseURL, 타임아웃 10초)
  - 요청 인터셉터: JWT 토큰 자동 주입 (쿠키 우선, localStorage 대체)
  - 응답 인터셉터: 401 에러 시 자동 로그인 페이지 리다이렉트 및 토큰 삭제
  - API 함수:
    - `authAPI`: login, register, getMe
    - `stocksAPI`: getStocks, getChartData, getOHLCData, getVolumeData, getCurrentPrice, getForeignInstitutionalData
    - `tradingPlansAPI`: 기본 CRUD + **getRecentTrades** (완전 구현)

##### 커스텀 훅
- **파일**: `front/src/lib/hooks/use-auth.ts`
- **훅**:
  - `useAuth()`: 현재 사용자 정보 조회 (React Query)
  - `useLogin()`: 로그인 뮤테이션 (성공 시 /dashboard 리다이렉트)
  - `useRegister()`: 회원가입 뮤테이션
  - `useLogout()`: 로그아웃 뮤테이션 (토큰 삭제 + 캐시 초기화)

##### 미들웨어
- **파일**: `front/src/middleware.ts`
- **기능**:
  - 보호된 경로 (`/dashboard`, `/profile`): 토큰 없으면 `/login`으로 리다이렉트
  - 공개 경로 (`/login`, `/register`): 토큰 있으면 `/dashboard`로 리다이렉트

##### Next.js API 라우트
- **파일**: `front/src/app/api/trading-plans/trades/recent/route.ts`
- **기능**: 서버사이드에서 쿠키의 토큰을 읽어 백엔드 API에 전달 (프록시 역할)

#### 3. 분석 서비스 (Python) - 데이터 제공 모듈

##### KIS API 래퍼
- **파일**: `analyze/lib/hantu.py`
- **클래스**: `KISApi`
- **함수**:
  - `get_combined_data(stock_code, days)`: OHLC + 거래량 + 이동평균선
  - `get_ohlc_data(stock_code, days)`: OHLC 데이터만
  - `get_volume_data(stock_code, days)`: 거래량 + 전일대비 변화율
  - `get_current_price_data(stock_code)`: 현재가 + 등락률
- **기능**: 토큰 캐싱 및 자동 갱신, 에러 처리, Pandas DataFrame 반환

##### 네이버 증권 스크래퍼
- **파일**: `analyze/lib/naver.py`
- **함수**: `get_foreign_institutional_data(stock_code)`
- **반환**: 외국인/기관/개인 순매수, 상위 5개 매수/매도 증권사
- **기술**: BeautifulSoup HTML 파싱, User-Agent 스푸핑

##### 키움증권 API 래퍼
- **파일**: `analyze/lib/kiwoom.py`
- **클래스**: `KiwoomAPI`
- **주요 메서드**: `get_recent_trades(days)` - 최근 N일간 실제 매매내역 조회
- **기능**: OAuth2 토큰 관리, Mock/실거래 지원, 토큰 캐싱

##### 기술적 분석 프레임워크
- **파일**: `analyze/src/technical_analyzer.py`
- **지표**: RSI, MACD, 볼린저밴드, 이동평균선, 지지/저항선
- **상태**: 프레임워크 구현, UI 통합 미완

##### 뉴스 감정 분석
- **파일**: `analyze/src/news_analyzer.py`
- **기능**: 네이버/다음 뉴스 수집, 긍정/부정 키워드 기반 감정 점수 계산
- **상태**: 프레임워크 구현, UI 통합 미완

#### 4. 인프라 및 설정

##### 프로세스 관리
- **도구**: PM2
- **프로세스**:
  - `goni-backend`: FastAPI 백엔드 (포트 8000)
  - `goni-frontend`: Next.js 프론트엔드 (포트 3000)

##### CORS 설정
- **허용 오리진**: localhost:3000-3003, AWS 서버 (3.34.102.218)

##### 환경 변수
- 백엔드: `SECRET_KEY`, DB 연결정보, KIS API 인증정보
- 프론트엔드: `NEXT_PUBLIC_API_URL`
- 분석 서비스: 키움 계좌번호, Mock 모드 설정

#### 5. 최근 버그 수정 (2025-10-22)

##### 토큰 만료 문제 해결
- **문제**: JWT 토큰 30분 만료로 인한 잦은 401 에러
- **해결**: 토큰 만료 시간을 8시간(480분)으로 연장 (`back/app/routers/auth.py:19`)
- **영향**: 사용자 경험 개선, 재로그인 빈도 감소

##### 자동 로그인 리다이렉트 구현
- **문제**: 토큰 만료 시 수동으로 로그인 페이지 이동 필요
- **해결**:
  - `dashboard/page.tsx`에서 직접 fetch 대신 axios API 함수 사용 (`tradingPlansAPI.getRecentTrades`)
  - axios 인터셉터가 401 에러 감지 시 자동으로 토큰 삭제 및 `/login`으로 리다이렉트
- **파일 수정**:
  - `front/src/lib/api.ts`: `tradingPlansAPI.getRecentTrades` 함수 추가
  - `front/src/app/dashboard/page.tsx`: `fetchRecentTrades` 함수를 axios 사용하도록 변경

#### 6. 미구현 기능

- 계획 모드 UI 및 매매 계획 CRUD
- 종목 추가/관리 UI
- 전략 관리 UI
- 캔들스틱 차트에 이동평균선 렌더링
- 기술적 분석 UI 통합
- 뉴스 감정 분석 UI 통합

#### 7. 다음 단계

1. 매매 계획 작성 기능 구현 (계획 모드 활성화)
2. 차트 컴포넌트 완성 (이동평균선 표시)
3. 기술적 분석 지표를 차트에 통합
4. 뉴스 감정 분석 결과를 대시보드에 표시
5. 종목 추가/삭제 기능 구현
6. 전략 관리 기능 구현