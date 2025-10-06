FROM node:18-alpine

WORKDIR /app

# package.json과 package-lock.json 복사
COPY package*.json ./

# 의존성 설치
RUN npm ci --only=production

# 앱 코드 복사
COPY . .

# Next.js 빌드 (프로덕션용)
# RUN npm run build

# 포트 노출
EXPOSE 3000

# 개발 서버 실행 (개발용)
CMD ["npm", "run", "dev"]

# 프로덕션 서버 실행 (프로덕션용)
# CMD ["npm", "start"]