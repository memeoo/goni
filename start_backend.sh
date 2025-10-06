#!/bin/bash

echo "🚀 백엔드 서버 시작 스크립트"
echo "==============================="

# 백엔드 디렉토리로 이동
cd /Users/meme/proj/goni/back

# 가상환경 활성화
echo "📦 가상환경 활성화 중..."
source venv/bin/activate

# 필요한 패키지 설치
echo "📋 의존성 설치 중..."
pip install requests beautifulsoup4 lxml

# 서버 실행
echo "🌐 FastAPI 서버 실행 중..."
echo "서버 주소: http://localhost:8000"
echo "API 문서: http://localhost:8000/docs"
echo ""
echo "서버를 중지하려면 Ctrl+C를 누르세요."
echo "==============================="

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000