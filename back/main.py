from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.database import database
from app.routers import auth, stocks, trading_plans, recap, trading, trading_stocks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.connect()
    yield
    # Shutdown
    await database.disconnect()


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
app.include_router(trading_plans.router, prefix="/api/trading-plans", tags=["trading-plans"])
app.include_router(trading.router, tags=["trading"])
app.include_router(trading_stocks.router, tags=["trading-stocks"])
app.include_router(recap.router)


@app.get("/")
async def root():
    return {"message": "Goni Trading API Server"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)