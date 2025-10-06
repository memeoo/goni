#!/bin/bash

echo "🚀 프론트엔드 서버 시작 스크립트"
echo "================================"

# 프론트엔드 디렉토리로 이동
cd /Users/meme/proj/goni/front

# 의존성 설치 (처음 실행시만 필요)
if [ ! -d "node_modules" ]; then
    echo "📦 의존성 설치 중..."
    npm install
fi

# 개발 서버 실행
echo "🌐 Next.js 개발 서버 실행 중..."
echo "서버 주소: http://localhost:3000"
echo ""
echo "서버를 중지하려면 Ctrl+C를 누르세요."
echo "================================"

npm run dev