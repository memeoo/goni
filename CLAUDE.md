# Structure
- back-end 소스 폴더 : root/back
- front-end 소스 폴더 : root/front
- 종목 분석 및 추천 서비스 소스 폴더: root/analyze

# Tech Stack
- back-end : fast api(latest)
- front-end : next.js v.15 이상
- analyze: python v.3.13
- DB : postgresql (db name:goni, port:5432, user:goniadmin, password:shsbsy70)
- 프로세스 관리: pm2. name: goni-backend(backend), goni-frontend(frontend)

# Port Configuration
- **포트 3000 (운영/Production)**: PM2 `goni-frontend` 프로세스가 실행하는 포트. `npm start -- -p 3000` 명령으로 빌드된 Next.js를 실행
- **포트 3001 (개발/Development)**: `npm run dev` 명령으로 개발 서버 시작. 로컬 개발 및 테스트 용도

# Project description
- 이름:  Goni(영화 타짜의 주인공 ‘고니’ 처럼 타짜 급의 탑 트레이더가 되기 위한 매매 계획 및 복기 일지 프로그램)
- 개요: 여러 주식 종목의 당일 정보(차트 및 수급, 뉴스 등)를 모니터링 할 수 있는 대쉬 보드 형태의 웹 페이지. 모니터링 목적 이외에, 종목을 매매 하는 플랜을 세우고, 매매 이유와 복기(결과 및 반성)를 입력해서 매매 계획과 복기 등의 일지를 작성해 트레이딩의 실력을 높히는게 주 목적. 

# Not To do.
- 절대 Mock 데이터를 만들어서 표시하지 말 것. 데이터가 없거나 가져올 수 없으면 그냥 없다고 표시할 것. Dummy 데이터나 Mock 데이터를 절대로 만들어서 표시하지 말 것. 

# README.md Update.
- 새로운 기능이 추가되거나 변경이 일어나면 항상 README.md 파일의 ## ADDED or MODIFIED 아래에 내용을 적어서 계속 업데이트 상태를 유지하시오.
- 프로젝트를 처음 시작할 때, 항상 README.md 파일을 먼저 읽어서 project의 진행 상황을 파악하시오.