# Goni - 주식 매매 계획 및 복기 일지

타짜급 트레이더로 성장하기 위한 매매 계획 수립과 복기 시스템

## 프로젝트 구조

```
goni/
├── back/           # FastAPI 백엔드
├── front/          # Next.js 15 프론트엔드  
├── analyze/        # Python 3.13 분석 서비스
├── docker-compose.yml
├── init.sql
└── README.md
```

## 기술 스택

- **백엔드**: FastAPI (latest)
- **프론트엔드**: Next.js 15+
- **분석**: Python 3.13
- **데이터베이스**: PostgreSQL
- **컨테이너**: Docker & Docker Compose

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

### 2. Docker로 실행

```bash
# 전체 서비스 시작
docker-compose up -d

# 개별 서비스 시작
docker-compose up postgres pgadmin  # 데이터베이스만
docker-compose up backend           # 백엔드만
docker-compose up frontend          # 프론트엔드만
docker-compose up analyzer          # 분석 서비스만
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
- **pgAdmin**: http://localhost:5050
  - Email: admin@goni.com
  - Password: admin123

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
- `stock_analysis`: 기술적 분석 결과
- `price_alerts`: 가격 알림
- `news_sentiment`: 뉴스 감정 분석

## API 엔드포인트

### 인증
- `POST /api/auth/token`: 로그인
- `POST /api/auth/register`: 회원가입
- `GET /api/auth/me`: 내 정보

### 주식
- `GET /api/stocks`: 주식 목록
- `GET /api/stocks/{id}`: 주식 상세
- `POST /api/stocks`: 주식 추가

### 매매 계획
- `GET /api/trading-plans`: 매매 계획 목록
- `POST /api/trading-plans`: 매매 계획 생성
- `PUT /api/trading-plans/{id}`: 매매 계획 수정
- `DELETE /api/trading-plans/{id}`: 매매 계획 삭제

## 개발 가이드

### 코드 구조

#### 백엔드 (FastAPI)
- `main.py`: 앱 진입점
- `app/models.py`: 데이터베이스 모델
- `app/schemas.py`: Pydantic 스키마
- `app/routers/`: API 라우터
- `app/database.py`: 데이터베이스 연결

#### 프론트엔드 (Next.js)
- `src/app/`: App Router 기반 페이지
- `src/components/`: 재사용 컴포넌트
- `src/lib/`: 유틸리티 및 API 클라이언트
- `src/types/`: TypeScript 타입 정의

#### 분석 서비스 (Python)
- `main.py`: 분석 서비스 진입점
- `src/data_collector.py`: 데이터 수집
- `src/technical_analyzer.py`: 기술적 분석
- `src/news_analyzer.py`: 뉴스 분석
- `src/database.py`: 데이터베이스 연동

### 배포

```bash
# 프로덕션 빌드
docker-compose -f docker-compose.prod.yml up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down
```

## 라이선스

MIT License