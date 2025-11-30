from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.database import database
from app.routers import auth, stocks, trading_plans, recap, trading, trading_stocks, stocks_info, rec_stocks, algorithm, principles
from app.scheduler import start_scheduler, stop_scheduler, get_scheduler_jobs, scheduler, sync_stocks_info_job

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.connect()
    # 스케줄러 시작
    start_scheduler()
    logger.info("애플리케이션 시작: 스케줄러 활성화")
    yield
    # Shutdown
    # 스케줄러 종료
    stop_scheduler()
    await database.disconnect()
    logger.info("애플리케이션 종료: 스케줄러 비활성화")


app = FastAPI(
    title="Goni Trading API",
    description="주식 매매 계획 및 복기 일지 서비스",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://3.34.102.218:3000",
        "http://3.34.102.218:3001"
    ],  # Next.js 개발 서버 (여러 포트 허용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(stocks_info.router, tags=["stocks-info"])  # /api/stocks-info 포함
app.include_router(trading_plans.router, prefix="/api/trading-plans", tags=["trading-plans"])
app.include_router(trading.router, tags=["trading"])
app.include_router(trading_stocks.router, tags=["trading-stocks"])  # trading_stocks.router 이미 /api/trading-stocks 포함
app.include_router(rec_stocks.router, tags=["rec-stocks"])  # /api/rec-stocks 포함
app.include_router(algorithm.router, tags=["algorithm"])  # /api/algorithms 포함
app.include_router(recap.router)
app.include_router(principles.router, prefix="/api/principles", tags=["principles"])


@app.get("/")
async def root():
    return {"message": "Goni Trading API Server"}


@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """
    스케줄러 상태 및 등록된 작업 조회

    Returns:
        dict: 스케줄러 상태
        {
            "running": true,
            "jobs": [
                {
                    "id": "sync_stocks_info",
                    "name": "종목정보 자동 동기화",
                    "trigger": "cron[hour='7', minute='30', day_of_week='0-4']",
                    "next_run_time": "2025-11-10T07:30:00+09:00"
                }
            ]
        }
    """
    return {
        "running": scheduler.running,
        "jobs": get_scheduler_jobs(),
    }


@app.post("/api/scheduler/manual-sync")
async def manual_sync_stocks_info():
    """
    종목정보 수동 동기화 (테스트용)

    Returns:
        dict: 동기화 작업 상태
        {
            "status": "success",
            "message": "종목정보 동기화 작업이 시작되었습니다"
        }
    """
    import threading

    # 백그라운드 스레드에서 작업 실행
    thread = threading.Thread(target=sync_stocks_info_job, daemon=True)
    thread.start()

    return {
        "status": "success",
        "message": "종목정보 동기화 작업이 시작되었습니다. 로그를 확인해주세요.",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)