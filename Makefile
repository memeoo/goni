# Goni 프로젝트 Makefile

.PHONY: help install dev build up down logs clean test

help: ## 사용 가능한 명령어 목록
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## 모든 의존성 설치
	@echo "Installing backend dependencies..."
	cd back && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd front && npm install
	@echo "Installing analyze dependencies..."
	cd analyze && pip install -r requirements.txt

dev: ## 개발 환경 실행
	docker-compose up -d postgres redis
	@echo "Database started. Run individual services:"
	@echo "  Backend:  cd back && uvicorn main:app --reload"
	@echo "  Frontend: cd front && npm run dev"
	@echo "  Analyzer: cd analyze && python main.py"

build: ## Docker 이미지 빌드
	docker-compose build

up: ## 전체 서비스 시작
	docker-compose up -d

down: ## 전체 서비스 중지
	docker-compose down

logs: ## 로그 확인
	docker-compose logs -f

clean: ## 컨테이너 및 볼륨 정리
	docker-compose down -v
	docker system prune -f

test-backend: ## 백엔드 테스트
	cd back && python -m pytest

test-frontend: ## 프론트엔드 테스트
	cd front && npm test

test: test-backend test-frontend ## 전체 테스트 실행

db-init: ## 데이터베이스 초기화
	docker-compose exec postgres psql -U goniadmin -d goni -f /docker-entrypoint-initdb.d/init.sql

db-backup: ## 데이터베이스 백업
	docker-compose exec postgres pg_dump -U goniadmin goni > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore: ## 데이터베이스 복원 (usage: make db-restore FILE=backup.sql)
	docker-compose exec -T postgres psql -U goniadmin goni < $(FILE)

migrate: ## 데이터베이스 마이그레이션
	cd back && alembic upgrade head

format: ## 코드 포맷팅
	cd back && black . && isort .
	cd front && npm run lint:fix
	cd analyze && black . && isort .

start-dev-backend: ## 백엔드만 개발 모드로 시작
	cd back && uvicorn main:app --reload --host 0.0.0.0 --port 8000

start-dev-frontend: ## 프론트엔드만 개발 모드로 시작
	cd front && npm run dev

start-dev-analyzer: ## 분석 서비스만 개발 모드로 시작
	cd analyze && python main.py

setup-env: ## 환경 변수 파일 설정
	cp back/.env.example back/.env
	cp front/.env.example front/.env
	cp analyze/.env.example analyze/.env
	@echo "Environment files created. Please edit them with your settings."

# Docker Compose 단축 명령어
ps: ## 실행 중인 컨테이너 상태 확인
	docker-compose ps

restart: ## 서비스 재시작
	docker-compose restart

pull: ## 최신 이미지 받기
	docker-compose pull